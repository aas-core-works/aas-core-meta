#!/usr/bin/env python3
"""Run pre-commit checks on the repository."""
import argparse
import enum
import os
import pathlib
import re
import shlex
import subprocess
import sys
from typing import Sequence, Optional, Mapping, List


class Step(enum.Enum):
    REFORMAT = "reformat"
    MYPY = "mypy"
    RUN = "run"
    AAS_CORE_CODEGEN_SMOKE = "aas-core-codegen-smoke"
    TEST = "test"
    CHECK_INIT_AND_SETUP_COINCIDE = "check-init-and-setup-coincide"
    PYLINT = "pylint"


def call_and_report(
    verb: str,
    cmd: Sequence[str],
    cwd: Optional[pathlib.Path] = None,
    env: Optional[Mapping[str, str]] = None,
) -> int:
    """
    Wrap a subprocess call with the reporting to STDERR if it failed.

    Return 1 if there is an error and 0 otherwise.
    """
    exit_code = None  # type: Optional[int]
    observed_exception = None  # type: Optional[Exception]
    try:
        exit_code = subprocess.call(
            cmd, cwd=str(cwd) if cwd is not None else None, env=env
        )
    except FileNotFoundError as exception:
        observed_exception = exception

    if (exit_code is not None and exit_code != 0) or observed_exception is not None:
        cmd_str = " ".join(shlex.quote(part) for part in cmd)

        if exit_code != 0:
            print(
                f"Failed to {verb} with exit code {exit_code}: {cmd_str}",
                file=sys.stderr,
            )
        elif observed_exception is not None:
            print(
                f"Failed to {verb}: {cmd_str}; with exception: {observed_exception}",
                file=sys.stderr,
            )
            return -1
        else:
            raise AssertionError("Unexpected executiong path")

    return exit_code


