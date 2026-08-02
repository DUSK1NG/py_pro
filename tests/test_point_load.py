"""任意位置集中力简支梁的测试。"""

import pytest

from mechanics.point_load import bending_moment, shear_force, support_reactions


def test_reactions_and_internal_forces_for_off_center_load():
    """非跨中荷载应产生不相等反力和正确的剪力、弯矩。"""
    assert support_reactions(1000, 100, 300) == (70.0, 30.0)
    assert shear_force(300, 1000, 100, 300) == 70.0
    assert shear_force(301, 1000, 100, 300) == -30.0
    assert bending_moment(300, 1000, 100, 300) == 21000.0


@pytest.mark.parametrize("position", [0, 1000, -1, 1001])
def test_load_position_must_be_strictly_inside_beam(position):
    """荷载位置必须严格位于两个支座之间。"""
    with pytest.raises(ValueError):
        support_reactions(1000, 100, position)
