"""Generate HTML for a given meta-model."""
import ast
import collections
import html
import itertools
import pathlib
import re
import textwrap
from typing import (
    Tuple,
    List,
    Union,
    Literal,
    Mapping,
    MutableMapping,
    Iterator,
    Optional,
)

import asttokens
import pygments
import pygments.formatters
import pygments.lexers
from aas_core_codegen import intermediate
from aas_core_codegen.common import (
    Stripped,
    indent_but_first_line,
    assert_never,
    Error,
    Identifier,
)
from icontract import require, ensure

import htmlgen.description
from htmlgen.common import I, II, III


def _over_descriptions_and_page_paths(
    symbol_table: intermediate.SymbolTable,
) -> Iterator[Tuple[intermediate.DescriptionUnion, str]]:
    """Iterate over the descriptions along the page paths."""
    for our_type in symbol_table.our_types:
        page_path = f"{our_type.name}.html"

        if our_type.description is not None:
            yield our_type.description, page_path

        if isinstance(our_type, intermediate.Enumeration):
            for literal in our_type.literals:
                if literal.description is not None:
                    yield literal.description, page_path

        elif isinstance(our_type, intermediate.ConstrainedPrimitive):
            # No special sub-descriptions in the constrained primitive
            pass

        elif isinstance(
            our_type, (intermediate.AbstractClass, intermediate.ConcreteClass)
        ):
            for prop in our_type.properties:
                if prop.description is not None:
                    yield prop.description, page_path

            for method in our_type.methods:
                if method.description is not None:
                    yield method.description, page_path
        else:
            assert_never(our_type)

    for constant in symbol_table.constants:
        page_path = f"{constant.name}.html"
        if constant.description is not None:
            yield constant.description, page_path

    for verification in symbol_table.verification_functions:
        page_path = f"{verification.name}.html"
        if verification.description is not None:
            yield verification.description, page_path

    if symbol_table.meta_model.description is not None:
        yield symbol_table.meta_model.description, "index.html"


def _collect_constraint_href_map(
    symbol_table: intermediate.SymbolTable,
) -> MutableMapping[str, str]:
    """Collect the references to constraint as ``constraint ID -> HREF``."""
    mapping = dict()  # type: MutableMapping[str, str]

    for description, page_path in _over_descriptions_and_page_paths(symbol_table):
        if isinstance(description, intermediate.SummaryRemarksConstraintsDescription):
            for identifier in description.constraints_by_identifier:
                mapping[identifier] = f"{page_path}#constraint-{identifier}"

    return mapping


def _generate_nav(
    symbol_table: intermediate.SymbolTable,
    active_item: Union[
        intermediate.OurType,
        intermediate.ConstantUnion,
        intermediate.Verification,
        Literal["Home"],
    ],
    constraint_href_map: Mapping[str, str],
) -> Stripped:
    """Generate the navigation unordered list."""
    lis = [
        f"""\
<li class="nav-item mb-2">
{I}<a class="nav-item" href="../index.html">Back</a>
</li>"""
    ]  # type: List[str]

    a_class = "nav-item active" if active_item == "Home" else "nav-item"

    lis.append(
        f"""\
<li class="nav-item  mb-2">
{I}<a class="{a_class}" href="index.html">{symbol_table.meta_model.version}</a>
</li>"""
    )

    # region Enumerations

    lis.append('<li class="nav-item mt-2">Enumerations</li>')

    enumerations = sorted(
        [
            our_type
            for our_type in symbol_table.our_types
            if isinstance(our_type, intermediate.Enumeration)
        ],
        key=lambda our_type: our_type.name,
    )
    for enumeration in enumerations:
        a_class = "nav-item active" if active_item is enumeration else "nav-item"

        lis.append(
            f"""\
<li class="nav-item">
{I}<a class="{a_class}" href="{enumeration.name}.html">
{II}{enumeration.name}
{I}</a>
</li>"""
        )

    # endregion

    # region Constrained primitives

    lis.append('<li class="nav-item mt-2">Constrained Primitives</li>')

    constrained_primitives = sorted(
        [
            our_type
            for our_type in symbol_table.our_types
            if isinstance(our_type, intermediate.ConstrainedPrimitive)
        ],
        key=lambda our_type: our_type.name,
    )
    for constrained_primitive in constrained_primitives:
        a_class = (
            "nav-item active" if active_item is constrained_primitive else "nav-item"
        )

        lis.append(
            f"""\
<li class="nav-item">
{I}<a class="{a_class}" href="{constrained_primitive.name}.html">
{II}{constrained_primitive.name}
{I}</a>
</li>"""
        )

    # endregion

    # region Abstract classes

    lis.append('<li class="nav-item mt-2">Abstract Classes</li>')

    abstract_classes = sorted(
        [
            our_type
            for our_type in symbol_table.our_types
            if isinstance(our_type, intermediate.AbstractClass)
        ],
        key=lambda our_type: our_type.name,
    )
    for abstract_class in abstract_classes:
        a_class = "nav-item active" if active_item is abstract_class else "nav-item"

        lis.append(
            f"""\
<li class="nav-item">
{I}<a class="{a_class}" href="{abstract_class.name}.html">
{II}{abstract_class.name}
{I}</a>
</li>"""
        )

    # endregion

    # region Concrete classes

    lis.append('<li class="nav-item mt-2">Concrete Classes</li>')

    concrete_classes = sorted(
        [
            our_type
            for our_type in symbol_table.our_types
            if isinstance(our_type, intermediate.ConcreteClass)
        ],
        key=lambda our_type: our_type.name,
    )
    for concrete_class in concrete_classes:
        a_class = "nav-item active" if active_item is concrete_class else "nav-item"

        lis.append(
            f"""\
<li class="nav-item">
{I}<a class="{a_class}" href="{concrete_class.name}.html">
{II}{concrete_class.name}
{I}</a>
</li>"""
        )

    # endregion

    # region Constants

    lis.append('<li class="nav-item mt-2">Constants</li>')

    constants = sorted(
        list(symbol_table.constants),
        key=lambda a_constant: a_constant.name,
    )
    for constant in constants:
        a_class = "nav-item active" if active_item is constant else "nav-item"

        lis.append(
            f"""\
<li class="nav-item">
{I}<a class="{a_class}" href="{constant.name}.html">
{II}{constant.name}
{I}</a>
</li>"""
        )

    # endregion

    # region Constraints

    lis.append('<li class="nav-item">Constraints</li>')

    constraints_hrefs = sorted(
        (constraint, href) for constraint, href in constraint_href_map.items()
    )

    for constraint, href in constraints_hrefs:
        # NOTE (mristin, 2023-01-13):
        # We do not set active/inactive on constraints as they point to multiple
        # anchors within a single page.
        lis.append(
            f"""\
<li class="nav-item">
{I}<a class="nav-item" href="{href}">
{II}{constraint}
{I}</a>
</li>"""
        )

    # endregion

    # region Verification functions

    lis.append('<li class="nav-item mt-2">Verification Functions</li>')

    verification_functions = sorted(
        list(symbol_table.verification_functions),
        key=lambda a_verification_function: a_verification_function.name,
    )
    for verification_function in verification_functions:
        a_class = (
            "nav-item active" if active_item is verification_function else "nav-item"
        )

        lis.append(
            f"""\
<li class="nav-item">
{I}<a class="{a_class}" href="{verification_function.name}.html">
{II}{verification_function.name}
{I}</a>
</li>"""
        )

    # endregion

    lis_joined = "\n".join(lis)
    return Stripped(
        f"""\
<ul class="nav flex-column mb-sm-auto mb-0 align-items-center align-items-sm-start" id="menu-ul">
{I}{indent_but_first_line(lis_joined, I)}
</ul>"""
    )


