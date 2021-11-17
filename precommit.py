#!/usr/bin/env python3
"""Run pre-commit checks on the repository."""
import argparse
import enum
import os
import pathlib
import subprocess
import sys


class Step(enum.Enum):
    BLACK = "black"
    MYPY = "mypy"
    RUN = "run"
    CHECK_INIT_AND_SETUP_COINCIDE = "check-init-and-setup-coincide"


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
            "check_init_and_setup_coincide.py"
        ]
        # fmt: on

        if overwrite:
            subprocess.check_call(["black"] + black_targets, cwd=str(repo_root))
        else:
            subprocess.check_call(
                ["black", "--check"] + black_targets, cwd=str(repo_root)
            )
    else:
        print("Skipped black'ing.")

    if Step.MYPY in selects and Step.MYPY not in skips:
        print("Mypy'ing...")
        # fmt: off
        mypy_targets = ["aas_core_meta"]
        subprocess.check_call(["mypy", "--strict"] + mypy_targets, cwd=str(repo_root))
        # fmt: on
    else:
        print("Skipped mypy'ing.")

    if Step.RUN in selects and Step.RUN not in skips:
        print(
            "Running the meta-models "
            "(so that all imports and assertions are tested) ..."
        )

        env = os.environ.copy()
        env["ICONTRACT_SLOW"] = "true"

        module_dir = repo_root / "aas_core_meta"
        for pth in module_dir.iterdir():
            if pth.is_file() and pth.name.startswith("v") and pth.name.endswith(".py"):
                subprocess.check_call([sys.executable, str(pth)], cwd=str(repo_root))
    if (
        Step.CHECK_INIT_AND_SETUP_COINCIDE in selects
        and Step.CHECK_INIT_AND_SETUP_COINCIDE not in skips
    ):
        print("Checking that aas_core_meta/__init__.py and setup.py coincide...")
        subprocess.check_call([sys.executable, "check_init_and_setup_coincide.py"])
    else:
        print(
            "Skipped checking that aas_core_meta/__init__.py and " "setup.py coincide."
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
