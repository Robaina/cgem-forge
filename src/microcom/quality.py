from __future__ import annotations
from pathlib import Path
import json


class Memote:
    """Class to run memote tests on a model."""

    def __init__(self, report: Path):
        with open(report, "r") as f:
            self._report = json.load(f)

    @property
    def report(self) -> dict:
        """Return memote report as dictionary."""
        return self._report

    def get_duplicated_reactions(self) -> list[list]:
        """Retrieve duplicated reactions from memote report

        Returns:
            list: list of lists of duplicated reaction pair IDs
        """
        tests = self._report["tests"]
        return tests["test_find_duplicated_reactions"]["data"]