STRIPPED_CODE_RE = re.compile(r"\[\[!DEDENT(.*?)DEDENT!]]", flags=re.DOTALL)


# fmt: off
@ensure(
    lambda result:
    not result.startswith('\n')
    and not result.startswith(' ')
    and not result.startswith('\t'),
    "No prefix whitespace"
)
@ensure(lambda result: result.endswith('\n'), "Trailing new line is mandatory")
# fmt: off
def _generate_page(
        title: Stripped,
        nav: Stripped,
        content: Stripped
) -> str:
    """Generate a HTML page."""
    # noinspection SpellCheckingInspection
    page = f"""\
<html>
<head>
{I}<meta charset="UTF-8">
{I}<meta name="viewport" content="width=device-width, initial-scale=1">
{I}<title>{html.escape(title)}</title>
{I}<link rel="stylesheet" href="../base.css">
{I}<link
{II}href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css"
{II}rel="stylesheet"
{II}integrity="sha384-EVSTQN3/azprG1Anm3QDgpJLIm9Nao0Yz1ztcQTwFspd3yD65VohhpuuCOmLASjC"
{II}crossorigin="anonymous"
{I}>
</head>
<body>
<div class="container-fluid px-0 mx-0">
{I}<div class="row px-0 mx-0" style="width: 100%;">
{II}<div class="col-3 px-2 mx-0 overflow-auto" id="menu">
{III}{indent_but_first_line(nav, III)}
{II}</div>
{II}<div class="col-9 mx-0 overflow-auto" id="content">
{III}{indent_but_first_line(content, III)}
{II}</div>
{I}</div>
</div>
<footer class="text-center p-1 text-lg-start bg-light text-muted" id="footer">
{I}Automatically generated with htmlgen as part of <a href="https://github.com/aas-core-works/aas-core-meta">aas-core-works/aas-core-meta</a>.
</footer>
<script src="../atTheEndOfBody.js"></script>
</body>
</html>
"""

    # NOTE (mristin, 2023-01-18):
    # We have to de-dent source code so that the formatting in ``<pre>`` remains
    # preserved.
    parts = []  # type: List[str]

    last_end = 0
    for match in STRIPPED_CODE_RE.finditer(page):
        parts.append(page[last_end:match.start()])
        last_end = match.end()

        original = match.group(1).rstrip()

        # NOTE (mristin, 2023-01-18):
        # We remove the leading new-line after the dedent directive as it messes up
        # the dedent.
        if original.startswith('\n'):
            original = original[1:]

        dedented = textwrap.dedent(original)

        parts.append(dedented)

    parts.append(page[last_end:])

    return "".join(parts)


def no_prefix_whitespace_and_trailing_newline(text: str) -> bool:
    """Check that the content conforms to expectations of a POSIX text file."""
    return (
            not text.startswith('\n')
            and not text.startswith(' ')
            and not text.startswith('\t')
            and text.endswith('\n')
    )


