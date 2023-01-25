"""Provide common functionalities used across the tests."""
import io
import pathlib
from typing import Tuple, MutableMapping, List, Final, Set, Union

import aas_core_codegen.common
import aas_core_codegen.parse
import aas_core_codegen.run
import asttokens
from aas_core_codegen import intermediate, infer_for_schema


class MetaModel:
    #: Tokens of the original meta-model
    atok: Final[asttokens.ASTTokens]

    #: Symbol table parsed from a meta-model
    symbol_table: Final[intermediate.SymbolTable]

    #: Inferred constraints grouped by class
    constraints_by_class: Final[
        MutableMapping[intermediate.ClassUnion, infer_for_schema.ConstraintsByProperty]
    ]

    def __init__(
        self,
        atok: asttokens.ASTTokens,
        symbol_table: intermediate.SymbolTable,
        constraints_by_class: MutableMapping[
            intermediate.ClassUnion, infer_for_schema.ConstraintsByProperty
        ],
    ) -> None:
        """Initialize with the given values."""
        self.atok = atok
        self.symbol_table = symbol_table
        self.constraints_by_class = constraints_by_class


def load_meta_model(
    model_path: pathlib.Path,
) -> MetaModel:
    """
    Load the symbol table from the meta-model and infer the schema constraints.

    These constraints might not be sufficient to generate *some* of the instances.
    Further constraints in form of invariants might apply which are not represented
    in the schema constraints. However, this will help us cover *many* classes of the
    meta-model and spare us the work of manually writing many generators.
    """
    assert model_path.exists() and model_path.is_file(), model_path

    text = model_path.read_text(encoding="utf-8")

    atok, parse_exception = aas_core_codegen.parse.source_to_atok(source=text)
    if parse_exception:
        if isinstance(parse_exception, SyntaxError):
            raise RuntimeError(
                f"Failed to parse the meta-model {model_path}: "
                f"invalid syntax at line {parse_exception.lineno}\n"
            )
        else:
            raise RuntimeError(
                f"Failed to parse the meta-model {model_path}: " f"{parse_exception}\n"
            )

    assert atok is not None

    import_errors = aas_core_codegen.parse.check_expected_imports(atok=atok)
    if import_errors:
        writer = io.StringIO()
        aas_core_codegen.run.write_error_report(
            message="One or more unexpected imports in the meta-model",
            errors=import_errors,
            stderr=writer,
        )

        raise RuntimeError(writer.getvalue())

    lineno_columner = aas_core_codegen.common.LinenoColumner(atok=atok)

    parsed_symbol_table, error = aas_core_codegen.parse.atok_to_symbol_table(atok=atok)
    if error is not None:
        writer = io.StringIO()
        aas_core_codegen.run.write_error_report(
            message=f"Failed to construct the symbol table from {model_path}",
            errors=[lineno_columner.error_message(error)],
            stderr=writer,
        )

        raise RuntimeError(writer.getvalue())

    assert parsed_symbol_table is not None

    ir_symbol_table, error = intermediate.translate(
        parsed_symbol_table=parsed_symbol_table,
        atok=atok,
    )
    if error is not None:
        writer = io.StringIO()
        aas_core_codegen.run.write_error_report(
            message=f"Failed to translate the parsed symbol table "
            f"to intermediate symbol table "
            f"based on {model_path}",
            errors=[lineno_columner.error_message(error)],
            stderr=writer,
        )

        raise RuntimeError(writer.getvalue())

    assert ir_symbol_table is not None

    (
        constraints_by_class,
        inference_errors,
    ) = aas_core_codegen.infer_for_schema.infer_constraints_by_class(
        symbol_table=ir_symbol_table
    )

    if inference_errors is not None:
        writer = io.StringIO()
        aas_core_codegen.run.write_error_report(
            message=f"Failed to infer the constraints for the schema "
            f"based on {model_path}",
            errors=[lineno_columner.error_message(error) for error in inference_errors],
            stderr=writer,
        )

        raise RuntimeError(writer.getvalue())

    assert constraints_by_class is not None
    (
        constraints_by_class,
        merge_error,
    ) = aas_core_codegen.infer_for_schema.merge_constraints_with_ancestors(
        symbol_table=ir_symbol_table, constraints_by_class=constraints_by_class
    )

    if merge_error is not None:
        writer = io.StringIO()
        aas_core_codegen.run.write_error_report(
            message=f"Failed to infer the constraints for the schema "
            f"based on {model_path}",
            errors=[lineno_columner.error_message(merge_error)],
            stderr=writer,
        )

        raise RuntimeError(writer.getvalue())

    assert constraints_by_class is not None

    return MetaModel(atok, ir_symbol_table, constraints_by_class)


