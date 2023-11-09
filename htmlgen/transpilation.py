"""Transpile meta-model Python code to Python code."""
import abc
import html
import io
from typing import (
    Tuple,
    Optional,
    List,
    Mapping,
    Union,
    Set,
    Sequence,
)

from aas_core_codegen import intermediate
from aas_core_codegen.common import (
    Error,
    Stripped,
    assert_never,
    Identifier,
    indent_but_first_line,
)
from aas_core_codegen.intermediate import type_inference as intermediate_type_inference
from aas_core_codegen.parse import tree as parse_tree
from aas_core_codegen.python import (
    common as python_common,
)
from aas_core_codegen.python.common import (
    INDENT as I,
)
from icontract import ensure, require

import htmlgen.common
import htmlgen.description
import htmlgen.naming

# noinspection SpellCheckingInspection
LPAREN = "<span class='p'>(</span>"
# noinspection SpellCheckingInspection
RPAREN = "<span class='p'>)</span>"
NONE = "<span class='kc'>None</span>"


def _enclose_in_highlight_div_pre(text: str) -> Stripped:
    """Enclose the HTML text in the appropriate ``<div>`` and ``<pre>``."""
    return Stripped(f"<div class='highlight'><pre>{text}</pre></div>")


class _Transpiler(
    parse_tree.RestrictedTransformer[Tuple[Optional[Stripped], Optional[Error]]]
):
    """Transpile a node of our AST to Python code, or return an error."""

    def __init__(
        self,
        type_map: Mapping[
            parse_tree.Node, intermediate_type_inference.TypeAnnotationUnion
        ],
        environment: intermediate_type_inference.Environment,
    ) -> None:
        """Initialize with the given values."""
        self.type_map = type_map
        self._environment = intermediate_type_inference.MutableEnvironment(
            parent=environment
        )

        # NOTE (mristin, 2023-10-20):
        # Keep track whenever we define a variable name, so that we can know how to
        # resolve it as a name in the Python code.
        #
        # While this class does not directly use it, the descendants of this class do!
        self._variable_name_set = set()  # type: Set[Identifier]

    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_member(
        self, node: parse_tree.Member
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        instance, error = self.transform(node.instance)
        if error is not None:
            return None, error

        # Ignore optionals as they need to be checked before in the code
        instance_type = intermediate_type_inference.beneath_optional(
            self.type_map[node.instance]
        )
        member_type = intermediate_type_inference.beneath_optional(self.type_map[node])

        # noinspection PyUnusedLocal
        member_name = None  # type: Optional[str]

        # noinspection PyUnusedLocal
        href = None  # type: Optional[str]

        if isinstance(
            instance_type, intermediate_type_inference.OurTypeAnnotation
        ) and isinstance(instance_type.our_type, intermediate.Enumeration):
            # The member denotes a literal of an enumeration.
            member_name = htmlgen.naming.enum_literal_name(node.name)

            href = f"{htmlgen.naming.of(instance_type.our_type)}.html#{member_name}"

        elif isinstance(
            instance_type, intermediate_type_inference.OurTypeAnnotation
        ) and isinstance(instance_type.our_type, intermediate.Class):
            if node.name in instance_type.our_type.properties_by_name:
                member_name = htmlgen.naming.property_name(node.name)

            elif node.name in instance_type.our_type.methods_by_name:
                member_name = htmlgen.naming.method_name(node.name)
            else:
                return None, Error(
                    node.original_node,
                    f"The property or method {node.name!r} has not been defined "
                    f"in the class {instance_type.our_type.name!r}",
                )

            href = f"{htmlgen.naming.of(instance_type.our_type)}.html#{member_name}"

        elif isinstance(
            instance_type, intermediate_type_inference.EnumerationAsTypeTypeAnnotation
        ):
            if node.name in instance_type.enumeration.literals_by_name:
                member_name = htmlgen.naming.enum_literal_name(node.name)
            else:
                return None, Error(
                    node.original_node,
                    f"The literal {node.name!r} has not been defined "
                    f"in the enumeration {instance_type.enumeration.name!r}",
                )

            href = f"{htmlgen.naming.of(instance_type.enumeration)}.html#{member_name}"

        else:
            return None, Error(
                node.original_node,
                f"We do not know how to generate the member access. The inferred type "
                f"of the instance was {instance_type}, while the member type "
                f"was {member_type}. However, we do not know how to resolve "
                f"the member {node.name!r} in {instance_type}.",
            )

        assert member_name is not None

        no_parentheses_types_in_this_context = (
            parse_tree.Member,
            parse_tree.FunctionCall,
            parse_tree.MethodCall,
            parse_tree.Name,
            parse_tree.Index,
        )

        if not isinstance(node.instance, no_parentheses_types_in_this_context):
            instance = Stripped(f"{LPAREN}{instance}{RPAREN}")

        dot = "<span class='o'>.</span>"

        if href is None:
            return Stripped(f"{instance}{dot}{member_name}"), None

        return Stripped(f'{instance}{dot}<a href="{href}">{member_name}</a>'), None

    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_index(
        self, node: parse_tree.Index
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        collection, error = self.transform(node.collection)
        if error is not None:
            return None, error

        index, error = self.transform(node.index)
        if error is not None:
            return None, error
        assert index is not None

        no_parentheses_types = (
            parse_tree.Member,
            parse_tree.FunctionCall,
            parse_tree.MethodCall,
            parse_tree.Name,
            parse_tree.Constant,
            parse_tree.Index,
        )

        if not isinstance(node.collection, no_parentheses_types):
            collection = Stripped(f"{LPAREN}{collection}{RPAREN}")

        return Stripped(f"{collection}[{index}]"), None

    _PYTHON_COMPARISON_MAP = {
        parse_tree.Comparator.LT: "<",
        parse_tree.Comparator.LE: "<=",
        parse_tree.Comparator.GT: ">",
        parse_tree.Comparator.GE: ">=",
        parse_tree.Comparator.EQ: "==",
        parse_tree.Comparator.NE: "!=",
    }

    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_comparison(
        self, node: parse_tree.Comparison
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        comparator = _Transpiler._PYTHON_COMPARISON_MAP[node.op]

        errors = []

        left, error = self.transform(node.left)
        if error is not None:
            errors.append(error)

        right, error = self.transform(node.right)
        if error is not None:
            errors.append(error)

        if len(errors) > 0:
            return None, Error(
                node.original_node, "Failed to transpile the comparison", errors
            )

        no_parentheses_types = (
            parse_tree.Member,
            parse_tree.FunctionCall,
            parse_tree.MethodCall,
            parse_tree.Name,
            parse_tree.Constant,
            parse_tree.Index,
        )

        html_comparator = f"<span class='o'>{html.escape(comparator)}</span>"

        if isinstance(node.left, no_parentheses_types) and isinstance(
            node.right, no_parentheses_types
        ):
            return Stripped(f"{left} {html_comparator} {right}"), None

        return (
            Stripped(
                f"{LPAREN}{left}{RPAREN} {html_comparator} {LPAREN}{right}{RPAREN}"
            ),
            None,
        )

    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_is_in(
        self, node: parse_tree.IsIn
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        errors = []

        member, error = self.transform(node.member)
        if error is not None:
            errors.append(error)

        container, error = self.transform(node.container)
        if error is not None:
            errors.append(error)

        if len(errors) > 0:
            return None, Error(
                node.original_node,
                "Failed to transpile the membership relation",
                errors,
            )

        assert member is not None
        assert container is not None

        no_parentheses_types = (
            parse_tree.Member,
            parse_tree.FunctionCall,
            parse_tree.MethodCall,
            parse_tree.Name,
            parse_tree.Constant,
            parse_tree.Index,
        )

        if not isinstance(node.container, no_parentheses_types):
            container = Stripped(f"{LPAREN}{container}{RPAREN}")

        if not isinstance(node.member, no_parentheses_types):
            member = Stripped(f"{LPAREN}{member}{RPAREN}")

        return Stripped(f"{member} <span class='ow'>in</span> {container}"), None

    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_implication(
        self, node: parse_tree.Implication
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        errors = []

        antecedent, error = self.transform(node.antecedent)
        if error is not None:
            errors.append(error)

        consequent, error = self.transform(node.consequent)
        if error is not None:
            errors.append(error)

        if len(errors) > 0:
            return None, Error(
                node.original_node, "Failed to transpile the implication", errors
            )

        assert antecedent is not None
        assert consequent is not None

        no_parentheses_types_in_this_context = (
            parse_tree.Member,
            parse_tree.FunctionCall,
            parse_tree.MethodCall,
            parse_tree.Name,
            parse_tree.Index,
        )

        not_html = "<span class='ow'>not</span>"

        if isinstance(node.antecedent, no_parentheses_types_in_this_context):
            not_antecedent = f"{not_html} {antecedent}"
        else:
            # NOTE (mristin, 2023-10-20):
            # This is a very rudimentary heuristic for breaking the lines, and can be
            # greatly improved by rendering into Python code. However, at this point, we
            # lack time for more sophisticated reformatting approaches.
            if "\n" in antecedent:
                not_antecedent = f"""\
{not_html} {LPAREN}
{I}{indent_but_first_line(antecedent, I)}
{RPAREN}"""
            else:
                not_antecedent = f"{not_html} {LPAREN}{antecedent}{RPAREN}"

        if not isinstance(node.consequent, no_parentheses_types_in_this_context):
            # NOTE (mristin, 2023-10-20):
            # This is a very rudimentary heuristic for breaking the lines, and can be
            # greatly improved by rendering into Python code. However, at this point, we
            # lack time for more sophisticated reformatting approaches.
            if "\n" in consequent:
                consequent = Stripped(
                    f"""\
{LPAREN}
{I}{indent_but_first_line(consequent, I)}
{RPAREN}"""
                )
            else:
                consequent = Stripped(f"{LPAREN}{consequent}{RPAREN}")

        return (
            Stripped(
                f"""\
{not_antecedent}
<span class='ow'>or</span> {consequent}"""
            ),
            None,
        )

    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_method_call(
        self, node: parse_tree.MethodCall
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        errors = []  # type: List[Error]

        member, error = self.transform(node.member)
        if error is not None:
            errors.append(error)

        args = []  # type: List[Stripped]
        for arg_node in node.args:
            arg, error = self.transform(arg_node)
            if error is not None:
                errors.append(error)
                continue

            assert arg is not None

            args.append(arg)

        if len(errors) > 0:
            return None, Error(
                node.original_node, "Failed to transpile the method call", errors
            )

        assert member is not None

        joined_args = ", ".join(args)
        if len(joined_args) > 50:
            joined_args = ",\n".join(args)
            return (
                Stripped(
                    f"""\
{member}{LPAREN}
{I}{indent_but_first_line(joined_args, I)}
{RPAREN}"""
                ),
                None,
            )

        else:
            return Stripped(f"{member}{LPAREN}{joined_args}{RPAREN}"), None

    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_function_call(
        self, node: parse_tree.FunctionCall
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        errors = []  # type: List[Error]

        args = []  # type: List[Stripped]
        for arg_node in node.args:
            arg, error = self.transform(arg_node)
            if error is not None:
                errors.append(error)
                continue

            assert arg is not None

            args.append(arg)

        if len(errors) > 0:
            return None, Error(
                node.original_node, "Failed to transpile the function call", errors
            )

        # NOTE (mristin, 2023-10-20):
        # The validity of the arguments is checked in
        # :py:func:`aas_core_codegen.intermediate._translate.translate`, so we do not
        # have to test for argument arity here.

        func_type = self.type_map[node.name]

        if not isinstance(
            func_type, intermediate_type_inference.FunctionTypeAnnotationUnionAsTuple
        ):
            return None, Error(
                node.name.original_node,
                f"Expected the name to refer to a function, "
                f"but its inferred type was {func_type}",
            )

        if isinstance(
            func_type, intermediate_type_inference.VerificationTypeAnnotation
        ):
            function_name, error = self.transform_name(node.name)
            if error is not None:
                return None, error

            assert function_name is not None

            joined_args = ", ".join(args)

            # Apply heuristic for breaking the lines
            if len(function_name) + len(joined_args) > 50:
                joined_args = ",\n".join(args)
                return (
                    Stripped(
                        f"""\
{function_name}{LPAREN}
{I}{indent_but_first_line(joined_args, I)}
{RPAREN}"""
                    ),
                    None,
                )
            else:
                return Stripped(f"{function_name}{LPAREN}{joined_args}{RPAREN}"), None

        elif isinstance(
            func_type, intermediate_type_inference.BuiltinFunctionTypeAnnotation
        ):
            if func_type.func.name == "len":
                assert len(args) == 1, (
                    f"Expected exactly one argument, but got: {args}; "
                    f"this should have been caught before."
                )

                return (
                    Stripped(f"<span class='nb'>len</span>{LPAREN}{args[0]}{RPAREN}"),
                    None,
                )
            elif func_type.func.name == "match":
                joined_args = ",\n".join(args)

                return (
                    Stripped(
                        f"<span class='nb'>match</span>{LPAREN}\n"
                        f"{I}{indent_but_first_line(joined_args, I)}\n"
                        f"{RPAREN}"
                    ),
                    None,
                )
            else:
                return None, Error(
                    node.original_node,
                    f"The handling of the built-in function {node.name.identifier!r} "
                    f"has not been implemented",
                )
        else:
            assert_never(func_type)

        raise AssertionError("Should not have gotten here")

    def transform_constant(
        self, node: parse_tree.Constant
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        if isinstance(node.value, bool):
            return Stripped("True" if node.value else "False"), None
        elif isinstance(node.value, (int, float)):
            return Stripped(str(node.value)), None
        elif isinstance(node.value, str):
            return (
                Stripped(
                    f"<span class='sc'>{html.escape(python_common.string_literal(node.value))}</span>"
                ),
                None,
            )
        elif isinstance(node.value, bytes):
            literal, multiline = python_common.bytes_literal(node.value)

            literal = f"<span class='sc'>{html.escape(literal)}</span>"

            if not multiline:
                return Stripped(literal), None
            else:
                return (
                    Stripped(
                        f"""\
{LPAREN}
{I}{indent_but_first_line(literal, I)}
{RPAREN}"""
                    ),
                    None,
                )
        else:
            assert_never(node.value)

        raise AssertionError("Should not have gotten here")

    def transform_is_none(
        self, node: parse_tree.IsNone
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        value, error = self.transform(node.value)
        if error is not None:
            return None, error

        no_parentheses_types = (
            parse_tree.Name,
            parse_tree.Member,
            parse_tree.MethodCall,
            parse_tree.FunctionCall,
            parse_tree.Index,
        )

        is_html = "<span class='ow'>is</span>"

        if isinstance(node.value, no_parentheses_types):
            return Stripped(f"{value} {is_html} {NONE}"), None
        else:
            return Stripped(f"{LPAREN}{value}{RPAREN} {is_html} {NONE}"), None

    def transform_is_not_none(
        self, node: parse_tree.IsNotNone
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        value, error = self.transform(node.value)
        if error is not None:
            return None, error

        no_parentheses_types_in_this_context = (
            parse_tree.Name,
            parse_tree.Member,
            parse_tree.MethodCall,
            parse_tree.FunctionCall,
            parse_tree.Index,
        )

        is_not = "<span class='ow'>is not</span>"

        if isinstance(node.value, no_parentheses_types_in_this_context):
            return Stripped(f"{value} {is_not} {NONE}"), None
        else:
            return Stripped(f"{LPAREN}{value}{RPAREN} {is_not} {NONE}"), None

    @abc.abstractmethod
    def transform_name(
        self, node: parse_tree.Name
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        raise NotImplementedError()

    def transform_not(
        self, node: parse_tree.Not
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        operand, error = self.transform(node.operand)
        if error is not None:
            return None, error

        no_parentheses_types_in_this_context = (
            parse_tree.Name,
            parse_tree.Member,
            parse_tree.MethodCall,
            parse_tree.FunctionCall,
            parse_tree.Index,
        )

        not_html = "<span class='ow'>not</span>"

        if not isinstance(node.operand, no_parentheses_types_in_this_context):
            return Stripped(f"{not_html} {LPAREN}{operand}{RPAREN}"), None
        else:
            return Stripped(f"{not_html} {operand}"), None

    def _transform_and_or_or(
        self, node: Union[parse_tree.And, parse_tree.Or]
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        errors = []  # type: List[Error]
        values = []  # type: List[Stripped]

        for value_node in node.values:
            value, error = self.transform(value_node)
            if error is not None:
                errors.append(error)
                continue

            assert value is not None

            no_parentheses_types_in_this_context = (
                parse_tree.Member,
                parse_tree.MethodCall,
                parse_tree.FunctionCall,
                parse_tree.Name,
                parse_tree.Index,
                parse_tree.Comparison,
            )

            if not isinstance(value_node, no_parentheses_types_in_this_context):
                # NOTE (mristin, 2023-10-20):
                # This is a very rudimentary heuristic for breaking the lines, and can
                # be greatly improved by rendering into Python code. However, at this
                # point, we lack time for more sophisticated reformatting approaches.
                if "\n" in value:
                    value = Stripped(
                        f"""\
{LPAREN}
{I}{indent_but_first_line(value, I)}
{RPAREN}"""
                    )
                else:
                    value = Stripped(f"{LPAREN}{value}{RPAREN}")

            values.append(value)

        if len(errors) > 0:
            if isinstance(node, parse_tree.And):
                return None, Error(
                    node.original_node, "Failed to transpile the conjunction", errors
                )
            elif isinstance(node, parse_tree.Or):
                return None, Error(
                    node.original_node, "Failed to transpile the disjunction", errors
                )
            else:
                assert_never(node)

        assert len(values) >= 1
        if len(values) == 1:
            return Stripped(values[0]), None

        and_html = "<span class='ow'>and</span>"
        or_html = "<span class='ow'>or</span>"

        writer = io.StringIO()
        writer.write(f"{LPAREN}\n")
        for i, value in enumerate(values):
            if i == 0:
                writer.write(f"{I}{indent_but_first_line(value, I)}\n")
            else:
                if isinstance(node, parse_tree.And):
                    writer.write(f"{I}{and_html} {indent_but_first_line(value, I)}\n")
                elif isinstance(node, parse_tree.Or):
                    writer.write(f"{I}{or_html} {indent_but_first_line(value, I)}\n")
                else:
                    assert_never(node)

        writer.write(f"{RPAREN}")

        return Stripped(writer.getvalue()), None

    def transform_and(
        self, node: parse_tree.And
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        return self._transform_and_or_or(node)

    def transform_or(
        self, node: parse_tree.Or
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        return self._transform_and_or_or(node)

    def _transform_add_or_sub(
        self, node: Union[parse_tree.Add, parse_tree.Sub]
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        errors = []  # type: List[Error]

        left, error = self.transform(node.left)
        if error is not None:
            errors.append(error)

        right, error = self.transform(node.right)
        if error is not None:
            errors.append(error)

        if len(errors) > 0:
            operation_name = None  # type: Optional[str]
            if isinstance(node, parse_tree.Add):
                operation_name = "the addition"
            elif isinstance(node, parse_tree.Sub):
                operation_name = "the subtraction"
            else:
                assert_never(node)

            return None, Error(
                node.original_node, f"Failed to transpile {operation_name}", errors
            )

        no_parentheses_types_in_this_context = (
            parse_tree.Member,
            parse_tree.MethodCall,
            parse_tree.FunctionCall,
            parse_tree.Constant,
            parse_tree.Name,
            parse_tree.Index,
        )

        if not isinstance(node.left, no_parentheses_types_in_this_context):
            left = Stripped(f"{LPAREN}{left}{RPAREN}")

        if not isinstance(node.right, no_parentheses_types_in_this_context):
            right = Stripped(f"{LPAREN}{right}{RPAREN}")

        plus = "<span class='o'>+</span>"
        minus = "<span class='o'>-</span>"

        if isinstance(node, parse_tree.Add):
            return Stripped(f"{left} {plus} {right}"), None
        elif isinstance(node, parse_tree.Sub):
            return Stripped(f"{left} {minus} {right}"), None
        else:
            assert_never(node)
            raise AssertionError("Unexpected execution path")

    def transform_add(
        self, node: parse_tree.Add
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        return self._transform_add_or_sub(node)

    def transform_sub(
        self, node: parse_tree.Sub
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        return self._transform_add_or_sub(node)

    def transform_joined_str(
        self, node: parse_tree.JoinedStr
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        # If we do not need interpolation, simply return the string literals
        # joined together by newlines.
        needs_interpolation = any(
            isinstance(value, parse_tree.FormattedValue) for value in node.values
        )
        if not needs_interpolation:
            str_literal = python_common.string_literal(
                "".join(value for value in node.values)  # type: ignore
            )

            return Stripped(f"<span class='sc'>{html.escape(str_literal)}</span>"), None

        parts = []  # type: List[str]

        # NOTE (mristin, 2023-10-20):
        # See which quotes occur more often in the non-interpolated parts, so that we
        # pick the escaping scheme which will result in as little escapes as possible.
        double_quotes_count = 0
        single_quotes_count = 0

        for value in node.values:
            if isinstance(value, str):
                double_quotes_count += value.count('"')
                single_quotes_count += value.count("'")

            elif isinstance(value, parse_tree.FormattedValue):
                pass
            else:
                assert_never(value)

        # Pick the escaping scheme
        if single_quotes_count <= double_quotes_count:
            enclosing = "'"
            quoting = python_common.StringQuoting.SINGLE_QUOTES
        else:
            enclosing = '"'
            quoting = python_common.StringQuoting.DOUBLE_QUOTES

        for value in node.values:
            if isinstance(value, str):
                str_literal = python_common.string_literal(
                    value,
                    quoting=quoting,
                    without_enclosing=True,
                    duplicate_curly_brackets=True,
                )

                parts.append(f"<span class='sc'>{html.escape(str_literal)}</span>")

            elif isinstance(value, parse_tree.FormattedValue):
                code, error = self.transform(value.value)
                if error is not None:
                    return None, error

                assert code is not None

                assert (
                    "\n" not in code
                ), f"New-lines are not expected in formatted values, but got: {code}"

                parts.append(
                    f"<span class='si'>{{</span>{code}<span class='si'>}}</span>"
                )
            else:
                assert_never(value)

        writer = io.StringIO()
        writer.write("<span class='sa'>f</span>")

        enclosing_escaped = html.escape(enclosing)
        if enclosing == "'":
            enclosing_html = f"<span class='s1'>{enclosing_escaped}</span>"
        elif enclosing == '"':
            enclosing_html = f"<span class='s2'>{enclosing_escaped}</span>"
        else:
            raise AssertionError(f"Unexpected enclosing: {enclosing}")

        writer.write(enclosing_html)
        for part in parts:
            writer.write(part)
        writer.write(enclosing_html)

        return Stripped(writer.getvalue()), None

    def _transform_any_or_all(
        self, node: Union[parse_tree.Any, parse_tree.All]
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        errors = []  # type: List[Error]

        iteration = None  # type: Optional[Stripped]
        start = None  # type: Optional[Stripped]
        end = None  # type: Optional[Stripped]

        if isinstance(node.generator, parse_tree.ForEach):
            iteration, error = self.transform(node.generator.iteration)
            if error is not None:
                errors.append(error)
        elif isinstance(node.generator, parse_tree.ForRange):
            start, error = self.transform(node.generator.start)
            if error is not None:
                errors.append(error)

            end, error = self.transform(node.generator.end)
            if error is not None:
                errors.append(error)

        else:
            assert_never(node.generator)

        if len(errors) > 0:
            return None, Error(
                node.original_node,
                "Failed to transpile the generator expression",
                errors,
            )

        assert (iteration is not None) ^ (start is not None and end is not None)

        variable_name = node.generator.variable.identifier
        variable_type = self.type_map[node.generator.variable]

        try:
            self._environment.set(
                identifier=variable_name, type_annotation=variable_type
            )
            self._variable_name_set.add(variable_name)

            condition, error = self.transform(node.condition)
            if error is not None:
                errors.append(error)

            variable, error = self.transform(node.generator.variable)
            if error is not None:
                errors.append(error)

        finally:
            self._variable_name_set.remove(variable_name)
            self._environment.remove(variable_name)

        if len(errors) > 0:
            return None, Error(
                node.original_node,
                "Failed to transpile the generator expression",
                errors,
            )

        assert variable is not None
        assert condition is not None

        qualifier_function = None  # type: Optional[str]
        if isinstance(node, parse_tree.Any):
            qualifier_function = "<span class='nb'>any</span>"
        elif isinstance(node, parse_tree.All):
            qualifier_function = "<span class='nb'>all</span>"
        else:
            assert_never(node)

        source = None  # type: Optional[Stripped]
        if isinstance(node.generator, parse_tree.ForEach):
            no_parentheses_types_in_this_context = (
                parse_tree.Member,
                parse_tree.MethodCall,
                parse_tree.FunctionCall,
                parse_tree.Name,
                parse_tree.Index,
            )

            if not isinstance(
                node.generator.iteration, no_parentheses_types_in_this_context
            ):
                source = Stripped(f"{LPAREN}{iteration}{RPAREN}")
            else:
                source = iteration
        elif isinstance(node.generator, parse_tree.ForRange):
            assert start is not None
            assert end is not None

            source = Stripped(
                f"""\
<span class='nb'>range</span>{LPAREN}
{I}{indent_but_first_line(start, I)},
{I}{indent_but_first_line(end, I)}
{RPAREN}"""
            )

        else:
            assert_never(node.generator)

        assert source is not None

        for_html = "<span class='k'>for</span>"
        in_html = "<span class='ow'>in</span>"

        return (
            Stripped(
                f"""\
{qualifier_function}{LPAREN}
{I}{indent_but_first_line(condition, I)}
{I}{for_html} {variable} {in_html} {indent_but_first_line(source, I)}
{RPAREN}"""
            ),
            None,
        )

    def transform_any(
        self, node: parse_tree.Any
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        return self._transform_any_or_all(node)

    def transform_all(
        self, node: parse_tree.All
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        return self._transform_any_or_all(node)

    def transform_assignment(
        self, node: parse_tree.Assignment
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        errors = []  # type: List[Error]

        value, error = self.transform(node.value)
        if error is not None:
            errors.append(error)

        if isinstance(node.target, parse_tree.Name):
            type_anno = self._environment.find(identifier=node.target.identifier)
            if type_anno is None:
                # NOTE (mristin, 2023-10-20):
                # This is a variable definition as we did not specify the identifier
                # in the environment.

                type_anno = self.type_map[node.value]
                self._variable_name_set.add(node.target.identifier)
                self._environment.set(
                    identifier=node.target.identifier, type_annotation=type_anno
                )

        target, error = self.transform(node=node.target)
        if error is not None:
            errors.append(error)

        if len(errors) > 0:
            return None, Error(
                node.original_node, "Failed to transpile the assignment", errors
            )

        assert target is not None
        assert value is not None

        assign_html = "<span class='o'>=</span>"

        # NOTE (mristin, 2023-10-20):
        # This is a rudimentary heuristic for basic line breaks, but works well in
        # practice.
        if "\n" not in value and len(value) > 50:
            return (
                Stripped(
                    f"""\
{target} {assign_html} {LPAREN}
{I}{indent_but_first_line(value, I)}
{RPAREN}"""
                ),
                None,
            )

        return Stripped(f"{target} {assign_html} {value}"), None

    def transform_return(
        self, node: parse_tree.Return
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        return_html = "<span class='k'>return</span>"

        if node.value is None:
            return Stripped(return_html), None

        value, error = self.transform(node.value)
        if error is not None:
            return None, error

        assert value is not None

        # NOTE (mristin, 2023-10-20):
        # This is a rudimentary heuristic for basic line breaks, but works well in
        # practice.
        if "\n" not in value and len(value) > 50:
            return (
                Stripped(
                    f"""\
{return_html} {LPAREN}
{I}{indent_but_first_line(value, I)}
{RPAREN}"""
                ),
                None,
            )

        return Stripped(f"{return_html} {value}"), None


# noinspection PyProtectedMember,PyProtectedMember
assert all(op in _Transpiler._PYTHON_COMPARISON_MAP for op in parse_tree.Comparator)


class _TranspilableVerificationTranspiler(_Transpiler):
    """Transpile the body of a :class:`.TranspilableVerification`."""

    # fmt: off
    @require(
        lambda environment, verification:
        all(
            environment.find(arg.name) is not None
            for arg in verification.arguments
        ),
        "All arguments defined in the environment"
    )
    # fmt: on
    def __init__(
        self,
        type_map: Mapping[
            parse_tree.Node, intermediate_type_inference.TypeAnnotationUnion
        ],
        environment: intermediate_type_inference.Environment,
        symbol_table: intermediate.SymbolTable,
        verification: Union[
            intermediate.TranspilableVerification,
            intermediate.PatternVerification,
        ],
    ) -> None:
        """Initialize with the given values."""
        htmlgen.transpilation._Transpiler.__init__(
            self, type_map=type_map, environment=environment
        )

        self._symbol_table = symbol_table

        self._argument_name_set = frozenset(arg.name for arg in verification.arguments)

    def transform_name(
        self, node: parse_tree.Name
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        if node.identifier in self._variable_name_set:
            name = htmlgen.naming.variable_name(node.identifier)
            return Stripped(f"<span class='nv'>{name}</span>"), None

        if node.identifier in self._argument_name_set:
            name = htmlgen.naming.argument_name(node.identifier)
            return Stripped(f"<span class='nv'>{name}</span>"), None

        if node.identifier in self._symbol_table.constants_by_name:
            name = htmlgen.naming.constant_name(node.identifier)
            return Stripped(f"<span class='no'>{name}</span>"), None

        if node.identifier in self._symbol_table.verification_functions_by_name:
            name = htmlgen.naming.function_name(node.identifier)
            return Stripped(f"<span class='nf'>{name}</span>"), None

        our_type = self._symbol_table.find_our_type(name=node.identifier)
        if isinstance(our_type, intermediate.Enumeration):
            name = htmlgen.naming.enum_name(node.identifier)
            return (
                Stripped(f"<span class='nc'><a href='{name}.html'>{name}</a></span>"),
                None,
            )

        return None, Error(
            node.original_node,
            f"We can not determine how to transpile the name {node.identifier!r} "
            f"to HTML. We could not find it neither in the constants, nor in "
            f"verification functions, nor as an enumeration. "
            f"If you expect this name to be transpilable, please contact "
            f"the developers.",
        )


def transpile_body_of_verification(
    verification: Union[
        intermediate.TranspilableVerification,
        intermediate.PatternVerification,
        intermediate.ImplementationSpecificVerification,
    ],
    symbol_table: intermediate.SymbolTable,
    environment: intermediate_type_inference.Environment,
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Transpile a verification function to HTML."""
    parsed_body = None  # type: Optional[Sequence[parse_tree.Node]]

    if isinstance(
        verification,
        (intermediate.TranspilableVerification, intermediate.PatternVerification),
    ):
        parsed_body = verification.parsed.body
    elif isinstance(verification, intermediate.ImplementationSpecificVerification):
        # NOTE (mristin, 2023-10-20):
        # We can not parse the implementation specific verification, so we simply
        # return a comment.
        return (
            Stripped(
                "<div><em>Code not available as this is implementation-specific.</em></div>"
            ),
            None,
        )

    else:
        assert_never(verification)

    assert parsed_body is not None
    assert not isinstance(verification, intermediate.ImplementationSpecificVerification)

    canonicalizer = intermediate_type_inference.Canonicalizer()
    for node in parsed_body:
        _ = canonicalizer.transform(node)

    environment_with_args = intermediate_type_inference.MutableEnvironment(
        parent=environment
    )
    for arg in verification.arguments:
        environment_with_args.set(
            identifier=arg.name,
            type_annotation=intermediate_type_inference.convert_type_annotation(
                arg.type_annotation
            ),
        )

    type_inferrer = intermediate_type_inference.Inferrer(
        symbol_table=symbol_table,
        environment=environment_with_args,
        representation_map=canonicalizer.representation_map,
    )

    for node in verification.parsed.body:
        _ = type_inferrer.transform(node)

    if len(type_inferrer.errors):
        return None, Error(
            verification.parsed.node,
            f"Failed to infer the types "
            f"in the verification function {verification.name!r}",
            type_inferrer.errors,
        )

    transpiler = _TranspilableVerificationTranspiler(
        type_map=type_inferrer.type_map,
        environment=environment_with_args,
        symbol_table=symbol_table,
        verification=verification,
    )

    body = []  # type: List[Stripped]
    for node in verification.parsed.body:
        stmt, error = transpiler.transform(node)
        if error is not None:
            return None, Error(
                verification.parsed.node,
                f"Failed to transpile the verification function {verification.name!r}",
                [error],
            )

        assert stmt is not None
        body.append(stmt)

    if len(body) == 0:
        return Stripped("<span class='c'># No implementation specified</span>"), None

    code = Stripped("\n".join(body))
    return Stripped(_enclose_in_highlight_div_pre(code)), None


class _InvariantTranspiler(_Transpiler):
    def __init__(
        self,
        type_map: Mapping[
            parse_tree.Node, intermediate_type_inference.TypeAnnotationUnion
        ],
        environment: intermediate_type_inference.Environment,
        symbol_table: intermediate.SymbolTable,
    ) -> None:
        """Initialize with the given values."""
        htmlgen.transpilation._Transpiler.__init__(
            self, type_map=type_map, environment=environment
        )

        self._symbol_table = symbol_table

    def transform_name(
        self, node: parse_tree.Name
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        if node.identifier in self._variable_name_set:
            name = htmlgen.naming.variable_name(node.identifier)
            return Stripped(f"<span class='nv'>{name}</span>"), None

        if node.identifier == "self":
            return Stripped("<span class='bp'>self</span>"), None

        if node.identifier in self._symbol_table.constants_by_name:
            name = htmlgen.naming.constant_name(node.identifier)
            return (
                Stripped(f"<span class='no'><a href='{name}.html'>{name}</a></span>"),
                None,
            )

        if node.identifier in self._symbol_table.verification_functions_by_name:
            name = htmlgen.naming.function_name(node.identifier)
            return (
                Stripped(f"<span class='nf'><a href='{name}.html'>{name}</a></span>"),
                None,
            )

        our_type = self._symbol_table.find_our_type(name=node.identifier)
        if isinstance(our_type, intermediate.Enumeration):
            name = htmlgen.naming.enum_name(node.identifier)
            return (
                Stripped(f"<span class='nc'><a href='{name}.html'>{name}</a></span>"),
                None,
            )

        return None, Error(
            node.original_node,
            f"We can not determine how to transpile the name {node.identifier!r} "
            f"to HTML. We could not find it neither in the local variables, "
            f"nor in the global constants, nor in verification functions, "
            f"nor as an enumeration. If you expect this name to be transpilable, "
            f"please contact the developers.",
        )


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def transpile_invariant(
    invariant: intermediate.Invariant,
    symbol_table: intermediate.SymbolTable,
    environment: intermediate_type_inference.Environment,
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Translate the invariant from the meta-model into HTML."""
    canonicalizer = intermediate_type_inference.Canonicalizer()
    _ = canonicalizer.transform(invariant.body)

    type_inferrer = intermediate_type_inference.Inferrer(
        symbol_table=symbol_table,
        environment=environment,
        representation_map=canonicalizer.representation_map,
    )

    _ = type_inferrer.transform(invariant.body)

    if len(type_inferrer.errors):
        return None, Error(
            invariant.parsed.node,
            "Failed to infer the types in the invariant",
            type_inferrer.errors,
        )

    transpiler = _InvariantTranspiler(
        type_map=type_inferrer.type_map,
        environment=environment,
        symbol_table=symbol_table,
    )

    expr, error = transpiler.transform(invariant.parsed.body)
    if error is not None:
        return None, error

    assert expr is not None

    return _enclose_in_highlight_div_pre(expr), None
