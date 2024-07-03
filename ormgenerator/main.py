"""CLI"""

import json
from functools import reduce

from ormgenerator.parse import get_type
from ormgenerator.types import JsonType

_SEP = "__"


def _process_schema(schema: JsonType) -> list[str]:

    def fname(path: list[str]) -> str:
        return reduce(
            lambda f1, f2: f"{f1}{_SEP}{f2}" if f1 and f2 else f1 or f2,
            path,
            "",
        )

    return [
        f"{fname(path)}: Mapped[{type_}]"
        for path, type_ in get_type("ROOT", schema, True)
    ]


def main() -> None:
    """Entry point"""
