import difflib
import pathlib
import sys
import unittest
from typing import Optional, List, Sequence

import aas_core_codegen
from aas_core_codegen import intermediate
from aas_core_codegen.common import Identifier
from icontract import ensure

import aas_core_meta.v3
import aas_core_meta.v3_http
import tests.common


@ensure(lambda result: not (result is not None) or len(result) > 0)
def compute_diff_text(text: str, other: str) -> Optional[str]:
    r"""
    Compute a diff on two texts.

    >>> compute_diff_text('hello\nworld\n!', 'hello\n!')
    '  hello\n- world\n  !'

    >>> compute_diff_text('hello!', 'hello!')
    """
    if text == other:
        return None

    return "\n".join(difflib.ndiff(text.splitlines(), other.splitlines()))


_META_MODEL: tests.common.MetaModel = tests.common.load_meta_model(
    pathlib.Path(aas_core_meta.v3_http.__file__)
)


def _assert_meta_data_class_valid(
        original_class: intermediate.ConcreteClass,
        meta_data_class: intermediate.ConcreteClass,
        names_of_expected_missing_properties: Sequence[Identifier]
) -> None:
    """Assert that the properties are either identical or expectedly missing."""
    if meta_data_class.description is not None:
        raise AssertionError(
            f"Unexpected description in the meta-data class {meta_data_class.name!r}. "
            f"We forbid descriptions to avoid confusing copy/pastes."
        )

    for prop_name in names_of_expected_missing_properties:
        if prop_name in meta_data_class.properties_by_name:
            raise AssertionError(
                f"Unexpected property {prop_name!r} "
                f"in the class {meta_data_class.name!r}"
            )

    for prop in meta_data_class.properties:
        if prop.name not in original_class.properties_by_name:
            raise AssertionError(
                f"Unexpected property {prop.name} present "
                f"in the meta-data class {meta_data_class.name!r}, "
                f"but missing in the original class {original_class.name!r}"
            )

        this_type_anno = prop.type_annotation
        that_type_anno = original_class.properties_by_name[prop.name].type_annotation
        if not intermediate.type_annotations_equal(
                this_type_anno,
                that_type_anno
        ):
            raise AssertionError(
                f"Mismatching type annotations for the property {prop.name!r} in "
                f"the meta-data class {meta_data_class.name!r} "
                f"and the original class {original_class.name!r}: "
                f"{this_type_anno} != {that_type_anno}"
            )

        if prop.specified_for is meta_data_class and prop.description is not None:
            raise AssertionError(
                f"Unexpected description about the property {prop.name!r} "
                f"in the meta-data class {meta_data_class.name!r}. We forbid "
                f"duplicating descriptions to avoid confusing copy/pastes."
            )

    # TODO (mristin, 2024-06-28):
    #  check for equal methods except for expected missing methods

    # TODO (mristin, 2024-06-28): check for missing invariants somehow, e.g.,
    #   check that only the listed invariants are missing.

def _assert_asset_administration_shell_metadata_class_valid(
        symbol_table: intermediate.SymbolTable
) -> None:
    """Assert that the meta-data class exists and check the properties."""
    expected_missing_properties = [
        "asset_information",
        "submodels"
    ]

    original_cls = symbol_table.must_find_concrete_class(
        Identifier("Asset_administration_shell")
    )

    meta_data_cls = symbol_table.must_find_concrete_class(
        Identifier("Asset_administration_shell_meta_data")
    )

    for prop_name in expected_missing_properties:
        if prop_name in meta_data_cls.properties_by_name:
            raise AssertionError(f"Unexpected property {prop_name!r} ")