# fmt: off
@ensure(
    lambda result:
    not (result[0] is not None)
    or no_prefix_whitespace_and_trailing_newline(result[0])
)
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
# fmt: off
def _generate_page_for_enumeration(
        enumeration: intermediate.Enumeration,
        symbol_table: intermediate.SymbolTable,
        constraint_href_map: Mapping[str, str]
) -> Tuple[Optional[str], Optional[Error]]:
    blocks = [
        Stripped(
            f"""\
<h1>
{I}{enumeration.name}
{I}<a class="aas-anchor-link" href="">🔗</a>
</h1>"""
        )
    ]  # type: List[Stripped]

    description = Stripped("")  # type: Optional[Stripped]

    if enumeration.description is not None:
        description, errors = htmlgen.description.generate_for_our_type(
            description=enumeration.description,
            constraint_href_map=constraint_href_map
        )
        if errors is not None:
            return None, Error(
                enumeration.parsed.node,
                f"Failed to render the description "
                f"of the enumeration {enumeration.name}",
                errors
            )

        assert description is not None
        blocks.append(
            Stripped(
                f"""\
<div class="aas-description">
{I}{indent_but_first_line(description, I)}
</div>"""
            )
        )

    literal_elements = []  # type: List[str]
    for literal in enumeration.literals:
        literal_description = ""  # type: Optional[str]

        if literal.description is not None:
            # fmt: off
            literal_description, errors = (
                htmlgen.description.generate_for_enumeration_literal(
                    description=literal.description,
                    constraint_href_map=constraint_href_map
                )
            )
            # fmt: on

            if errors is not None:
                return None, Error(
                    enumeration.parsed.node,
                    f"Failed to render the description of the literal {literal.name}",
                    errors
                )

        assert literal_description is not None

        literal_elements.append(
            f"""\
<dt>
{I}<a name="literal-{literal.name}" />
{I}{html.escape(literal.name)}
{I}<a class="aas-anchor-link" href="#literal-{literal.name}">🔗</a>
{I} = <code>{html.escape(repr(literal.value))}</code>
</dt>
<dd>
{I}{indent_but_first_line(literal_description, I)}
</dd>"""
        )

    literal_elements_joined = "\n".join(literal_elements)

    blocks.append(
        Stripped(
            f"""\
<h2>Literals</h2>
<div>
{I}<dl>
{I}{indent_but_first_line(literal_elements_joined, I)}
{I}</dl>
</div>"""
        )
    )

    usage_block = _generate_usages_block(
        our_type=enumeration, symbol_table=symbol_table
    )
    if usage_block is not None:
        blocks.append(usage_block)

    content = Stripped("\n".join(blocks))

    nav = _generate_nav(
        symbol_table=symbol_table,
        active_item=enumeration,
        constraint_href_map=constraint_href_map
    )

    return (
        _generate_page(title=Stripped(enumeration.name), nav=nav, content=content),
        None
    )


NAME_MEMBER_SPAN_RE = re.compile(
    r'<span class="n">([a-zA-Z0-9_]+)</span>'
    r'<span class="o">\.</span>'
    r'<span class="n">([a-zA-Z0-9_]+)</span>'
)
NAME_SPAN_RE = re.compile(r'<span class="n">([a-zA-Z0-9_]+)</span>')


def _code_as_div(
        code: str,
        symbol_table: intermediate.SymbolTable
) -> Stripped:
    """Format the code and link names to verification functions and constants."""
    code_div = pygments.highlight(
        code,
        pygments.lexers.PythonLexer(),
        pygments.formatters.HtmlFormatter()
    ).strip()

    # NOTE (mristin, 2023-01-18):
    # We now hard-wire names to matching literals, functions and constants. This is
    # super fragile and will break with changes in pygments! For now, it works.
    #
    # See this pygments issue in case you ever want to implement this in a robust way:
    # https://github.com/pygments/pygments/issues/1091

    # region Link literals

    parts = []  # type: List[str]
    last_end = 0

    for match in NAME_MEMBER_SPAN_RE.finditer(code_div):
        parts.append(code_div[last_end:match.start()])
        last_end = match.end()

        name = match.group(1)
        member = match.group(2)

        our_type = symbol_table.find_our_type(Identifier(name))

        literal = None  # type: Optional[intermediate.EnumerationLiteral]
        if isinstance(our_type, intermediate.Enumeration):
            literal = our_type.literals_by_name.get(member, None)

        if literal is not None:
            parts.append(
                f'<a href="{name}.html#literal-{member}">{match.group()}</a>'
            )
        else:
            parts.append(match.group())

    parts.append(code_div[last_end:])

    code_div = "".join(parts)

    # endregion

    # region Link constants and verification functions

    parts = []
    last_end = 0

    for match in NAME_SPAN_RE.finditer(code_div):
        parts.append(code_div[last_end:match.start()])
        last_end = match.end()

        name = match.group(1)
        if (
                name in symbol_table.verification_functions_by_name
                or name in symbol_table.constants_by_name
        ):
            parts.append(
                f'<span class="n"><a href="{name}.html">{name}</a></span>'
            )
        else:
            parts.append(match.group())

    parts.append(code_div[last_end:])

    code_div = "".join(parts)

    # endregion

    return Stripped(code_div)