def main() -> int:
    """ "Execute entry_point routine."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--overwrite",
        help="Try to automatically fix the offending files (e.g., by re-formatting).",
        action="store_true",
    )
    parser.add_argument(
        "--select",
        help=(
            "If set, only the selected steps are executed. "
            "This is practical if some of the steps failed and you want to "
            "fix them in isolation. "
            "The steps are given as a space-separated list of: "
            + " ".join(value.value for value in Step)
        ),
        metavar="",
        nargs="+",
        choices=[value.value for value in Step],
    )
    parser.add_argument(
        "--skip",
        help=(
            "If set, skips the specified steps. "
            "This is practical if some of the steps passed and "
            "you want to fix the remainder in isolation. "
            "The steps are given as a space-separated list of: "
            + " ".join(value.value for value in Step)
        ),
        metavar="",
        nargs="+",
        choices=[value.value for value in Step],
    )

    args = parser.parse_args()

    overwrite = bool(args.overwrite)

    selects = (
        [Step(value) for value in args.select]
        if args.select is not None
        else [value for value in Step]
    )
    skips = [Step(value) for value in args.skip] if args.skip is not None else []

    repo_root = pathlib.Path(__file__).parent

    if Step.REFORMAT in selects and Step.REFORMAT not in skips:
        print("Re-formatting...")
        # fmt: off
        black_targets = [
            "aas_core_meta",
            "precommit.py",
            "setup.py",
            "check_init_and_setup_coincide.py",
            "tests",
            "htmlgen"
        ]
        # fmt: on

        # region Check or remove trailing whitespace
        trailing_whitespace_pths = []  # type: List[pathlib.Path]

        for relative_pth in black_targets:
            pth = repo_root / relative_pth
            if pth.is_file():
                trailing_whitespace_pths.append(pth)
            elif pth.is_dir():
                trailing_whitespace_pths.extend(pth.glob("**/*.py"))
            else:
                raise RuntimeError(
                    f"Unexpected path to neither a file nor a directory: {pth}"
                )

        trailing_whitespace_pths.sort()

        offending_lines = []  # type: List[int]

        for pth in trailing_whitespace_pths:
            text = pth.read_text(encoding="utf-8")
            lines = text.splitlines()
            if overwrite:
                lines = [re.sub(r"[ \t]+$", "", line) for line in lines]

                new_text = "\n".join(lines)
                if text.endswith("\n") and not new_text.endswith("\n"):
                    new_text = new_text + "\n"

                pth.write_text(new_text, encoding="utf-8")
            else:
                for i, line in enumerate(lines):
                    if re.match(r"[ \t]+$", line) is not None:
                        offending_lines.append(i)

            if len(offending_lines) > 0:
                for i in offending_lines:
                    print(
                        f"{pth.relative_to(repo_root)}:{i + 1}: "
                        f"unexpected trailing whitespace",
                        file=sys.stderr,
                    )
                return 1

        # endregion

        if overwrite:
            exit_code = call_and_report(
                verb="black", cmd=["black"] + black_targets, cwd=repo_root
            )
            if exit_code != 0:
                return 1
        else:
            exit_code = call_and_report(
                verb="check with black",
                cmd=["black", "--check"] + black_targets,
                cwd=repo_root,
            )
            if exit_code != 0:
                return 1
    else:
        print("Skipped reformatting.")

    if Step.MYPY in selects and Step.MYPY not in skips:
        print("Mypy'ing...")
        mypy_targets = ["aas_core_meta", "htmlgen"]

        exit_code = call_and_report(
            verb="mypy",
            cmd=["mypy", "--strict", "--config-file", "mypy.ini"] + mypy_targets,
            cwd=repo_root,
        )
        if exit_code != 0:
            return 1
    else:
        print("Skipped mypy'ing.")

    module_dir = repo_root / "aas_core_meta"

    if Step.RUN in selects and Step.RUN not in skips:
        print(
            "Running the meta-models "
            "(so that all imports and assertions are tested) ..."
        )

        env = os.environ.copy()
        env["ICONTRACT_SLOW"] = "true"

        for pth in sorted(pth for pth in module_dir.glob("v*.py") if pth.is_file()):
            exit_code = call_and_report(
                verb="run the meta-models",
                cmd=[sys.executable, str(pth)],
                cwd=repo_root,
            )
            if exit_code != 0:
                return 1

    if (
        Step.AAS_CORE_CODEGEN_SMOKE in selects
        and Step.AAS_CORE_CODEGEN_SMOKE not in skips
    ):
        print("Running smoke tests with aas-core-codegen-smoke...")

        for pth in sorted(pth for pth in module_dir.glob("v*.py") if pth.is_file()):
            exit_code = call_and_report(
                verb="Run smoke tests with aas-core-codegen-smoke",
                cmd=["aas-core-codegen-smoke", "--model_path", str(pth)],
                cwd=repo_root,
            )
            if exit_code != 0:
                return 1
    else:
        print("Skipped smoke tests with aas-core-codegen-smoke.")

    if Step.TEST in selects and Step.TEST not in skips:
        print("Running unit tests...")
        env = os.environ.copy()
        env["ICONTRACT_SLOW"] = "true"

        exit_code = call_and_report(
            verb="execute unit tests",
            cmd=[
                sys.executable,
                "-m",
                "unittest",
                "discover",
            ],
            cwd=repo_root,
            env=env,
        )
        if exit_code != 0:
            return 1

    if (
        Step.CHECK_INIT_AND_SETUP_COINCIDE in selects
        and Step.CHECK_INIT_AND_SETUP_COINCIDE not in skips
    ):
        print("Checking that aas_core_meta/__init__.py and setup.py coincide...")
        exit_code = call_and_report(
            verb="Check that aas_core_meta/__init__.py and setup.py coincide",
            cmd=[sys.executable, "check_init_and_setup_coincide.py"],
            cwd=repo_root,
        )
        if exit_code != 0:
            return 1
    else:
        print("Skipped checking that aas_core_meta/__init__.py and setup.py coincide.")

    if Step.PYLINT in selects and Step.PYLINT not in skips:
        print("Pylint'ing...")
        pylint_targets = ["tests", "htmlgen"]
        rcfile = "pylint.rc"

        exit_code = call_and_report(
            verb="pylint",
            cmd=[sys.executable, "-m", "pylint", f"--rcfile={rcfile}"] + pylint_targets,
            cwd=repo_root,
        )
        if exit_code != 0:
            return 1
    else:
        print("Skipped pylint'ing.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
