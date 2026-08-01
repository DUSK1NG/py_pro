"""输入校验模块的测试。"""

import pytest

from utils.validation import validate_positive_finite, validate_sample_count


@pytest.mark.parametrize("value", [0, -1, float("nan"), float("inf"), "100"])
def test_positive_finite_validator_rejects_invalid_values(value):
    """长度、荷载等必须是有限的正数。"""
    with pytest.raises(ValueError):
        validate_positive_finite(value, "梁长 L")


def test_sample_count_validator_accepts_three_or_more_integer_points():
    """采样点数至少为 3，且必须为整数。"""
    assert validate_sample_count(3) == 3


def test_sample_count_validator_rejects_too_few_or_non_integer_points():
    """不接受过少、非整数或布尔类型的采样点数。"""
    for value in (2, 3.5, True):
        with pytest.raises(ValueError):
            validate_sample_count(value)
