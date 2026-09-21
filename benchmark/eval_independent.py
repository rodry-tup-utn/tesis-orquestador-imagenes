#!/usr/bin/env python3
"""Validacion predictiva independiente del motor de triaje.

Compara la clasificacion del motor con un patron de referencia humano obtenido
ANTES de ejecutar el motor, sobre ordenes que los autores no usaron para calibrar.
Sustituye la prueba de regresion (validate_motor.py), cuyas etiquetas derivan de
la misma especificacion de reglas y por eso no es una validacion predictiva.

Entrada (CSV UTF-8, una fila por orden). Columnas:
    id, description, modality, origin_service, patient_location, diagnosis,
    is_urgent (0/1), study_setting, observations (opcional),
    rater_1 ... rater_K  (Critico | Urgente | Prioritario | Rutina)
Plantilla: benchmark/templates/validacion_independiente_PLANTILLA.csv

Procedimiento y criterios: PROTOCOLOS_EVIDENCIA_ADICIONAL.md (seccion 1).

Uso:
    python benchmark/eval_independent.py --orders mis_ordenes.csv [--config calibrada_fase4]

Salida: informe por consola, CSV por orden y resumen en Markdown en
benchmark/results/. Registra el SHA-256 de la configuracion evaluada para
acreditar que no se recalibro tras conocer las etiquetas.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import sys
import time
import unicodedata
from collections import Counter

BENCHMARK_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BENCHMARK_DIR)
import validate_motor as vm  # reutiliza el mismo motor y helpers de la regresion

LEVELS = ["Crítico", "Urgente", "Prioritario", "Rutina"]
SEVERITY = {"Crítico": 4, "Urgente": 3, "Prioritario": 2, "Rutina": 1}


def canon(label: str) -> str:
    key = "".join(c for c in unicodedata.normalize("NFD", str(label).strip().lower())
                  if unicodedata.category(c) != "Mn")
    if key not in vm.PRIORITY_MAP:
        raise ValueError(f"Etiqueta de prioridad no reconocida: {label!r}")
    return vm.PRIORITY_MAP[key]


def reference_label(votes: list[str]) -> tuple[str, bool]:
    """Moda; ante empate, el nivel mas severo (criterio del Capitulo 6)."""
    counts = Counter(votes)
    top = max(counts.values())
    tied = [lvl for lvl, c in counts.items() if c == top]
    return max(tied, key=lambda l: SEVERITY[l]), len(tied) > 1


# ── Estadistica sin dependencias externas ─────────────────────────────────
def _binom_cdf(k: int, n: int, p: float) -> float:
    return sum(math.comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(0, k + 1))


def clopper_pearson(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    def bisect(f, lo=0.0, hi=1.0):
        for _ in range(80):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if f(mid) > 0 else (lo, mid)
        return (lo + hi) / 2
    # cota inferior: P(X >= k | p) = alpha/2 ; cota superior: P(X <= k | p) = alpha/2
    lower = 0.0 if k == 0 else bisect(lambda p: alpha / 2 - (1 - _binom_cdf(k - 1, n, p)))
    upper = 1.0 if k == n else bisect(lambda p: _binom_cdf(k, n, p) - alpha / 2)
    return lower, upper


def binom_sf_ge(k: int, n: int, p: float) -> float:
    """P(X >= k) con X ~ Bin(n, p)."""
    return sum(math.comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(k, n + 1))


def weighted_kappa(a: list[str], b: list[str]) -> float:
    idx = {l: i for i, l in enumerate(LEVELS)}
    n, m = len(a), len(LEVELS)
    obs = [[0.0] * m for _ in range(m)]
    for x, y in zip(a, b):
        obs[idx[x]][idx[y]] += 1
    ra = [sum(obs[i]) for i in range(m)]
    cb = [sum(obs[i][j] for i in range(m)) for j in range(m)]
    w = lambda i, j: 1 - abs(i - j) / (m - 1)
    po = sum(w(i, j) * obs[i][j] for i in range(m) for j in range(m)) / n
    pe = sum(w(i, j) * ra[i] * cb[j] for i in range(m) for j in range(m)) / (n * n)
    return (po - pe) / (1 - pe) if pe != 1 else float("nan")


def fleiss_kappa(rows: list[list[str]]) -> float:
    n_items, n_raters = len(rows), len(rows[0])
    counts = [[r.count(l) for l in LEVELS] for r in rows]
    p_j = [sum(c[j] for c in counts) / (n_items * n_raters) for j in range(len(LEVELS))]
    p_i = [(sum(x * x for x in c) - n_raters) / (n_raters * (n_raters - 1)) for c in counts]
    p_bar, pe = sum(p_i) / n_items, sum(x * x for x in p_j)
    return (p_bar - pe) / (1 - pe) if pe != 1 else float("nan")


def per_level(ref: list[str], pred: list[str]) -> list[dict]:
    out = []
    for lvl in LEVELS:
        tp = sum(r == lvl and p == lvl for r, p in zip(ref, pred))
        fn = sum(r == lvl and p != lvl for r, p in zip(ref, pred))
        fp = sum(r != lvl and p == lvl for r, p in zip(ref, pred))
        tn = len(ref) - tp - fn - fp
        sens = tp / (tp + fn) if tp + fn else float("nan")
        spec = tn / (tn + fp) if tn + fp else float("nan")
        prec = tp / (tp + fp) if tp + fp else float("nan")
        f1 = 2 * prec * sens / (prec + sens) if prec == prec and sens == sens and prec + sens else float("nan")
        out.append({"level": lvl, "support": tp + fn, "sens": sens, "spec": spec, "prec": prec, "f1": f1})
    return out


def parse_bool(v: str) -> bool:
    return str(v).strip().lower() in ("1", "true", "si", "sí", "yes", "y", "t")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--orders", required=True)
    ap.add_argument("--config", default="calibrada_fase4")
    args = ap.parse_args()

    cfg_path = os.path.join(vm.CONFIGS_DIR, f"{args.config}.json")
    raw = open(cfg_path, "rb").read()
    cfg_sha = hashlib.sha256(raw).hexdigest()
    cfg = json.loads(raw.decode("utf-8"))

    with open(args.orders, newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        sys.exit("El CSV no contiene ordenes.")
    rater_cols = sorted(c for c in rows[0] if c.lower().startswith("rater_"))
    if len(rater_cols) < 3:
        sys.exit("Se requieren al menos 3 columnas rater_* (idealmente 5 o mas).")

    ref, pred, votes_all, ties, detail = [], [], [], 0, []
    for r in rows:
        votes = [canon(r[c]) for c in rater_cols]
        label, tied = reference_label(votes)
        ties += tied
        order = {
            "modality": r.get("modality"), "origin_service": r.get("origin_service"),
            "patient_location": r.get("patient_location"), "diagnosis": r.get("diagnosis"),
            "is_urgent": parse_bool(r.get("is_urgent", "0")), "description": r.get("description"),
            "observations": r.get("observations"), "study_setting": r.get("study_setting"),
        }
        p, score, _ = vm.evaluate_order(order, cfg["rules"], cfg["thresholds"])
        ref.append(label); pred.append(p); votes_all.append(votes)
        detail.append({"id": r["id"], "referencia": label, "motor": p, "score": score,
                       "empate": int(tied), "acierta": int(label == p),
                       "distancia": abs(SEVERITY[label] - SEVERITY[p])})

    n = len(rows)
    exact = sum(d["acierta"] for d in detail)
    within1 = sum(d["distancia"] <= 1 for d in detail)
    lo, hi = clopper_pearson(exact, n)
    maj_lvl, maj_n = Counter(ref).most_common(1)[0]
    p_base = maj_n / n
    p_val = binom_sf_ge(exact, n, p_base)
    kw = weighted_kappa(ref, pred)
    kf = fleiss_kappa(votes_all)
    crit_fn = [d["id"] for d in detail if d["referencia"] == "Crítico" and d["motor"] != "Crítico"]
    under = sum(SEVERITY[d["motor"]] < SEVERITY[d["referencia"]] for d in detail)

    lines = []
    P = lines.append
    P("# Validación predictiva independiente del motor de triaje")
    P(f"- Fecha de ejecución: {time.strftime('%Y-%m-%d %H:%M')}")
    P(f"- Configuración: `{args.config}` — SHA-256 `{cfg_sha}`")
    P(f"- Órdenes: {n} · evaluadores por orden: {len(rater_cols)} · empates resueltos al nivel más severo: {ties}")
    P(f"- Distribución del patrón: " + ", ".join(f"{l}={Counter(ref)[l]}" for l in LEVELS))
    P("")
    P(f"| Métrica | Valor |\n|---|---|")
    P(f"| Coincidencia exacta | {exact}/{n} = {100*exact/n:.1f} % (IC 95 % Clopper-Pearson {100*lo:.1f}–{100*hi:.1f} %) |")
    P(f"| Dentro de un nivel | {within1}/{n} = {100*within1/n:.1f} % |")
    P(f"| Línea de base (clase mayoritaria «{maj_lvl}») | {100*p_base:.1f} % · p exacto unilateral = {p_val:.4g} |")
    P(f"| κ ponderado lineal motor–patrón | {kw:.3f} |")
    P(f"| κ de Fleiss entre evaluadores | {kf:.3f} |")
    P(f"| Subestimaciones (motor < patrón) | {under}/{n} |")
    P(f"| Falsos negativos en nivel Crítico | {len(crit_fn)} ({', '.join(crit_fn) or '—'}) |")
    P("")
    P("| Nivel | n patrón | Sensibilidad | Especificidad | Precisión | F1 |\n|---|---|---|---|---|---|")
    for m in per_level(ref, pred):
        f = lambda x: "—" if x != x else f"{x:.3f}"
        P(f"| {m['level']} | {m['support']} | {f(m['sens'])} | {f(m['spec'])} | {f(m['prec'])} | {f(m['f1'])} |")
    P("")
    P("Matriz de confusión (filas = patrón; columnas = motor)\n")
    P("| | " + " | ".join(LEVELS) + " |\n|---|" + "---|" * len(LEVELS))
    for a in LEVELS:
        P(f"| **{a}** | " + " | ".join(str(sum(r == a and p == b for r, p in zip(ref, pred))) for b in LEVELS) + " |")
    P("")
    P("> Reportar este resultado tal como salga, sin recalibrar el motor y volver a medir sobre el mismo conjunto.")

    print("\n".join(lines))
    os.makedirs(os.path.join(BENCHMARK_DIR, "results"), exist_ok=True)
    stamp = time.strftime("%Y-%m-%d")
    base = os.path.join(BENCHMARK_DIR, "results", f"results_independent_validation_{stamp}")
    with open(base + ".csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(detail[0].keys()))
        w.writeheader(); w.writerows(detail)
    with open(base + ".md", "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"\nGuardado: {base}.csv y {base}.md")


if __name__ == "__main__":
    main()