@require(lambda invariant, our_type: id(invariant) in our_type.invariant_id_set)
def _invariant_as_li(
        invariant: intermediate.Invariant,
        atok: asttokens.ASTTokens,
        our_type: intermediate.OurType,
        symbol_table: intermediate.SymbolTable
) -> Stripped:
    """Render an invariant as an ``<li>`` element."""
    parts = []  # type: List[Stripped]

    if invariant.description is not None:
        parts.append(
            Stripped(html.escape(invariant.description.strip()))
        )

    if invariant.specified_for is not our_type:
        parts.append(
            Stripped(
                f'<em>(From <a href="{invariant.specified_for.name}.html">'
                f'{invariant.specified_for.name}</a>)</em>'
            )
        )

    invariant_start, invariant_end = atok.get_text_range(
        invariant.parsed.body.original_node
    )

    # NOTE (mristin, 2023-01-18):
    # We include the preceding whitespace to facilitate dedent.
    while invariant_start > 0 and atok._text[invariant_start - 1] in (' ', '\t'):
        invariant_start -= 1

    code = textwrap.dedent(atok._text[invariant_start:invariant_end])

    code_div = _code_as_div(code=code, symbol_table=symbol_table)

    parts.append(
        Stripped(
            f"""\
[[!DEDENT
{code_div}
DEDENT!]]"""
        )
    )

    parts_joined_and_indented = "<br/>\n".join(
        I + indent_but_first_line(part, I)
        for part in parts
    )

    return Stripped(
        f"""\
<li>
{parts_joined_and_indented}
</li>"""
    )


# fmt: off
@ensure(
    lambda result:
    not (result[0] is not None)
    or no_prefix_whitespace_and_trailing_newline(result[0])
)
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
# fmt: off
def _generate_page_for_constrained_primitive(
        constrained_primitive: intermediate.ConstrainedPrimitive,
        symbol_table: intermediate.SymbolTable,
        constraint_href_map: Mapping[str, str],
        atok: asttokens.ASTTokens
) -> Tuple[Optional[str], Optional[Error]]:
    primitive_type_snippet = Stripped(
        f"""\
<dl>
<dt>
{I}<a name="primitive-type"></a>
{I}Primitive type: <code>{constrained_primitive.constrainee.value}</code>
{I}<a class="aas-anchor-link" href="#primitive-type">🔗</a>
</dt>
<dd></dd>
</dl>"""
    )

    blocks = [
Stripped(
    f"""\
<h1>
{I}{html.escape(constrained_primitive.name)}
{I}<a class="aas-anchor-link" href="">🔗</a>
</h1>
{primitive_type_snippet}"""
)
    ]

    if constrained_primitive.description is not None:
        description, errors = htmlgen.description.generate_for_our_type(
            description=constrained_primitive.description,
            constraint_href_map=constraint_href_map
        )
        if errors is not None:
            return None, Error(
                constrained_primitive.parsed.node,
                f"Failed to render the description "
                f"of the constrained primitive {constrained_primitive.name}",
                errors
            )

        assert description is not None
        blocks.append(
            Stripped(
                f"""\
<div class="aas-description">
{I}{indent_but_first_line(description, I)}
</div>"""
            )
        )

    if len(constrained_primitive.inheritances) > 0:
        li_inheritances = [
            f"""\
<li>
{I}<a href="{inheritance.name}.html">{inheritance.name}</a>
</li>"""
            for inheritance in constrained_primitive.inheritances
        ]

        li_inheritances_joined = "\n".join(li_inheritances)
        ul_inheritances = Stripped(
            f"""\
<ul>
{I}{indent_but_first_line(li_inheritances_joined, I)}
</ul>"""
        )

        blocks.append(
            Stripped(
                f"""\
<h2>
{I}<a name="inheritances"></a>
{I}Inheritances
{I}<a class="aas-anchor-link" href="#inheritances">🔗</a>
</h2>
{ul_inheritances}"""
            )
        )

    if len(constrained_primitive.invariants) > 0:
        li_invariants = [
            _invariant_as_li(
                invariant=invariant,
                atok=atok,
                our_type=constrained_primitive,
                symbol_table=symbol_table
            )
            for invariant in constrained_primitive.invariants
        ]

        li_invariants_joined = "\n".join(li_invariants)

        ul_invariants = Stripped(
            f"""\
<h2>
{I}<a name="invariants"></a>
{I}Invariants
{I}<a class="aas-anchor-link" href="#invariants">🔗</a>
</h2>
<ul>
{I}{indent_but_first_line(li_invariants_joined, I)}
</ul>"""
        )

        blocks.append(ul_invariants)

    usage_block = _generate_usages_block(
        our_type=constrained_primitive, symbol_table=symbol_table
    )
    if usage_block is not None:
        blocks.append(usage_block)

    content = Stripped("\n".join(blocks))

    nav = _generate_nav(
        symbol_table=symbol_table,
        active_item=constrained_primitive,
        constraint_href_map=constraint_href_map
    )

    return (
        _generate_page(
            title=Stripped(constrained_primitive.name),
            nav=nav,
            content=content
        ),
        None
    )