class Test_assertions(unittest.TestCase):
    def test_module_inheritance(self) -> None:
        """
        Test that all the definitions are inherited from the original meta-model.

        We exclude :py:class:`v3.Environment` as it is not used in the API.
        """
        v3 = tests.common.load_meta_model(
            model_path=pathlib.Path(aas_core_meta.v3.__file__)
        )

        assert _META_MODEL.symbol_table.find_our_type(
            Identifier('Environment')) is None, (
            f"The class ``Environment`` should not be defined "
            f"in {aas_core_meta.v3_http.__file__}, but it was."
        )

        for our_type in v3.symbol_table.our_types:
            if our_type.name == "Environment":
                continue

            other_our_type = _META_MODEL.symbol_table.find_our_type(our_type.name)
            if other_our_type is None:
                raise AssertionError(
                    f"Our type {our_type.name!r} is missing "
                    f"in {aas_core_meta.v3_http.__file__}, "
                    f"but defined in {aas_core_meta.v3.__file__}"
                )

            # noinspection PyTypeChecker
            diff = compute_diff_text(
                text=v3.atok.get_text(our_type.parsed.node),
                other=_META_MODEL.atok.get_text(other_our_type.parsed.node),
            )

            if diff is not None:
                raise AssertionError(
                    f"The text for our type {our_type.name!r} differs "
                    f"between {aas_core_meta.v3.__file__} and "
                    f"{aas_core_meta.v3_http.__file__}. Diff:\n"
                    f"{diff}"
                )

    # NOTE (mristin, 2023-01-25):
    # We do not state "ID" as an abbreviation (which might imply "Identity Document"),
    # but rather expect "Id" or "id", short for "identifier".
    #
    # See: https://english.stackexchange.com/questions/101248/how-should-the-abbreviation-for-identifier-be-capitalized
    LOWER_TO_ABBREVIATION = {
        "aas": "AAS",
        "bcp": "BCP",
        "din": "DIN",
        "ece": "ECE",
        "html": "HTML",
        "id": "ID",
        "ids": "IDs",
        "iec": "IEC",
        "irdi": "IRDI",
        "iri": "IRI",
        "mime": "MIME",
        "nist": "NIST",
        "rfc": "RFC",
        "si": "SI",
        "uri": "URI",
        "url": "URL",
        "utc": "UTC",
        "xml": "XML",
        "xsd": "XSD",
        "w3c": "W3C",
        "did": "DID",
        "ssp": "SSP",
        "aasx": "AASX",
        "tlsa": "TLSA"
    }

    ABBREVIATIONS = set(LOWER_TO_ABBREVIATION.values())

    @staticmethod
    def check_class_name(name: aas_core_codegen.common.Identifier) -> List[str]:
        errors = []  # type: List[str]

        parts = name.split("_")  # type: List[str]

        if parts[0] not in Test_assertions.ABBREVIATIONS:
            if parts[0] != parts[0].capitalize():
                errors.append(
                    f"Expected first part of a class name "
                    f"to be capitalized ({parts[0].capitalize()!r}), "
                    f"but it was not ({parts[0]!r}) for class {name!r}"
                )

        for part in parts:
            expected_part = Test_assertions.LOWER_TO_ABBREVIATION.get(
                part.lower(), None
            )

            if expected_part is not None and part != expected_part:
                errors.append(
                    f"Expected a part of a class name "
                    f"to be {expected_part!r} "
                    f"since it denotes an abbreviation, "
                    f"but got {part!r} for the class {name!r}"
                )

        for part in parts[1:]:
            if part not in Test_assertions.ABBREVIATIONS:
                if part.lower() != part:
                    errors.append(
                        f"Expected a non-first part of a class name "
                        f"to be lower-case ({part.lower()}) "
                        f"since it was not registered as an abbreviation, "
                        f"but it was not ({part!r}) "
                        f"for class {name!r}"
                    )

        return errors

    @staticmethod
    def check_enum_literal_name(name: aas_core_codegen.common.Identifier) -> List[str]:
        errors = []  # type: List[str]

        parts = name.split("_")  # type: List[str]

        if parts[0] not in Test_assertions.ABBREVIATIONS:
            if parts[0] != parts[0].capitalize():
                errors.append(
                    f"Expected first part of an enumeration literal name "
                    f"to be capitalized ({parts[0].capitalize()!r}), "
                    f"but it was not ({parts[0]!r}) for enumeration literal {name!r}"
                )

        for part in parts:
            expected_part = Test_assertions.LOWER_TO_ABBREVIATION.get(
                part.lower(), None
            )

            if expected_part is not None and part != expected_part:
                errors.append(
                    f"Expected a part of an enumeration literal name "
                    f"to be {expected_part!r} since it denotes an abbreviation, "
                    f"but got {part!r} for enumeration literal {name!r}"
                )

        for part in parts[1:]:
            if part not in Test_assertions.ABBREVIATIONS:
                if part.lower() != part:
                    errors.append(
                        f"Expected a non-first part of an enumeration literal name "
                        f"to be lower-case ({part.lower()}) "
                        f"since it was not registered as an abbreviation, "
                        f"but it was not ({part!r}) "
                        f"for enumeration literal {name!r}"
                    )

        return errors

    @staticmethod
    def check_property_name(name: aas_core_codegen.common.Identifier) -> List[str]:
        errors = []  # type: List[str]

        parts = name.split("_")  # type: List[str]

        for part in parts:
            expected_part = Test_assertions.LOWER_TO_ABBREVIATION.get(
                part.lower(), None
            )

            if expected_part is not None and part != expected_part:
                errors.append(
                    f"Expected a part of a property name "
                    f"to be {expected_part!r} "
                    f"since it denotes an abbreviation, "
                    f"but got {part!r} for the property {name!r}"
                )

        for part in parts:
            if part not in Test_assertions.ABBREVIATIONS:
                if part.lower() != part:
                    errors.append(
                        f"Expected a part of a property name "
                        f"to be lower-case ({part.lower()}) "
                        f"since it was not registered as an abbreviation, "
                        f"but it was not ({part!r}) "
                        f"for the property {name!r}"
                    )

        return errors

    @staticmethod
    def check_method_name(name: aas_core_codegen.common.Identifier) -> List[str]:
        errors = []  # type: List[str]

        parts = name.split("_")  # type: List[str]

        for part in parts:
            expected_part = Test_assertions.LOWER_TO_ABBREVIATION.get(
                part.lower(), None
            )

            if expected_part is not None and part != expected_part:
                errors.append(
                    f"Expected a part of a method name "
                    f"to be {expected_part!r} "
                    f"since it denotes an abbreviation, "
                    f"but got {part!r} for the method {name!r}"
                )

        for part in parts:
            if part not in Test_assertions.ABBREVIATIONS:
                if part.lower() != part:
                    errors.append(
                        f"Expected a part of a method name "
                        f"to be lower-case ({part.lower()}) "
                        f"since it was not registered as an abbreviation, "
                        f"but it was not ({part!r}) "
                        f"for the method {name!r}"
                    )

        return errors

    @staticmethod
    def check_function_name(name: aas_core_codegen.common.Identifier) -> List[str]:
        errors = []  # type: List[str]

        parts = name.split("_")  # type: List[str]

        for part in parts:
            expected_part = Test_assertions.LOWER_TO_ABBREVIATION.get(
                part.lower(), None
            )

            if expected_part is not None and part != expected_part:
                errors.append(
                    f"Expected a part of a function name "
                    f"to be {expected_part!r} "
                    f"since it denotes an abbreviation, "
                    f"but got {part!r} for the function {name!r}"
                )

        for part in parts:
            if part not in Test_assertions.ABBREVIATIONS:
                if part.lower() != part:
                    errors.append(
                        f"Expected a part of a function name "
                        f"to be lower-case ({part.lower()}) "
                        f"since it was not registered as an abbreviation, "
                        f"but it was not ({part!r}) "
                        f"for the function {name!r}"
                    )

        return errors

    @staticmethod
    def needs_plural(type_annotation: intermediate.TypeAnnotationUnion) -> bool:
        lang_string_cls = _META_MODEL.symbol_table.must_find_class(
            aas_core_codegen.common.Identifier("Abstract_lang_string")
        )

        type_anno = intermediate.beneath_optional(type_annotation)

        return isinstance(type_anno, intermediate.ListTypeAnnotation) and not (
                isinstance(type_anno.items, intermediate.OurTypeAnnotation)
                and type_anno.items.our_type.is_subclass_of(lang_string_cls)
        )

    def test_naming(self) -> None:
        errors = []  # type: List[str]

        hard_wired_plural_exceptions = {
            "Concept_description.is_case_of",
            "Submodel_element_collection.value",
            "Submodel_element_list.value",
            "Extension.refers_to",
            "Get_asset_administration_shells_result.result",
            "Get_submodel_result.result",
        }

        symbol_table = _META_MODEL.symbol_table

        for our_type in symbol_table.our_types:
            errors.extend(Test_assertions.check_class_name(name=our_type.name))

            # We descend and check literals, properties *etc.*

            if isinstance(our_type, intermediate.Enumeration):
                for literal in our_type.literals:
                    errors.extend(
                        Test_assertions.check_enum_literal_name(name=literal.name)
                    )

            elif isinstance(our_type, intermediate.ConstrainedPrimitive):
                # NOTE (mristin, 2022-08-19):
                # There are no names to be checked beneath the constrained primitive.
                pass

            elif isinstance(
                    our_type,
                    (intermediate.AbstractClass, intermediate.ConcreteClass)
            ):
                for prop in our_type.properties:
                    errors.extend(Test_assertions.check_property_name(prop.name))

                    qualified_name = f"{our_type.name}.{prop.name}"

                    if (
                            Test_assertions.needs_plural(prop.type_annotation)
                            and qualified_name not in hard_wired_plural_exceptions
                            and not prop.name.endswith("s")
                    ):
                        errors.append(
                            f"Expected the property to have a suffix '-s', "
                            f"but it does not: {qualified_name}"
                        )

                for method in our_type.methods:
                    errors.extend(Test_assertions.check_method_name(method.name))

            else:
                aas_core_codegen.common.assert_never(our_type)

        for func in symbol_table.verification_functions:
            errors.extend(Test_assertions.check_function_name(func.name))

        if len(errors) != 0:
            raise AssertionError("\n".join(f"* {error}" for error in errors))

    def test_meta_data_classes_properly_defined(self) -> None:
        # NOTE (mristin):
        # Listed from:
        # https://industrialdigitaltwin.org/wp-content/uploads/2023/06/IDTA-01002-3-0_SpecificationAssetAdministrationShell_Part2_API_.pdf#page=118
        for (
                original_cls_name,
                names_of_expected_missing_property
        ) in [
            ("Asset_administration_shell", ["asset_information", "submodels"]),
            ("Submodel", ["submodel_elements"]),
            ("Submodel_element", []),
            ("Submodel_element_collection", ["value"]),
            ("Submodel_element_list", ["value"]),
            ("Entity", ["statements", "global_asset_ID", "specific_asset_ID"]),
            ("Event_element", []),
            ("Basic_event_element", ["observed"]),
            ("Capability", []),
            ("Operation", []),
            ("Property", ["value", "value_ID"]),
            ("Multi_language_property", ["value", "value_ID"]),
            ("Range", ["min", "max"]),
            ("Reference_element", ["value"]),
            ("Relationship_element", ["first", "second"]),
            ("Annotated_relationship_element", ["first", "second", "annotations"]),
            ("Blob", ["value", "content_type"]),
            ("File", ["value", "content_type"])
        ]:
            original_cls = _META_MODEL.symbol_table.find_our_type(
                Identifier(original_cls_name)
            )
            if original_cls is None:
                raise AssertionError(f"Missing original class: {original_cls_name!r}")

            meta_data_cls_name = Identifier(original_cls_name + "_meta_data")
            meta_data_cls = _META_MODEL.symbol_table.find_our_type(
                meta_data_cls_name
            )
            if meta_data_cls is None:
                raise AssertionError(f"Missing meta-data class: {meta_data_cls_name!r}")

            _assert_meta_data_class_valid(
                original_class=original_cls,
                meta_data_class=meta_data_cls,
                names_of_expected_missing_properties=names_of_expected_missing_property
            )


if __name__ == "__main__":
    unittest.main()
