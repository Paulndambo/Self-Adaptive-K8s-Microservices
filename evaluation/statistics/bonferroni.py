from __future__ import annotations


def bonferroni_alpha(alpha: float, comparisons: int) -> float:
    if comparisons <= 0:
        raise ValueError("comparisons must be positive")
    return alpha / comparisons


def bonferroni_significant(p_values: list[float], alpha: float) -> list[bool]:
    corrected_alpha = bonferroni_alpha(alpha, len(p_values))
    return [p_value <= corrected_alpha for p_value in p_values]
