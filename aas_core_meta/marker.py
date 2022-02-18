"""Define markers for the meta model to mark the functions and data structures."""
from enum import Enum
from typing import (
    TypeVar,
    Type,
    Optional,
    Tuple,
    Generic,
    Sequence,
    Callable,
    Any,
    Union,
    overload,
)

from icontract import require

T = TypeVar("T")

CallableT = TypeVar("CallableT", bound=Callable[..., Any])


@overload
def implementation_specific(thing: Type[T]) -> Type[T]:
    ...


@overload
def implementation_specific(thing: CallableT) -> CallableT:
    ...


# See https://github.com/python/mypy/issues/9420 for why we use ``Any`` here
def implementation_specific(thing: Any) -> Any:
    """
    Mark the function or class that can not be defined in the meta-model.

    The specification of the class or function will be disregarded when generating
    the code and serve only as guidance for the developer. Hence the contracts,
    properties and methods need to be manually written.
    """
    return thing


def comment(text: str) -> None:
    """Mark a comment to be included in the generated code."""
    pass


def abstract(thing: Type[T]) -> Type[T]:
    """
    Mark the class as abstract.

    This instructs the code generators for languages which do not support
    multiple inheritance to convert them to interfaces.
    """
    return thing


class reference_in_the_book:
    """Mark the location in the book where the definition resides."""

    @require(lambda section: all(number >= 1 for number in section))
    @require(lambda index: index >= 0)
    def __init__(
        self, section: Tuple[int, ...], index: int = 0, fragment: Optional[str] = None
    ) -> None:
        """
        Initialize with the given values.

        :param section: Section of the book given as tuple (so that it is sortable)
        :param index:
            Index in the section.
            The index helps us distinguish between multiple definitions in a section.
        :param fragment:
            Fragment of the section as a fragment suffix to the book URL.

            If no fragment is given, the fragment is computed as a concatenation
            of the indicated section number and the capitalized class name.

            Example of an inferred fragment:

            .. code-block:

                @reference_in_the_book(section=(4, 7, 2, 8))
                class Qualifiable(...):
                    ...

            The inferred fragment will be ``4.7.2.8 Qualifiable``.

            Example of a fully specified fragment:

            .. code-block:

                @reference_in_the_book(
                    section=(4, 7, 2, 13),
                    fragment=(
                        "4.7.2.13 Used Templates for Data Specification "
                        "Attributes (HasDataSpecification)"
                    )
                )
                class HasDataSpecification(...):
                    ...

            We expect the downstream to URL-encode the fragment and prepend the literal
            ``#``.
        """
        self.section = section
        self.index = index
        self.fragment = fragment

    def __call__(self, func: Type[T]) -> Type[T]:
        return func


class serialization:
    """Mark the settings for the general serialization schemas."""

    def __init__(self, with_model_type: bool) -> None:
        """
        Initialize with the given values.

        :param with_model_type:
            The serialization needs to specify the concrete type since the given
            type is abstract and the implemented de-serializations need to know the
            concrete type up-front.
        """
        self.with_model_type = with_model_type

    def __call__(self, func: Type[T]) -> Type[T]:
        return func


EnumT = TypeVar("EnumT", bound=Enum)


class is_superset_of:
    """Mark the contained enumeration subsets of the decoratee."""

    def __init__(self, enums: Sequence[Type[EnumT]]) -> None:
        """
        Initialize with the given values.

        :param enums:
            The contained subset enumerations
        """
        self.enums = enums

    def __call__(self, func: Type[T]) -> Type[T]:
        return func


def verification(thing: CallableT) -> CallableT:
    """Mark the function as a verification function used in contracts."""
    return thing
