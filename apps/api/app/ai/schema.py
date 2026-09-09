"""Translate DealSage validation schemas to the shared provider-safe subset."""

from copy import deepcopy
from typing import Any


UNSUPPORTED_PROVIDER_KEYWORDS = frozenset(
    {
        "uniqueItems",
        "minLength",
        "maxLength",
        "minimum",
        "maximum",
        "exclusiveMinimum",
        "exclusiveMaximum",
        "multipleOf",
    }
)


def provider_safe_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Remove constraints unsupported by both providers; local validation retains them."""
    portable = deepcopy(schema)

    def visit(node: Any) -> None:
        if isinstance(node, dict):
            for keyword in UNSUPPORTED_PROVIDER_KEYWORDS:
                node.pop(keyword, None)
            if isinstance(node.get("minItems"), int) and node["minItems"] not in (0, 1):
                node.pop("minItems")
            for value in node.values():
                visit(value)
        elif isinstance(node, list):
            for value in node:
                visit(value)

    visit(portable)
    return portable