@require(lambda prop, cls: id(prop) in cls.property_id_set)
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _property_as_dt_dd(
        prop: intermediate.Property,
        cls: intermediate.ClassUnion,
        constraint_href_map: Mapping[str, str]
)->Tuple[Optional[Stripped], Optional[Error]]:
    """Render the property as ``<dt>...</dt><dd>...</dd>``."""
    dd_divs = []  # type: List[str]

    if prop.specified_for is not cls:
        dd_divs.append(
            f"""\
<div>
{I}<em>(From <a href="{prop.specified_for.name}.html">{prop.specified_for.name}</a>)</em>
</div>"""
        )

    if prop.description is not None:
        description, errors = htmlgen.description.generate_for_property(
            description=prop.description,
            constraint_href_map=constraint_href_map
        )
        if errors is not None:
            return None, Error(
                prop.parsed.node,
                f"Failed to render the description "
                f"of the property {prop.name} from the class {cls.name}",
                errors
            )

        assert description is not None
        dd_divs.append(
            f"""\
<div>
{I}{indent_but_first_line(description, I)}
</div>"""
        )

    if len(dd_divs) > 0:
        dd_divs_joined = "\n".join(dd_divs)
        dd_element = f"""\
<dd>
{I}{indent_but_first_line(dd_divs_joined, I)}
</dd>"""
    else:
        dd_element = "<dd></dd>"

    span_type_anno = _type_annotation_as_span(prop.type_annotation)
    dt_element = f"""\
<dt>
{I}<a name="#property-{prop.name}"></a>
{I}{prop.name}: {span_type_anno}
{I}<a class="aas-anchor-link" href="#property-{prop.name}">🔗</a>
</dt>
"""

    return Stripped(
        f"""\
{dt_element}
{dd_element}"""
    ), None


def  _render_type_annotation_recursively(
        type_annotation: intermediate.TypeAnnotationUnion
)->Stripped:
    """Render the type annotation as HTML, without enclosing ``<span>``."""
    if isinstance(type_annotation, intermediate.PrimitiveTypeAnnotation):
        return Stripped(type_annotation.a_type.value)
    elif isinstance(type_annotation, intermediate.OurTypeAnnotation):
        name = type_annotation.our_type.name
        return Stripped(f'<a href="{name}.html">{name}</a>')
    elif isinstance(type_annotation, intermediate.ListTypeAnnotation):
        items_type_anno = _render_type_annotation_recursively(type_annotation.items)
        return Stripped(f"List[{items_type_anno}]")
    elif isinstance(type_annotation, intermediate.OptionalTypeAnnotation):
        value_type_anno = _render_type_annotation_recursively(type_annotation.value)
        return Stripped(f"Optional[{value_type_anno}]")
    else:
        assert_never(type_annotation)


def _type_annotation_as_span(
        type_annotation: intermediate.TypeAnnotationUnion
)->Stripped:
    """Render the type annotation as a ``<span>``."""
    content = _render_type_annotation_recursively(type_annotation)
    return Stripped(f'<span class="aas-type-annotation">{content}</span>')


def _our_type_appears_in_type_annotation(
        our_type: intermediate.OurType,
        type_annotation: intermediate.TypeAnnotationUnion
)->bool:
    """Check if the ``cls`` appears in the type annotation."""
    if isinstance(type_annotation, intermediate.PrimitiveTypeAnnotation):
        return False
    elif isinstance(type_annotation, intermediate.OurTypeAnnotation):
        return our_type is type_annotation.our_type
    elif isinstance(type_annotation, intermediate.ListTypeAnnotation):
        return _our_type_appears_in_type_annotation(our_type, type_annotation.items)
    elif isinstance(type_annotation, intermediate.OptionalTypeAnnotation):
        return _our_type_appears_in_type_annotation(our_type, type_annotation.value)
    else:
        assert_never(type_annotation)


def _generate_usages_block(
        our_type: intermediate.OurType,
        symbol_table: intermediate.SymbolTable
) -> Optional[Stripped]:
    """Generate the block where we infer the usages of our type."""
    usages = collections.OrderedDict(
    )  # type: MutableMapping[intermediate.ClassUnion, List[intermediate.Property]]

    for other_type in symbol_table.our_types:
        if not isinstance(
                other_type, (intermediate.AbstractClass, intermediate.ConcreteClass)
        ):
            continue

        if our_type is other_type:
            continue

        for prop in other_type.properties:
            if _our_type_appears_in_type_annotation(our_type, prop.type_annotation):
                if other_type not in usages:
                    usages[other_type] = [prop]
                else:
                    usages[other_type].append(prop)

    if len(usages) == 0:
        return None

    tr_usages = []  # type: List[str]
    for other_type, props in usages.items():
        a_props = [
            (
                f'<a href="{other_type.name}.html#property-{prop.name}">'
                f'{other_type.name}.{prop.name}</a>'
            )
            for prop in props
        ]
        a_props_joined = ",\n".join(a_props)
        tr_usages.append(
            f"""\
<tr>
{I}<td>
{II}<a href="{other_type.name}.html">{other_type.name}</a>
{I}</td>
{I}<td>
{II}{indent_but_first_line(a_props_joined, II)}
{I}</td>
</tr>"""
        )

    tr_usages_joined = "\n".join(tr_usages)
    table_usages = f"""\
<table class="table">
{I}{indent_but_first_line(tr_usages_joined, I)}
</table>"""

    return Stripped(
            f"""\
<h2>Usages</h2>
{table_usages}"""
        )


