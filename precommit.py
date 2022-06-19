#!/usr/bin/env python3
"""Run pre-commit checks on the repository."""
import argparse
import enum
import os
import pathlib
import shlex
import subprocess
import sys
from typing import Sequence, Optional, Mapping


class Step(enum.Enum):
    BLACK = "black"
    MYPY = "mypy"
    RUN = "run"
    AAS_CORE_CODEGEN_SMOKE = "aas-core-codegen-smoke"
    TEST = "test"
    CHECK_INIT_AND_SETUP_COINCIDE = "check-init-and-setup-coincide"


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
    exit_code = subprocess.call(cmd, cwd=str(cwd) if cwd is not None else None, env=env)

    if exit_code != 0:
        cmd_str = " ".join(shlex.quote(part) for part in cmd)
        print(
            f"Failed to {verb} with exit code {exit_code}: {cmd_str}", file=sys.stderr
        )

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

    if Step.BLACK in selects and Step.BLACK not in skips:
        print("Black'ing...")
        # fmt: off
        black_targets = [
            "aas_core_meta",
            "precommit.py",
            "setup.py",
            "check_init_and_setup_coincide.py",
            "tests"
        ]
        # fmt: on

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
        print("Skipped black'ing.")

    if Step.MYPY in selects and Step.MYPY not in skips:
        print("Mypy'ing...")
        mypy_targets = ["aas_core_meta"]

        exit_code = call_and_report(
            verb="mypy",
            cmd=["mypy", "--strict"] + mypy_targets,
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

    return 0


if __name__ == "__main__":
    sys.exit(main())
