import ast
import difflib
import itertools
import pathlib
import unittest
from types import ModuleType
from typing import MutableMapping, Union, Optional

import asttokens
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


class TestAssertions(unittest.TestCase):
    def test_module_inheritance(self) -> None:
        """
        Test that all the definitions are inherited from the original meta-model.

        We exclude :py:class:`v3.Environment` as it is not used in the API.
        """
        v3 = tests.common.load_meta_model(
            model_path=pathlib.Path(aas_core_meta.v3.__file__)
        )

        v3_http = tests.common.load_meta_model(
            model_path=pathlib.Path(aas_core_meta.v3_http.__file__)
        )

        assert v3_http.symbol_table.find_our_type(Identifier('Environment')) is None, (
            f"The class ``Environment`` should not be defined "
            f"in {aas_core_meta.v3_http.__file__}, but it was."
        )

        for our_type in v3.symbol_table.our_types:
            if our_type.name == "Environment":
                continue

            other_our_type = v3_http.symbol_table.find_our_type(our_type.name)
            if other_our_type is None:
                raise AssertionError(
                    f"Our type {our_type.name!r} is missing "
                    f"in {aas_core_meta.v3_http.__file__}, "
                    f"but defined in {aas_core_meta.v3.__file__}"
                )

            # noinspection PyTypeChecker
            diff = compute_diff_text(
                text=v3.atok.get_text(our_type.parsed.node),
                other=v3_http.atok.get_text(other_our_type.parsed.node),
            )

            if diff is not None:
                raise AssertionError(
                    f"The text for our type {our_type.name!r} differs "
                    f"between {aas_core_meta.v3.__file__} and "
                    f"{aas_core_meta.v3_http.__file__}. Diff:\n"
                    f"{diff}"
                )


if __name__ == "__main__":
    unittest.main()
