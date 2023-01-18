"""Generate HTML for all the meta-models."""

import argparse
import io
import os
import pathlib
import sys
from typing import Tuple, Optional, List

import asttokens
from aas_core_codegen import intermediate
from aas_core_codegen.common import Error, LinenoColumner
import aas_core_codegen.run
import aas_core_codegen.parse
from icontract import require, ensure

import htmlgen.for_metamodel


@require(lambda model_path: model_path.exists() and model_path.is_file())
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _load_meta_model(
    model_path: pathlib.Path,
) -> Tuple[
    Optional[Tuple[intermediate.SymbolTable, asttokens.ASTTokens]], Optional[str]
]:
    """Load the given meta-model from the repository and understand it."""
    text = model_path.read_text(encoding="utf-8")

    atok, parse_exception = aas_core_codegen.parse.source_to_atok(source=text)
    if parse_exception:
        if isinstance(parse_exception, SyntaxError):
            return None, (
                f"Failed to parse the meta-model: "
                f"invalid syntax at line {parse_exception.lineno}"
            )
        else:
            return None, f"Failed to parse the meta-model: {parse_exception}"

    assert atok is not None

    import_errors = aas_core_codegen.parse.check_expected_imports(atok=atok)
    if import_errors:
        writer = io.StringIO()
        aas_core_codegen.run.write_error_report(
            message="One or more unexpected imports in the meta-model",
            errors=import_errors,
            stderr=writer,
        )
        return None, writer.getvalue()

    lineno_columner = aas_core_codegen.common.LinenoColumner(atok=atok)

    parsed_symbol_table, error = aas_core_codegen.parse.atok_to_symbol_table(atok=atok)
    if error is not None:
        writer = io.StringIO()
        aas_core_codegen.run.write_error_report(
            message=f"Failed to construct the symbol table",
            errors=[lineno_columner.error_message(error)],
            stderr=writer,
        )
        return None, writer.getvalue()

    assert parsed_symbol_table is not None

    ir_symbol_table, error = intermediate.translate(
        parsed_symbol_table=parsed_symbol_table,
        atok=atok,
    )
    if error is not None:
        writer = io.StringIO()
        aas_core_codegen.run.write_error_report(
            message=f"Failed to translate the parsed symbol table "
            f"to intermediate symbol table",
            errors=[lineno_columner.error_message(error)],
            stderr=writer,
        )
        return None, writer.getvalue()

    assert ir_symbol_table is not None

    return (ir_symbol_table, atok), None


def main() -> int:
    """Execute the main routine."""
    this_path = pathlib.Path(os.path.realpath(__file__))

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--html_dir",
        help="path to where the generated HTML will be saved",
    )
    args = parser.parse_args()

    html_dir = pathlib.Path(args.html_dir)
    html_dir.mkdir(parents=True, exist_ok=True)

    this_path = pathlib.Path(os.path.realpath(__file__))

    aas_core_meta_dir = this_path.parent.parent / "aas_core_meta"

    names_paths = []  # type: List[Tuple[str, str]]

    for model_path in sorted(aas_core_meta_dir.glob("v*.py")):
        symbol_table_atok, error = _load_meta_model(model_path)
        if error is not None:
            print(f"Failed to load {model_path}:\n{error}", file=sys.stderr)
            return 1

        assert symbol_table_atok is not None
        symbol_table, atok = symbol_table_atok

        target_dir = html_dir / model_path.stem
        target_dir.mkdir(exist_ok=True)
        htmlgen.for_metamodel.generate(
            symbol_table=symbol_table, atok=atok, target_dir=target_dir
        )

        names_paths.append(
            (
                symbol_table.meta_model.book_version,
                (target_dir / "index.html").relative_to(html_dir).as_posix(),
            )
        )

    li_models = [f'<li><a href="{path}">{name}</a></li>' for name, path in names_paths]
    li_models_joined = "\n".join(li_models)
    ul_models = f"<ul>\n{li_models_joined}\n</ul>"

    (html_dir / "index.html").write_text(
        f"""\
<html>
<head>
<title>aas-core-meta</title>
</head>
<body>
<h1>aas-core-meta</h1>
<p>
This is automatically generated documentation based on the meta-models of the AAS
written in simplified Python.
</p>
<p>
Please refer to the original publications of the AAS workgroups for official releases.
</p>
<p>
We generated the HTML documentation for the following versions of the meta-model:
</p>
{ul_models}
</body>
</html>
""",
        encoding="utf-8",
    )
    # TODO (mristin, 2023-01-13): generate the index page

    return 0


if __name__ == "__main__":
    sys.exit(main())
