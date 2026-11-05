"""Small helpers for reading DATEX II XML without caring about namespaces.

NDW publishes DATEX II v2.3 and v3 files. The element names are stable across
versions, but the namespaces and prefixes are not, so everything here matches
on the *local* name of an element (the part after the namespace).
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import IO
from xml.etree import ElementTree as ET

XSI_TYPE = "{http://www.w3.org/2001/XMLSchema-instance}type"


def local(tag: str) -> str:
    """Return the local name of a tag: '{ns}speed' -> 'speed'."""
    return tag.rsplit("}", 1)[-1]


def xsi_type(elem: ET.Element) -> str:
    """Return the xsi:type of an element without its prefix ('sit:Foo' -> 'Foo')."""
    value = elem.get(XSI_TYPE, "")
    return value.rsplit(":", 1)[-1]


def find_first(elem: ET.Element, name: str) -> ET.Element | None:
    """First descendant (depth first) whose local name is `name`."""
    for child in elem.iter():
        if child is not elem and local(child.tag) == name:
            return child
    return None


def text_of(elem: ET.Element, name: str) -> str | None:
    """Stripped text of the first descendant called `name`, or None."""
    found = find_first(elem, name)
    if found is None or found.text is None:
        return None
    return found.text.strip() or None


def iter_elements(source: IO[bytes], name: str) -> Iterator[ET.Element]:
    """Stream through `source`, yielding each complete element called `name`.

    Elements are cleared after they are yielded, so memory stays flat even for
    large national files.
    """
    for _event, elem in ET.iterparse(source, events=("end",)):
        if local(elem.tag) == name:
            yield elem
            elem.clear()


def to_float(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None
