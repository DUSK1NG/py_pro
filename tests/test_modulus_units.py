"""弹性模量单位换算测试。"""

from utils.units import convert_modulus_to_mpa


def test_converts_gpa_to_mpa():
    assert convert_modulus_to_mpa(1, "GPa") == 1000.0
    assert convert_modulus_to_mpa(200, "MPa") == 200.0
