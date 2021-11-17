"""
Provide stubs for verification methods.

The methods listed here will not be automatically transpiled, and their implementation
needs to be provided in form of snippets.

The stubs provide merely the type annotations and hint about the logic.
"""
from typing import TypeVar, Iterable, Set


def is_IRI(text: str) -> bool:
    raise NotImplementedError()


def is_IRDI(text: str) -> bool:
    raise NotImplementedError()


def is_ID_short(text: str) -> bool:
    raise NotImplementedError()


T = TypeVar("T")


def are_unique(iterable: Iterable[T]) -> bool:
    """Return ``True`` if all the elements in the sequence are unique."""
    observed = set()  # type: Set[T]
    count = 0

    for item in iterable:
        observed.add(item)
        count += 1

    return len(observed) == count