# fmt: off
@ensure(
    lambda result:
    not (result[0] is not None)
    or no_prefix_whitespace_and_trailing_newline(result[0])
)
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
# fmt: off
def _generate_page_for_class(
        cls: intermediate.ClassUnion,
        symbol_table: intermediate.SymbolTable,
        constraint_href_map: Mapping[str, str],
        atok: asttokens.ASTTokens
) -> Tuple[Optional[str], Optional[Error]]:
    blocks = []  # type: List[Stripped]

    if isinstance(cls, intermediate.AbstractClass):
        blocks.append(
            Stripped(
                f"""\
<h1>
{I}{cls.name}<a class="aas-anchor-link" href="">🔗</a><br/>
{I}<em>(abstract)</em>
</h1>"""
            )
        )
    elif isinstance(cls, intermediate.ConcreteClass):
        blocks.append(
            Stripped(
                f"""\
<h1>
{I}{cls.name}<a class="aas-anchor-link" href="">🔗</a>
</h1>"""
            )
        )
    else:
        assert_never(cls)

    if cls.description is not None:
        description, errors = htmlgen.description.generate_for_our_type(
            description=cls.description,
            constraint_href_map=constraint_href_map
        )
        if errors is not None:
            return None, Error(
                cls.parsed.node,
                f"Failed to render the description "
                f"of the class {cls.name}",
                errors
            )

        assert description is not None
        blocks.append(
            Stripped(
                f"""\
<div class="aas-description">
{I}{indent_but_first_line(description, I)}
</div>"""
            )
        )

    if len(cls.inheritances) > 0:
        li_inheritances = [
            f"""\
<li>
{I}<a href="{inheritance.name}.html">{inheritance.name}</a>
</li>"""
            for inheritance in cls.inheritances
        ]

        li_inheritances_joined = "\n".join(li_inheritances)
        ul_inheritances = Stripped(
            f"""\
<ul>
{I}{indent_but_first_line(li_inheritances_joined, I)}
</ul>"""
        )

        blocks.append(
            Stripped(
                f"""\
<h2>
{I}<a name="inheritances"></a>
{I}Inheritances
{I}<a class="aas-anchor-link" href="#inheritances">🔗</a>
</h2>
{ul_inheritances}"""
            )
        )

    if len(cls.descendants) > 0:
        li_descendants = [
            f"""\
<li>
{I}<a href="{descendant.name}.html">{descendant.name}</a>
</li>"""
            for descendant in cls.descendants
        ]

        li_descendants_joined = "\n".join(li_descendants)
        ul_descendants = Stripped(
            f"""\
<ul>
{I}{indent_but_first_line(li_descendants_joined, I)}
</ul>"""
        )

        blocks.append(
            Stripped(
                f"""\
<h2>
{I}<a name="concrete-descendants"></a>
{I}Descendants
{I}<a class="aas-anchor-link" href="#concrete-descendants">🔗</a>
</h2>
{ul_descendants}"""
            )
        )

    if len(cls.properties) > 0:
        blocks.append(
            Stripped(
                f"""\
<h2>
{I}<a name="properties"></a>
{I}Properties
{I}<a class="aas-anchor-link" href="#properties">🔗</a>
</h2>"""
            )
        )

        dt_dd_properties = []  # type: List[Stripped]
        for prop in cls.properties:
            dt_dd_property, error = _property_as_dt_dd(
                prop=prop,
                cls=cls,
                constraint_href_map=constraint_href_map
            )
            if error is not None:
                return None, error

            assert dt_dd_property is not None
            dt_dd_properties.append(dt_dd_property)

        dt_dd_properties_joined = "\n".join(dt_dd_properties)
        blocks.append(
            Stripped(
                f"""\
<dl>
{I}{indent_but_first_line(dt_dd_properties_joined, I)}
</dl>"""
            )
        )

    if len(cls.invariants) > 0:
        li_invariants = [
            _invariant_as_li(
                invariant=invariant,
                atok=atok,
                our_type=cls,
                symbol_table=symbol_table
            )
            for invariant in cls.invariants
        ]

        li_invariants_joined = "\n".join(li_invariants)

        ul_invariants = Stripped(
            f"""\
<h2>
{I}<a name="invariants"></a>
{I}Invariants
{I}<a class="aas-anchor-link" href="#invariants">🔗</a>
</h2>
<ul>
{I}{indent_but_first_line(li_invariants_joined, I)}
</ul>"""
        )

        blocks.append(ul_invariants)

    usage_block = _generate_usages_block(our_type=cls, symbol_table=symbol_table)
    if usage_block is not None:
        blocks.append(usage_block)

    content = Stripped("\n".join(blocks))

    nav = _generate_nav(
        symbol_table=symbol_table,
        active_item=cls,
        constraint_href_map=constraint_href_map
    )

    return (
        _generate_page(
            title=Stripped(cls.name),
            nav=nav,
            content=content
        ),
        None
    )


