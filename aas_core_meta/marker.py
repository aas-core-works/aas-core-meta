"""Define markers for the meta model to mark the functions and data structures."""
from enum import Enum
from typing import TypeVar, Type, Optional, Tuple, Generic, Sequence

from icontract import require

T = TypeVar("T")


def implementation_specific(thing: Type[T]) -> Type[T]:
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


def template(thing: Type[T]) -> Type[T]:
    """
    Mark the class as template.

    specification of the common features of an object in sufficient
    detail that such object can be instantiated using it
    """
    return thing


def deprecated(thing: Type[T]) -> Type[T]:
    """
    Mark deprecated parts of the book
    """
    return thing


class reference_in_the_book:
    """Mark the location in the book where the definition resides."""

    @require(lambda section: all(number >= 1 for number in section))
    @require(lambda index: index >= 0)
    def __init__(self, section: Tuple[int, ...], index: int = 0) -> None:
        """
        Initialize with the given values.

        :param section: Section of the book given as tuple (so that it is sortable)
        :param index:
            Index in the section.

            The index helps us distinguish between multiple definitions in a section.
        """
        self.section = section
        self.index = index

    def __call__(self, func: Type[T]) -> Type[T]:
        return func


class json_serialization:
    """Mark the settings for JSON serialization."""

    def __init__(self, with_model_type: bool) -> None:
        """
        Initialize with the given values.

        :param with_model_type:
            The class needs to include ``modelType`` property in the serialization
        """
        self.with_model_type = with_model_type

    def __call__(self, func: Type[T]) -> Type[T]:
        return func


class Ref(Generic[T]):
    """
    Represent a reference to an instance of ``T``.

    This is described by ``ref*`` in the book.
    """


def associate_ref_with(cls: Type[T]) -> None:
    """Mark that the type ``T`` represents :py:class:`Ref` in the implementation."""


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
