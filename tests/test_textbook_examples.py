"""教材梁 JSON 示例的端到端回归测试。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mechanics.textbook_models import BeamProblem, DistributedLoad, PointLoad, Support
from mechanics.textbook_solver import solve_textbook_beam


EXAMPLES_PATH = Path(__file__).parents[1] / "sample_data" / "textbook_examples.json"
README_PATH = Path(__file__).parents[1] / "README.md"


def _problem_from_example(example: dict[str, object]) -> BeamProblem:
    return BeamProblem(
        length_mm=example["length_mm"],
        elastic_modulus_mpa=example["elastic_modulus_mpa"],
        inertia_mm4=example["inertia_mm4"],
        supports=[Support(**support) for support in example["supports"]],
        point_loads=[PointLoad(**load) for load in example["point_loads"]],
        distributed_loads=[DistributedLoad(**load) for load in example["distributed_loads"]],
    )


def test_textbook_examples_run_with_documented_methods_reactions_and_deflections():
    assert "77 项" not in README_PATH.read_text(encoding="utf-8")
    examples = json.loads(EXAMPLES_PATH.read_text(encoding="utf-8"))["examples"]

    assert {example["id"] for example in examples} == {
        "midspan_point_load",
        "partial_uniform_load",
        "cantilever_tip_load",
    }
    for example in examples:
        result = solve_textbook_beam(_problem_from_example(example))
        expected = example["expected"]

        assert result.method == expected["method"]
        assert result.classification.category == expected["classification"]
        assert [reaction.vertical_n for reaction in result.reactions] == pytest.approx(
            expected["vertical_reactions_n"], abs=1e-6
        )
        if example["id"] == "cantilever_tip_load":
            fixed_reaction = next(
                reaction
                for reaction in result.reactions
                if reaction.support_kind == "fixed"
            )
            assert fixed_reaction.moment_n_mm == pytest.approx(
                expected["fixed_reaction_moment_n_mm"], abs=1e-6
            )
        assert result.max_deflection_mm == pytest.approx(
            expected["max_deflection_mm"], abs=1e-9
        )
        assert result.max_deflection_position_mm == pytest.approx(
            expected["max_deflection_position_mm"], abs=1e-6
        )