# fmt: off
@ensure(
    lambda result:
    not (result[0] is not None)
    or no_prefix_whitespace_and_trailing_newline(result[0])
)
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
# fmt: off
def _generate_page_for_constant(
        constant: intermediate.ConstantUnion,
        symbol_table: intermediate.SymbolTable,
        constraint_href_map: Mapping[str, str]
) -> Tuple[Optional[str], Optional[Error]]:
    blocks = [
        Stripped(
            f"""\
<h1>
{I}{constant.name}<a class="aas-anchor-link" href="">🔗</a>
</h1>"""
        )
    ]  # type: List[Stripped]

    constant_type = None  # type: Optional[str]
    if isinstance(constant, intermediate.ConstantPrimitive):
        constant_type = constant.a_type.value
    elif isinstance(constant, intermediate.ConstantSetOfPrimitives):
        constant_type = f"Set[{constant.a_type.value}]"
    elif isinstance(constant, intermediate.ConstantSetOfEnumerationLiterals):
        name = constant.enumeration.name
        constant_type = f'<a href="{name}.html">{name}</a>'
    else:
        assert_never(constant)

    assert constant_type is not None

    blocks.append(
        Stripped(
            f"""\
<du>
{I}<dt>Type: <span class="aas-type-annotation">{constant_type}</span></dt>
{I}<dd></dd>
</du>"""
        )
    )

    if constant.description is not None:
        description, errors = htmlgen.description.generate_for_constant(
            description=constant.description,
            constraint_href_map=constraint_href_map
        )
        if errors is not None:
            return None, Error(
                constant.parsed.node,
                f"Failed to render the description "
                f"of the constant {constant.name}",
                errors
            )

        assert description is not None
        blocks.append(
            Stripped(
                f"""\
<div class="aas-description">
{I}{indent_but_first_line(description, I)}
</div>"""
            )
        )

    if isinstance(constant, intermediate.ConstantPrimitive):
        blocks.append(
            Stripped(
                f"""\
<du>
{I}<dt>Value: <code>{html.escape(repr(constant.value))}</code>
{I}<dd></dd>
</du>"""
            )
        )
    elif isinstance(constant, intermediate.ConstantSetOfPrimitives):
        blocks.append(Stripped("<h2>Values</h2>"))

        li_values = []  # type: List[str]
        for literal_value in constant.literal_value_set:
            li_values.append(
                f"<li><code>{html.escape(repr(literal_value))}</code></li>"
            )

        li_values_joined = "\n".join(li_values)
        ul_values = Stripped(
            f"""\
<ul>
{I}{indent_but_first_line(li_values_joined, I)}
</ul>"""
        )

        blocks.append(ul_values)

    elif isinstance(constant, intermediate.ConstantSetOfEnumerationLiterals):
        blocks.append(Stripped("<h2>Values</h2>"))

        li_values = []
        for literal in constant.literals:
            text = f"{constant.enumeration.name}.{literal.name}"
            href = f"{constant.enumeration.name}.html#literal-{literal.name}"
            li_values.append(
                f'<li><a href="{html.escape(href, quote=True)}">'
                f'{html.escape(text)}</a></li>'
            )

        li_values_joined = "\n".join(li_values)
        ul_values = Stripped(
            f"""\
<ul>
{I}{indent_but_first_line(li_values_joined, I)}
</ul>"""
        )

        blocks.append(ul_values)

    else:
        assert_never(constant)

    content = Stripped("\n".join(blocks))

    nav = _generate_nav(
        symbol_table=symbol_table,
        active_item=constant,
        constraint_href_map=constraint_href_map
    )

    return (
        _generate_page(
            title=Stripped(constant.name),
            nav=nav,
            content=content
        ),
        None
    )

WHITESPACE_RE = re.compile(r'^[ |\t]+')

# fmt: off
@ensure(
    lambda result:
    not (result[0] is not None)
    or no_prefix_whitespace_and_trailing_newline(result[0])
)
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
# fmt: off
def _generate_page_for_verification_function(
        func: Union[
            intermediate.ImplementationSpecificVerification,
            intermediate.PatternVerification,
            intermediate.TranspilableVerification,
        ],
        symbol_table: intermediate.SymbolTable,
        constraint_href_map: Mapping[str, str],
        atok: asttokens.ASTTokens
) -> Tuple[Optional[str], Optional[Error]]:
    blocks = [
        Stripped(
            f"""\
<h1>
{I}{func.name}<a class="aas-anchor-link" href="">🔗</a>
</h1>"""
        )
    ]  # type: List[Stripped]

    func_type = None  # type: Optional[str]
    if isinstance(func, intermediate.ImplementationSpecificVerification):
        func_type = "Implementation specific"
    elif isinstance(func, intermediate.PatternVerification):
        func_type = "Pattern verification"
    elif isinstance(func, intermediate.TranspilableVerification):
        func_type = "Transpilable verification function"
    else:
        assert_never(func)

    assert func_type is not None

    blocks.append(
        Stripped(
            f"""\
<du>
{I}<dt>Type: <span class="aas-type-annotation">{func_type}</span></dt>
{I}<dd></dd>
</du>"""
        )
    )

    if func.description is not None:
        description, errors = htmlgen.description.generate_for_signature(
            signature_name=func.name,
            description=func.description,
            constraint_href_map=constraint_href_map
        )
        if errors is not None:
            return None, Error(
                func.parsed.node,
                f"Failed to render the description "
                f"of the verification function {func.name}",
                errors
            )

        assert description is not None
        blocks.append(
            Stripped(
                f"""\
<div class="aas-description">
{I}{indent_but_first_line(description, I)}
</div>"""
            )
        )

    func_node = func.parsed.node
    assert isinstance(func_node, ast.FunctionDef)

    code = ""
    if len(func_node.body) > 0:
        non_description_node = None  # type: Optional[ast.AST]

        for node in func_node.body:
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
                continue

            non_description_node = node
            break

        last_node = func_node.body[-1]
        if non_description_node is not None:
            start, _ = atok.get_text_range(non_description_node)
            _, end = atok.get_text_range(last_node)

            # NOTE (mristin, 2023-01-18):
            # We include the whitespace *before* the first statement so that we can
            # easily dedent afterwards.
            while start > 0 and atok._text[start-1] in (' ', '\t'):
                start -= 1

            code = textwrap.dedent(atok._text[start:end])

    code_div = _code_as_div(code=code, symbol_table=symbol_table)

    blocks.append(
        Stripped(
            f"""\
<h2>Code</h2>
[[!DEDENT
{code_div.strip()}
DEDENT!]]"""
        )
    )

    content = Stripped("\n".join(blocks))

    nav = _generate_nav(
        symbol_table=symbol_table,
        active_item=func,
        constraint_href_map=constraint_href_map
    )

    return (
        _generate_page(
            title=Stripped(func.name),
            nav=nav,
            content=content
        ),
        None
    )


