"""单位换算层测试。"""

import pytest

from utils.units import (
    convert_distributed_load_to_n_per_mm,
    convert_force_to_n,
    convert_length_to_mm,
)


def test_converts_supported_units_to_internal_units():
    assert convert_length_to_mm(1, "m") == 1000.0
    assert convert_length_to_mm(10, "mm") == 10.0
    assert convert_force_to_n(1, "kN") == 1000.0
    assert convert_distributed_load_to_n_per_mm(1, "kN/m") == 1.0
    assert convert_distributed_load_to_n_per_mm(1, "N/m") == 0.001


@pytest.mark.parametrize(
    "function,unit",
    [
        (convert_length_to_mm, "cm"),
        (convert_force_to_n, "kg"),
        (convert_distributed_load_to_n_per_mm, "kN/cm"),
    ],
)
def test_rejects_unknown_units(function, unit):
    with pytest.raises(ValueError):
        function(1, unit)
