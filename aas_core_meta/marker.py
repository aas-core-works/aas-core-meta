"""Define markers for the meta model to mark the functions and data structures."""
from typing import (
    TypeVar,
    Type,
    Optional,
    Sequence,
    Callable,
    Any,
    overload,
    Set,
    List,
)

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


def non_mutating(thing: CallableT) -> CallableT:
    """
    Mark the method as non-mutating.

    At the moment (2023-07-07), the non-mutating property of the method will *not*
    be checked by the downstream code generators as that is very complex. Some compilers
    might partially enforce it (such as popular C++ compilers like clang or g++), but
    bear in mind that they also do not completely cover the whole problem space.

    See, for example, this paper for some background:
    https://pm.inf.ethz.ch/publications/LeinoMuellerWallenburg08.pdf
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


def verification(thing: CallableT) -> CallableT:
    """Mark the function as a verification function used in contracts."""
    return thing


# noinspection PyUnusedLocal,PyShadowingNames
def constant_bool(
    value: bool,
    description: Optional[str] = None,
) -> bool:
    """Define a constant boolean in the meta-model."""
    return value


# noinspection PyUnusedLocal,PyShadowingNames
def constant_int(
    value: int,
    description: Optional[str] = None,
) -> int:
    """Define a constant integer in the meta-model."""
    return value


# noinspection PyUnusedLocal,PyShadowingNames
def constant_float(
    value: float,
    description: Optional[str] = None,
) -> float:
    """Define a constant floating-point number in the meta-model."""
    return value


# noinspection PyUnusedLocal,PyShadowingNames
def constant_str(
    value: str,
    description: Optional[str] = None,
) -> str:
    """Define a constant string in the meta-model."""
    return value


# noinspection PyUnusedLocal,PyShadowingNames
def constant_bytearray(
    value: bytearray,
    description: Optional[str] = None,
) -> bytearray:
    """Define a constant bytearray in the meta-model."""
    return value


# noinspection PyUnusedLocal,PyShadowingNames
def constant_set(
    values: Sequence[T],
    description: Optional[str] = None,
    superset_of: Optional[Sequence[Set[T]]] = None,
) -> Set[T]:
    """
    Define a constant set in the meta-model.

    The values need to be given as a list so that we can follow the order in
    the generated code.
    """
    result = set(values)

    if superset_of is not None:
        for i, subset in enumerate(superset_of):
            offending_values = []  # type: List[T]
            for value in subset:
                if value not in result:
                    offending_values.append(value)

            if len(offending_values) > 0:
                offending_values_str = ",\n".join(map(str, offending_values))
                raise AssertionError(
                    f"The following values "
                    f"from the subset {i + 1} (index starts from 1) "
                    f"are not contained in the values:\n{offending_values_str}"
                )

    return result
