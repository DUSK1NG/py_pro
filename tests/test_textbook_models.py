"""教材题梁模型的输入校验测试。"""

import pytest

from mechanics.textbook_models import (
    BeamProblem,
    DistributedLoad,
    PointLoad,
    ProblemInputError,
    Support,
)


def make_problem(**changes):
    """构造一个可供单项校验测试复用的有效问题。"""
    values = {
        "length_mm": 1000.0,
        "elastic_modulus_mpa": 200000.0,
        "inertia_mm4": 1_000_000.0,
        "supports": [Support(0.0, "pin"), Support(1000.0, "roller")],
        "point_loads": [],
        "distributed_loads": [],
    }
    values.update(changes)
    return BeamProblem(**values)


def test_validate_rejects_support_outside_beam():
    problem = make_problem(supports=[Support(-1.0, "pin")])

    with pytest.raises(ProblemInputError):
        problem.validate()


def test_validate_rejects_reverse_distributed_load_interval():
    problem = make_problem(distributed_loads=[DistributedLoad(700.0, 200.0, -2.0)])

    with pytest.raises(ProblemInputError):
        problem.validate()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("length_mm", 0.0),
        ("elastic_modulus_mpa", 0.0),
        ("inertia_mm4", -1.0),
    ],
)
def test_validate_rejects_non_positive_beam_properties(field, value):
    problem = make_problem(**{field: value})

    with pytest.raises(ProblemInputError):
        problem.validate()


def test_validate_rejects_unsupported_support_kind():
    problem = make_problem(supports=[Support(0.0, "hinge")])

    with pytest.raises(ProblemInputError):
        problem.validate()


def test_validate_rejects_duplicate_support_positions():
    problem = make_problem(supports=[Support(0.0, "pin"), Support(0.0, "roller")])

    with pytest.raises(ProblemInputError):
        problem.validate()


def test_validate_rejects_point_load_outside_beam():
    problem = make_problem(point_loads=[PointLoad(1001.0, -1.0)])

    with pytest.raises(ProblemInputError):
        problem.validate()


def test_validate_rejects_distributed_load_outside_beam():
    problem = make_problem(distributed_loads=[DistributedLoad(0.0, 1001.0, -1.0)])

    with pytest.raises(ProblemInputError):
        problem.validate()


def test_validate_rejects_empty_supports():
    problem = make_problem(supports=[])

    with pytest.raises(ProblemInputError):
        problem.validate()


def test_total_vertical_load_preserves_load_signs():
    problem = make_problem(
        point_loads=[PointLoad(200.0, -100.0), PointLoad(800.0, 25.0)],
        distributed_loads=[
            DistributedLoad(0.0, 100.0, -2.0),
            DistributedLoad(500.0, 700.0, 0.5),
        ],
    )

    assert problem.total_vertical_load_n() == -175.0
