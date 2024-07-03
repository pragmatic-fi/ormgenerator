"""CLI"""

import json
import logging
from functools import reduce

import click
import yaml
from jinja2 import Environment, PackageLoader

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


@click.command()
@click.argument("spec", type=click.Path(dir_okay=False, readable=True))
def main(spec: str) -> None:
    """Create skeleton of SQLAlchemy ORM model."""
    with open(spec, encoding="UTF-8") as spec_file:
        spec_content = yaml.safe_load(spec_file)

    log = logging.getLogger(__name__)
    classes: list[str] = []
    env = Environment(loader=PackageLoader("ormgenerator"))

    for obj in spec_content:
        class_name, class_schema_file = obj.popitem()
        log.debug("Processing class %s", class_name)
        try:  # pylint: disable=too-many-try-statements
            with open(
                class_schema_file, encoding="UTF-8"
            ) as class_schema_content:
                class_schema = json.load(class_schema_content)
        except FileNotFoundError:
            log.warning(
                "Cannot find schema '%s' for object '%s'",
                class_schema_file,
                class_name,
            )
            continue
        except json.JSONDecodeError:
            log.warning(
                "Cannot decode JSON schema '%s' for object '%s'",
                class_schema_file,
                class_name,
            )
            continue

        log.debug("Processing object '%s'", class_name)
        class_fields = _process_schema(class_schema)
        template = env.get_template("class.py.j2")
        classes.append(
            template.render(
                class_name=class_name,
                tablename=f"{class_name.lower()}s",
                class_fields=class_fields,
            )
        )

    template = env.get_template("model.py.j2")
    print(template.render(classes=classes))
