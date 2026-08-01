"""跨中集中力简支梁的基础力学计算测试。"""

import pytest

from mechanics.central_point_load import bending_moment, shear_force, support_reactions


def test_support_reactions_are_equal_for_midspan_load():
    """跨中集中力的两个支座反力均为 P/2。"""
    assert support_reactions(1000, 100) == (50.0, 50.0)


def test_shear_force_changes_sign_across_midspan():
    """剪力在跨中荷载处发生大小为 P 的跳变。"""
    assert shear_force(499, 1000, 100) == 50.0
    assert shear_force(500, 1000, 100) == 50.0
    assert shear_force(501, 1000, 100) == -50.0


def test_bending_moment_is_zero_at_supports_and_largest_at_midspan():
    """弯矩在两支座为零，跨中为最大值 P*L/4。"""
    assert bending_moment(0, 1000, 100) == 0.0
    assert bending_moment(500, 1000, 100) == 25000.0
    assert bending_moment(1000, 1000, 100) == 0.0


def test_force_functions_reject_position_outside_beam():
    """梁外位置不能用于剪力与弯矩计算。"""
    with pytest.raises(ValueError):
        shear_force(1001, 1000, 100)