# fmt: off
@ensure(
    lambda result:
    not (result[0] is not None)
    or (
        not result[0].startswith('\n')
        and not result[0].startswith(' ')
        and not result[0].startswith('\t')
    ),
    "No prefix whitespace"
)
@ensure(
    lambda result:
    not (result[0] is not None)
    or result[0].endswith('\n'),
    "Trailing new line is mandatory"
)
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
# fmt: off
def _generate_home_page(
        symbol_table: intermediate.SymbolTable,
        constraint_href_map: Mapping[str, str]
) -> Tuple[Optional[str], Optional[Error]]:
    description = Stripped("")  # type: Optional[Stripped]

    if symbol_table.meta_model.description is not None:
        description, errors = (
            htmlgen.description.generate_for_meta_model(
                description=symbol_table.meta_model.description,
                constraint_href_map=constraint_href_map
            )
        )
        if errors is not None:
            return None, Error(
                symbol_table.meta_model.description.parsed.node,
                "Failed to render the description of the meta-model",
                errors
            )

        assert description is not None

    content = Stripped(
        f"""\
<h1>
{I}aas-core-meta {html.escape(symbol_table.meta_model.version)}
{I}<a class="aas-anchor-link" href="">🔗</a>
</h1>
<div class="aas-description">
{description}
</div>"""
    )

    nav = _generate_nav(
        symbol_table=symbol_table,
        active_item="Home",
        constraint_href_map=constraint_href_map
    )

    return (
        _generate_page(
            title=Stripped(f"Meta-model {symbol_table.meta_model.version}"),
            nav=nav,
            content=content
        ),
        None
    )


@require(lambda target_dir: target_dir.exists() and target_dir.is_dir())
def generate(
    symbol_table: intermediate.SymbolTable,
    atok: asttokens.ASTTokens,
    target_dir: pathlib.Path,
) -> List[Error]:
    """Generate the pages and save them to the target directory."""
    constraint_href_map = _collect_constraint_href_map(symbol_table)

    errors = []  # type: List[Error]

    home_page, error = _generate_home_page(
        symbol_table=symbol_table, constraint_href_map=constraint_href_map
    )
    if error is not None:
        errors.append(error)
    else:
        assert home_page is not None
        (target_dir / "index.html").write_text(home_page, encoding="utf-8")

    for something in itertools.chain(
        symbol_table.our_types,
        symbol_table.constants,
        symbol_table.verification_functions,
    ):
        page = None  # type: Optional[str]
        if isinstance(something, intermediate.Enumeration):
            page, error = _generate_page_for_enumeration(
                enumeration=something,
                symbol_table=symbol_table,
                constraint_href_map=constraint_href_map,
            )
        elif isinstance(something, intermediate.ConstrainedPrimitive):
            page, error = _generate_page_for_constrained_primitive(
                constrained_primitive=something,
                symbol_table=symbol_table,
                constraint_href_map=constraint_href_map,
                atok=atok,
            )
        elif isinstance(
            something, (intermediate.AbstractClass, intermediate.ConcreteClass)
        ):
            page, error = _generate_page_for_class(
                cls=something,
                symbol_table=symbol_table,
                constraint_href_map=constraint_href_map,
                atok=atok,
            )
        elif isinstance(
            something,
            (
                intermediate.ConstantPrimitive,
                intermediate.ConstantSetOfPrimitives,
                intermediate.ConstantSetOfEnumerationLiterals,
            ),
        ):
            page, error = _generate_page_for_constant(
                constant=something,
                symbol_table=symbol_table,
                constraint_href_map=constraint_href_map,
            )
        elif isinstance(
            something,
            (
                intermediate.ImplementationSpecificVerification,
                intermediate.PatternVerification,
                intermediate.TranspilableVerification,
            ),
        ):
            page, error = _generate_page_for_verification_function(
                func=something,
                symbol_table=symbol_table,
                constraint_href_map=constraint_href_map,
                atok=atok,
            )
        else:
            assert_never(something)

        if error is not None:
            errors.append(error)
        else:
            assert page is not None

            (target_dir / f"{something.name}.html").write_text(
                page, encoding="utf-8"
            )

    return errors
