import ast
import pathlib
import unittest
from types import ModuleType
from typing import MutableMapping, Union

import asttokens
from aas_core_codegen.common import Identifier

import aas_core_meta.v3
import aas_core_meta.v3_http

import tests.common


# TODO (mristin, 2024-06-21): remove
# def module_from_ast(atok: asttokens.ASTTokens) -> ast.Module:
#     """Retrieve the underlying module from the given Abstract Syntax Tree."""
#     root = atok.tree
#     assert isinstance(root, ast.Module)
#     return root
#
# def map_symbols_to_ast_nodes(
#         a_module: ast.Module
# ) -> MutableMapping[str, Union[ast.FunctionDef, ast.ClassDef, ast.Assign]]:
#     """Map each symbol in the module to its corresponding name."""
#     mapping: MutableMapping[
#         str,
#         Union[ast.FunctionDef, ast.ClassDef, ast.Assign]
#     ] = dict()
#
#     for i, stmt in enumerate(a_module.body):
#         if (
#                 i == 0 and isinstance(stmt, ast.Expr)
#                 and isinstance(stmt.value, ast.Constant)
#                 and isinstance(stmt.value.value, str)
#         ):
#             # NOTE (mristin):
#             # We skip the docstring of the module.
#             continue
#         elif isinstance(stmt, (ast.ImportFrom, ast.Import)):
#             # NOTE (mristin):
#             # The imports refer to the markers and types, so we skip them. They do not
#             # introduce any symbols by definition of our domain-specific language.
#             continue
#         elif isinstance(stmt, (ast.ClassDef, ast.FunctionDef)):
#             mapping[stmt.name] = stmt
#         elif isinstance(stmt, ast.Assign):
#             print(f"ast.dump(stmt) is {ast.dump(stmt)!r}")  # TODO: debug
#         else:
#             assert_never(stmt)
#
#     return mapping

class TestAssertions(unittest.TestCase):
    def test_inheritance(self) -> None:
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


if __name__ == "__main__":
    unittest.main()