def human_readable_property_name(name: str) -> str:
    """
    Convert the property name from the specs to a human-readable property name.

    The abbreviation "id" is upper-cased to "ID" for human-readable text, though we
    leave it as "id" in the code.

    >>> human_readable_property_name('some_URL_to_id')
    "some URL to ID"

    >>> human_readable_property_name('some_URL_to_ids')
    "some URL to IDs"
    """
    if name == "id":
        return "ID"

    if name == "ids":
        return "IDs"

    parts = name.split("_")
    if len(parts) == 1:
        return name

    human_readable_parts = []  # type: List[str]
    for part in parts:
        if part == "id":
            human_readable_parts.append("ID")
        elif part == "ids":
            human_readable_parts.append("IDs")
        else:
            human_readable_parts.append(part)

    return " ".join(human_readable_parts)


def assert_subclasses_correspond_to_enumeration_literals(
    symbol_table: intermediate.SymbolTable,
    cls: Union[intermediate.ConcreteClass, intermediate.AbstractClass],
    enumeration_or_set: Union[
        intermediate.Enumeration, intermediate.ConstantSetOfEnumerationLiterals
    ],
) -> None:
    """
    Check that all the subclasses (including the class itself) are
    represented in the enumeration.
    """
    errors = []  # type: List[str]

    class_name_set = set()  # type: Set[aas_core_codegen.common.Identifier]

    for our_type in symbol_table.our_types:
        if not isinstance(
            our_type, (intermediate.AbstractClass, intermediate.ConcreteClass)
        ):
            continue

        # We also include ``Identifiable``.
        if our_type.is_subclass_of(cls):
            class_name_set.add(our_type.name)

    literal_set = {literal.name for literal in enumeration_or_set.literals}

    if class_name_set != literal_set:
        errors.append(
            f"""\
The sub-classes of {cls.name} do not correspond to {enumeration_or_set.name}.

Observed classes:  {sorted(class_name_set)!r}
Observed literals: {sorted(literal_set)!r}"""
        )

    if len(errors) != 0:
        raise AssertionError("\n".join(f"* {error}" for error in errors))


def assert_all_lists_have_min_length_at_least_one(
    symbol_table: intermediate.SymbolTable,
    constraints_by_class: MutableMapping[
        intermediate.ClassUnion, infer_for_schema.ConstraintsByProperty
    ],
) -> None:
    """Assert that all lists are constrained to at least one item."""
    # List of (property reference, error message)
    errors = []  # type: List[Tuple[str, str]]

    for our_type in symbol_table.our_types:
        if not isinstance(
            our_type, (intermediate.AbstractClass, intermediate.ConcreteClass)
        ):
            continue

        constraints_by_prop = constraints_by_class.get(our_type, None)

        for prop in our_type.properties:
            if isinstance(
                intermediate.beneath_optional(prop.type_annotation),
                intermediate.ListTypeAnnotation,
            ):
                if constraints_by_prop is None:
                    errors.append(
                        (
                            f"{our_type.name}.{prop.name}",
                            f"Inferred no constraints for our type {our_type.name}",
                        )
                    )
                    continue

                len_constraints = constraints_by_prop.len_constraints_by_property.get(
                    prop, None
                )
                if len_constraints is None:
                    errors.append(
                        (
                            f"{our_type.name}.{prop.name}",
                            "Inferred no length constraints for the property",
                        )
                    )
                    continue

                if len_constraints.min_value is None:
                    errors.append(
                        (
                            f"{our_type.name}.{prop.name}",
                            "Inferred no minimum length constraint for the property",
                        )
                    )
                    continue

                if len_constraints.min_value < 1:
                    errors.append(
                        (
                            f"{our_type.name}.{prop.name}",
                            f"Inferred the minimum length constraints of "
                            f"{len_constraints.min_value}",
                        )
                    )
                    continue

    if len(errors) != 0:
        joined_errors = "\n".join(
            f"* {prop_ref}: {message}" for prop_ref, message in errors
        )
        raise AssertionError(
            f"Expected to infer the minimum length for the following lists "
            f"as at least 1, but:\n"
            f"{joined_errors}"
        )
