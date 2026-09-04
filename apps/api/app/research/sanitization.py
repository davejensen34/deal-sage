from dataclasses import dataclass
import re
from typing import Any


# Normalize field spelling before comparison so snake_case, camelCase, and
# punctuation variants cannot bypass the capability-field boundary.
SENSITIVE_FIELD_NAMES = frozenset(
    {
        "accesstoken",
        "apikey",
        "authorization",
        "clientsecret",
        "cookie",
        "csrftoken",
        "creationsessionid",
        "edittoken",
        "managementurl",
        "password",
        "refreshtoken",
        "sessionid",
        "sessiontoken",
    }
)


@dataclass(frozen=True)
class SanitationReport:
    retained_fields: int
    dropped_unknown_paths: tuple[str, ...]
    dropped_sensitive_paths: tuple[str, ...]

    def public_summary(self) -> dict[str, Any]:
        """Describe contract handling without retaining any external values."""
        return {
            "retained_fields": self.retained_fields,
            "dropped_unknown_count": len(self.dropped_unknown_paths),
            "dropped_sensitive_count": len(self.dropped_sensitive_paths),
            "dropped_unknown_paths": list(self.dropped_unknown_paths),
            "dropped_sensitive_paths": list(self.dropped_sensitive_paths),
        }


@dataclass(frozen=True)
class SanitizedResponse:
    data: dict[str, Any]
    report: SanitationReport


def normalize_field_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def is_sensitive_field(name: str) -> bool:
    return normalize_field_name(name) in SENSITIVE_FIELD_NAMES


def sanitize_external_mapping(
    payload: dict[str, Any], allowlist: dict[str, Any]
) -> SanitizedResponse:
    """Apply an explicit shape policy and drop unsafe or unknown fields in memory.

    A rule is `True` for a scalar, a nested mapping for an object, or a
    single-item list containing the rule for every list item. Structured values
    require an explicit nested shape so an allowed parent cannot smuggle in new
    fields after a provider contract change.
    """
    unknown: list[str] = []
    sensitive: list[str] = []
    retained = [0]
    data = _sanitize_value(payload, allowlist, "$", unknown, sensitive, retained)
    return SanitizedResponse(
        data=data,
        report=SanitationReport(
            retained_fields=retained[0],
            dropped_unknown_paths=tuple(unknown),
            dropped_sensitive_paths=tuple(sensitive),
        ),
    )


def _sanitize_value(
    value: Any,
    rule: Any,
    path: str,
    unknown: list[str],
    sensitive: list[str],
    retained: list[int],
) -> Any:
    if rule is True:
        if isinstance(value, (dict, list)):
            raise ValueError(f"Structured allowlist rule required at {path}")
        retained[0] += 1
        return value
    if isinstance(rule, dict):
        if not isinstance(value, dict):
            raise ValueError(f"Expected object at {path}")
        result = {}
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if is_sensitive_field(str(key)):
                sensitive.append(child_path)
            elif key not in rule:
                unknown.append(child_path)
            else:
                result[key] = _sanitize_value(
                    child, rule[key], child_path, unknown, sensitive, retained
                )
        return result
    if isinstance(rule, list) and len(rule) == 1:
        if not isinstance(value, list):
            raise ValueError(f"Expected list at {path}")
        return [
            _sanitize_value(item, rule[0], f"{path}[{index}]", unknown, sensitive, retained)
            for index, item in enumerate(value)
        ]
    raise ValueError(f"Invalid sanitation policy at {path}")
