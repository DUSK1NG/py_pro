import math

import pytest

from mechanics.section_properties import circle_inertia, rectangle_inertia, section_inertia


def test_rectangle_inertia_uses_width_and_height_in_mm():
    assert rectangle_inertia(20, 30) == pytest.approx(20 * 30**3 / 12)


def test_circle_inertia_uses_diameter_in_mm():
    assert circle_inertia(20) == pytest.approx(math.pi * 20**4 / 64)


def test_section_inertia_accepts_custom_inertia():
    assert section_inertia("自定义", inertia=12345) == pytest.approx(12345)


@pytest.mark.parametrize(
    "call",
    [
        lambda: rectangle_inertia(0, 30),
        lambda: rectangle_inertia(20, -1),
        lambda: circle_inertia(float("nan")),
        lambda: section_inertia("自定义", inertia=0),
        lambda: section_inertia("未知"),
    ],
)
def test_section_properties_reject_invalid_inputs(call):
    with pytest.raises(ValueError):
        call()
