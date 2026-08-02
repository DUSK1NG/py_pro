"""任意位置集中力简支梁的挠度与采样测试。"""

import math

from mechanics.central_point_load import deflection as midspan_deflection
from mechanics.point_load import deflection, sample_beam


def test_deflection_boundaries_and_midspan_compatibility():
    """挠度在支座为零，跨中时与第一阶段公式一致。"""
    assert deflection(0, 1000, 100, 300, 200000, 1000000) == 0.0
    assert deflection(1000, 1000, 100, 300, 200000, 1000000) == 0.0
    assert math.isclose(
        deflection(500, 1000, 100, 500, 200000, 1000000),
        midspan_deflection(500, 1000, 100, 200000, 1000000),
    )


def test_sample_result_contains_load_position_and_exact_maximum_moment():
    """偶数采样点时也必须额外保留荷载位置和精确最大弯矩。"""
    result = sample_beam(1000, 100, 300, 200000, 1000000, sample_count=100)

    assert 300.0 in result["x"]
    assert result["max_moment"] == 21000.0
    assert result["max_moment_position"] == 300.0
