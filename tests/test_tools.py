import pytest

from app.services.tools import TOOL_DEFINITIONS, calculate


def test_calculate_allows_arithmetic() -> None:
    assert calculate("(12 * 3) - 4 / 2") == 34


@pytest.mark.parametrize("expression", ["__import__('os').system('whoami')", "open('x')", "a + 1"])
def test_calculate_blocks_code_execution(expression: str) -> None:
    with pytest.raises(ValueError):
        calculate(expression)


def test_tool_schemas_are_strict() -> None:
    assert all(tool["strict"] and tool["parameters"]["additionalProperties"] is False for tool in TOOL_DEFINITIONS)

