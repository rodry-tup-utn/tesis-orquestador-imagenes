#!/usr/bin/env python3
"""Funciones estadísticas puras compartidas por los verificadores del benchmark.

Este módulo no importa el backend, FastAPI, SQLModel ni la configuración del
motor. Su objetivo es que los cálculos del capítulo 6 puedan reproducirse en
un entorno mínimo usando únicamente los CSV de evidencia incluidos en la
entrega.
"""
from __future__ import annotations

import math
from collections import Counter

LEVELS = ["Crítico", "Urgente", "Prioritario", "Rutina"]
SEVERITY = {"Crítico": 4, "Urgente": 3, "Prioritario": 2, "Rutina": 1}


def reference_label(votes: list[str]) -> tuple[str, bool]:
    """Moda; ante empate, selecciona el nivel más severo."""
    if not votes:
        raise ValueError("Se requiere al menos un voto para reconstruir el patrón")
    counts = Counter(votes)
    top = max(counts.values())
    tied = [level for level, count in counts.items() if count == top]
    return max(tied, key=lambda level: SEVERITY[level]), len(tied) > 1


def fleiss_kappa(rows: list[list[str]]) -> float:
    """Calcula el kappa de Fleiss sin dependencias externas."""
    if not rows or not rows[0]:
        raise ValueError("Se requieren observaciones y evaluadores")
    n_items, n_raters = len(rows), len(rows[0])
    if any(len(row) != n_raters for row in rows):
        raise ValueError("Todas las observaciones deben tener el mismo número de evaluadores")
    if n_raters < 2:
        raise ValueError("Fleiss kappa requiere al menos 2 evaluadores")

    counts = [[row.count(level) for level in LEVELS] for row in rows]
    p_j = [
        sum(counts[i][j] for i in range(n_items)) / (n_items * n_raters)
        for j in range(len(LEVELS))
    ]
    p_i = [
        (sum(x * x for x in count_row) - n_raters)
        / (n_raters * (n_raters - 1))
        for count_row in counts
    ]
    p_bar = sum(p_i) / n_items
    p_e = sum(p * p for p in p_j)
    return (p_bar - p_e) / (1 - p_e) if p_e != 1 else float("nan")


def clopper_pearson(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Intervalo exacto binomial por inversión numérica de la CDF."""
    if not 0 <= k <= n or n <= 0:
        raise ValueError("Debe cumplirse 0 <= k <= n y n > 0")

    def binom_cdf(x: int, p: float) -> float:
        return sum(math.comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(x + 1))

    def bisect(f, lo: float = 0.0, hi: float = 1.0) -> float:
        for _ in range(80):
            mid = (lo + hi) / 2
            if f(mid) > 0:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2

    lower = 0.0 if k == 0 else bisect(lambda p: alpha / 2 - (1 - binom_cdf(k - 1, p)))
    upper = 1.0 if k == n else bisect(lambda p: binom_cdf(k, p) - alpha / 2)
    return lower, upper
