"""Provide common elements used between the generators."""
from aas_core_codegen import intermediate
from aas_core_codegen.common import Stripped, assert_never

import htmlgen.naming

I = "  "
II = I * 2
III = I * 3
IIII = I * 4


def _render_type_annotation_recursively(
    type_annotation: intermediate.TypeAnnotationUnion,
) -> Stripped:
    """Render the type annotation as HTML, without enclosing ``<span>``."""
    if isinstance(type_annotation, intermediate.PrimitiveTypeAnnotation):
        return Stripped(type_annotation.a_type.value)
    elif isinstance(type_annotation, intermediate.OurTypeAnnotation):
        name = htmlgen.naming.of(type_annotation.our_type)
        return Stripped(f'<a href="{name}.html">{name}</a>')
    elif isinstance(type_annotation, intermediate.ListTypeAnnotation):
        items_type_anno = _render_type_annotation_recursively(type_annotation.items)
        return Stripped(f"List[{items_type_anno}]")
    elif isinstance(type_annotation, intermediate.OptionalTypeAnnotation):
        value_type_anno = _render_type_annotation_recursively(type_annotation.value)
        return Stripped(f"Optional[{value_type_anno}]")
    else:
        assert_never(type_annotation)


def type_annotation_html(type_annotation: intermediate.TypeAnnotationUnion) -> Stripped:
    """Render the type annotation as a ``<span>``."""
    content = _render_type_annotation_recursively(type_annotation)
    return Stripped(f'<span class="aas-type-annotation">{content}</span>')
