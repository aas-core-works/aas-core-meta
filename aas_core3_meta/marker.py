"""Define markers for the meta model to mark the functions and data structures."""
from typing import TypeVar, Type, Optional, Tuple

from icontract import require

T = TypeVar('T')


class implementation_specific:
    """
    Mark the function or class that can not be defined in the meta-model.

    For example, semantics such as ``ValueDataType``'s need to be defined in
    the respective implementation language.

    The specification of the class or function will be disregarded when generating
    the code and serve only as guidance for the developer. Hence the contracts,
    properties and methods need to be manually written.
    """

    def __init__(self, label: Optional[str] = None) -> None:
        """Initialize with the given values."""
        self.label = label

    def __call__(self, thing: T) -> T:
        """Decorate the function or a class."""
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
