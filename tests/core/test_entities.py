import pytest

from tests.factories import FileProgressSummaryFactory, ProgressFactory


@pytest.mark.parametrize(
    "translated, total, expected_percentage",
    [
        (0, 0, 0.0),  # Edge case: avoid ZeroDivisionError
        (50, 100, 50.0),  # Normal case
        (1, 3, 33.33),  # Precision rounding check
        (10, 10, 100.0),  # Complete progress
    ],
)
def test_progress_percentage(translated: int, total: int, expected_percentage: float) -> None:
    """Ensure percentage calculates correctly and handles division by zero."""
    progress = ProgressFactory.build(translated=translated, total=total)
    assert progress.percentage == expected_percentage


@pytest.mark.parametrize(
    "total, expected_is_empty",
    [
        (0, True),
        (10, False),
    ],
)
def test_progress_is_empty(total: int, expected_is_empty: bool) -> None:
    """Ensure is_empty correctly reflects the total count."""
    progress = ProgressFactory.build(total=total)
    assert progress.is_empty is expected_is_empty


@pytest.mark.parametrize(
    "total_value, expected_is_empty",
    [
        (0, True),
        (1, False),
    ],
)
def test_file_progress_summary_is_empty(total_value: int, expected_is_empty: bool) -> None:
    """Ensure is_empty correctly reflects the total count."""

    total_progress = ProgressFactory.build(total=total_value)
    summary = FileProgressSummaryFactory.build(total=total_progress)

    assert summary.is_empty is expected_is_empty


def test_progress_addition() -> None:
    """Ensure two Progress objects can be added together correctly."""
    p1 = ProgressFactory.build(translated=10, total=20)
    p2 = ProgressFactory.build(translated=5, total=15)

    result = p1 + p2

    assert result.translated == 15
    assert result.total == 35


def test_progress_addition_type_error() -> None:
    """Ensure adding a non-Progress object returns NotImplemented."""
    p1 = ProgressFactory.build(translated=10, total=20)

    with pytest.raises(TypeError):
        _ = p1 + 5
