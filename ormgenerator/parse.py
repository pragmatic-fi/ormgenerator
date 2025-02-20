"""Parser for one property."""

import logging
import sys
from collections.abc import Callable
from typing import cast

from ormgenerator.types import JsonType


def _process_object(
    name: str, element: JsonType, required: bool
) -> list[tuple[list[str], str]]:
    log = logging.getLogger(__name__)
    result = cast(list[tuple[list[str], str]], [])
    required_fields = cast(list[str], element.get("required"))
    if not (props := cast(JsonType, element.get("properties") or {})):
        log.warning(
            "Object %s '%s' has no properties, creating one optional 'blah' string field.",
            name,
            element,
        )
        return [(["blah"], "Optional[str]")]

    for subfield, schema in props.items():
        sbft = get_type(
            f"{name}->{subfield}",
            cast(JsonType, schema),
            required and (subfield in required_fields),
        )
        for path, type_ in sbft:
            new_path = [subfield]
            new_path.extend(path)
            result.append((new_path, type_))
    return result


def _process_array(
    name: str, element: JsonType, required: bool
) -> list[tuple[list[str], str]]:
    log = logging.getLogger(__name__)
    if not (items := cast(JsonType, element.get("items") or {})):
        log.warning(
            "Array %s '%s' has no items, creating one optional list of strings",
            name,
            element,
        )

        return [([""], "Optional[list[str]]")]
    op = "" if required else "Optional["
    cl = "" if required else "]"
    return [
        (path, f"{op}list[{type_}]{cl}")
        for path, type_ in get_type(f"{name}->(item)", items, required)
    ]


def _scalar(
    type_: str,
) -> Callable[[str, JsonType, bool], list[tuple[list[str], str]]]:
    def inner(
        name: str,
        _: JsonType,
        required: bool,
    ) -> list[tuple[list[str], str]]:
        log = logging.getLogger(__name__)
        log.debug("Scalar element %s of type %s", name, type_)
        op = "" if required else "Optional["
        cl = "" if required else "]"
        return [([], f"{op}{type_}{cl}")]

    return inner


_MAPPING = {
    "object": _process_object,
    "array": _process_array,
    "number": _scalar("float"),
    "string": _scalar("str"),
    "boolean": _scalar("bool"),
}


# if type is an array, we understand only [real_type, "null"]
_HACK_TYPE_LEN = 2
_NULL = "null"


def get_type(
    name: str, element: JsonType, required: bool
) -> list[tuple[list[str], str]]:
    """Parse given element and return the corresponding SQLAlchemy type.

    Return the list of subfields (see return value). If the given
    element is not an object, returns something like
    [([], "str")]. Notice that Mapped is not added.

    :param name: The name of the current element (used for logging)
    :param element: The part of JSON schema representing the element.
    :param required: Return the list of tuples, where the first element
                     is a list of strings, representing the path to
                     subfield, and the second is SQLAlchemy type of
                     subfield.
    """
    log = logging.getLogger(__name__)
    log.debug("Processing element %s", name)
    if not (tp := cast(str | list[str], element.get("type") or "")):
        log.fatal("Element '%s' has no type, exiting.", element)
        sys.exit(1)

    if tp == _NULL:
        log.warning("Type of %s is null, skipping", name)
        return []

    if isinstance(tp, list):
        # HACK: hardcoded behaviour
        if not len(tp) == _HACK_TYPE_LEN:
            log.fatal("Cannot process type '%s', exiting.", tp)
            sys.exit(1)
        if (tp_real := tp[0]) == _NULL:
            tp_real = tp[1]
        elif not tp[1] == _NULL:
            log.fatal("Cannot process type '%s', exiting.", tp)
            sys.exit(1)
        required = False
    else:
        tp_real = tp

    if tp_real not in _MAPPING:
        log.fatal("Unknown type '%s' in '%s', exiting.", tp, element)
        sys.exit(1)
    return _MAPPING[tp_real](name, element, required)
