from pathlib import Path

from cavity_transport.artifacts import ensure_output_tree
from cavity_transport.experiments import RunContext, _render_reference_comparison


def test_missing_private_reference_does_not_block_public_numerics(
    tmp_path: Path,
) -> None:
    context = RunContext(
        workspace=tmp_path / "code",
        output_root=tmp_path / "outputs",
        config={},
        profile_name="quick",
        profile={},
        paths=ensure_output_tree(tmp_path / "outputs"),
    )

    result = _render_reference_comparison(
        context,
        "not-published.png",
        tmp_path / "generated.png",
        "comparison.png",
    )

    assert result is None
    assert not (tmp_path / "outputs" / "comparisons" / "comparison.png").exists()
