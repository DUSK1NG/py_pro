import pytest

from app import calculate_beam


@pytest.mark.parametrize(
    "load_type, load_value, load_unit, position",
    [
        ("跨中集中力", 100, "N", None),
        ("任意位置集中力", 100, "N", 300),
        ("满跨均布荷载", 1, "N/mm", None),
    ],
)
def test_calculate_beam_results_include_support_reactions(
    load_type, load_value, load_unit, position
):
    result = calculate_beam(
        load_type=load_type,
        load_value=load_value,
        load_unit=load_unit,
        length=1000,
        length_unit="mm",
        elastic_modulus=200000,
        inertia_moment=1000000,
        position=position,
    )

    if load_type == "跨中集中力":
        assert result["left_reaction"] == pytest.approx(50)
        assert result["right_reaction"] == pytest.approx(50)
    elif load_type == "任意位置集中力":
        assert result["left_reaction"] == pytest.approx(70)
        assert result["right_reaction"] == pytest.approx(30)
    else:
        assert result["left_reaction"] == pytest.approx(500)
        assert result["right_reaction"] == pytest.approx(500)
    assert result["left_reaction"] + result["right_reaction"] == pytest.approx(
        100 if load_type != "满跨均布荷载" else 1000
    )
