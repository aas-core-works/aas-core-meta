"""Generate HTML identifiers based on the identifiers from the meta-model."""

from typing import Union

import aas_core_codegen.naming
from aas_core_codegen import intermediate
from aas_core_codegen.common import Identifier, assert_never


def class_name(identifier: Identifier) -> Identifier:
    """
    Generate an HTML class name based on its meta-model ``identifier``.

    >>> class_name(Identifier("something"))
    'Something'

    >>> class_name(Identifier("URL_to_something"))
    'UrlToSomething'
    """
    return aas_core_codegen.naming.capitalized_camel_case(identifier)


def enum_name(identifier: Identifier) -> Identifier:
    """
    Generate an HTML enum name based on its meta-model ``identifier``.

    >>> enum_name(Identifier("something"))
    'Something'

    >>> enum_name(Identifier("URL_to_something"))
    'UrlToSomething'
    """
    return aas_core_codegen.naming.capitalized_camel_case(identifier)


def enum_literal_name(identifier: Identifier) -> Identifier:
    """
    Generate an HTML name for an enum literal based on its meta-model ``identifier``.

    >>> enum_literal_name(Identifier("something"))
    'Something'

    >>> enum_literal_name(Identifier("URL_to_something"))
    'UrlToSomething'
    """
    return aas_core_codegen.naming.capitalized_camel_case(identifier)


def property_name(identifier: Identifier) -> Identifier:
    """
    Generate a name for a property based on its meta-model ``identifier``.

    >>> property_name(Identifier("something"))
    'something'

    >>> property_name(Identifier("something_to_URL"))
    'somethingToUrl'
    """
    return aas_core_codegen.naming.lower_camel_case(identifier)


def method_name(identifier: Identifier) -> Identifier:
    """
    Generate a name for a member method based on its meta-model ``identifier``.

    >>> method_name(Identifier("do_something"))
    'DoSomething'

    >>> method_name(Identifier("do_something_to_URL"))
    'DoSomethingToUrl'
    """
    return aas_core_codegen.naming.capitalized_camel_case(identifier)


def argument_name(identifier: Identifier) -> Identifier:
    """
    Generate a name for an argument based on its meta-model ``identifier``.

    >>> argument_name(Identifier("something"))
    'something'

    >>> argument_name(Identifier("something_to_URL"))
    'somethingToUrl'
    """
    return aas_core_codegen.naming.lower_camel_case(identifier)


def function_name(identifier: Identifier) -> Identifier:
    """
    Generate a name for a function based on its meta-model ``identifier``.

    >>> function_name(Identifier("do_something"))
    'DoSomething'

    >>> function_name(Identifier("do_something_to_URL"))
    'DoSomethingToUrl'
    """
    return aas_core_codegen.naming.capitalized_camel_case(identifier)


def constrained_primitive(identifier: Identifier) -> Identifier:
    """
    Generate a name for a constrained primitive based on its meta-model ``identifier``.

    >>> constrained_primitive(Identifier("something"))
    'Something'

    >>> constrained_primitive(Identifier("something_to_URL"))
    'SomethingToUrl'
    """
    return aas_core_codegen.naming.capitalized_camel_case(identifier)


def constant_name(identifier: Identifier) -> Identifier:
    """
    Generate a name for a constant based on its meta-model ``identifier``.

    >>> constant_name(Identifier("something"))
    'Something'

    >>> constant_name(Identifier("something_to_URL"))
    'SomethingToUrl'
    """
    return aas_core_codegen.naming.capitalized_camel_case(identifier)


def variable_name(identifier: Identifier) -> Identifier:
    """
    Generate a name for a variable in code.

    >>> variable_name(Identifier("something"))
    'something'

    >>> constant_name(Identifier("something_to_URL"))
    'somethingToUrl'
    """
    return aas_core_codegen.naming.lower_camel_case(identifier)


def of(
    something: Union[
        intermediate.Enumeration,
        intermediate.EnumerationLiteral,
        intermediate.Class,
        intermediate.Verification,
        intermediate.Property,
        intermediate.Method,
        intermediate.ConstrainedPrimitive,
        intermediate.Constant,
    ],
) -> Identifier:
    """Dispatch to the appropriate naming function."""
    if isinstance(something, intermediate.Enumeration):
        return enum_name(something.name)

    elif isinstance(something, intermediate.EnumerationLiteral):
        return enum_name(something.name)

    elif isinstance(something, intermediate.Class):
        return class_name(something.name)

    elif isinstance(something, intermediate.Verification):
        return function_name(something.name)

    elif isinstance(something, intermediate.Property):
        return property_name(something.name)

    elif isinstance(something, intermediate.Method):
        return method_name(something.name)

    elif isinstance(something, intermediate.ConstrainedPrimitive):
        return constrained_primitive(something.name)

    elif isinstance(something, intermediate.Constant):
        return constant_name(something.name)

    else:
        assert_never(something)

    raise AssertionError("Should not have gotten here")
