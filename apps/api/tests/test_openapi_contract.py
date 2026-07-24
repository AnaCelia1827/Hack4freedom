import re
from pathlib import Path

from bluejet_api import create_app


HTTP_METHODS = {"delete", "get", "patch", "post", "put"}
OPENAPI_PATH = Path(__file__).resolve().parents[3] / "openapi" / "openapi.yaml"


def _normalized_path(path: str, parameter_pattern: str) -> str:
    return re.sub(parameter_pattern, "{}", path)


def _openapi_operations() -> set[tuple[str, str]]:
    operations = []
    current_path = None
    inside_paths = False

    for line in OPENAPI_PATH.read_text(encoding="utf-8").splitlines():
        if line == "paths:":
            inside_paths = True
            continue
        if inside_paths and line and not line.startswith(" "):
            break

        path_match = re.match(r"^  (/[^:]+):\s*$", line)
        if path_match:
            current_path = path_match.group(1)
            continue

        method_match = re.match(r"^    ([a-z]+):\s*$", line)
        if current_path and method_match and method_match.group(1) in HTTP_METHODS:
            operations.append(
                (
                    method_match.group(1).upper(),
                    _normalized_path(current_path, r"\{[^}]+\}"),
                )
            )

    assert len(operations) == len(set(operations)), "OpenAPI contains a duplicate path and method"
    return set(operations)


def _runtime_operations() -> set[tuple[str, str]]:
    app = create_app()
    return {
        (method, _normalized_path(rule.rule, r"<[^>]+>"))
        for rule in app.url_map.iter_rules()
        if rule.endpoint != "static"
        for method in rule.methods - {"HEAD", "OPTIONS"}
    }


def test_openapi_paths_and_methods_match_flask_runtime():
    assert _openapi_operations() == _runtime_operations()
