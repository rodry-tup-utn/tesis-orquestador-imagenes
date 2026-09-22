#!/usr/bin/env python3
"""Verificacion mecanica del Capitulo 6 a partir de los datos crudos del panel.

Recibe los votos individuales de los 17 evaluadores sobre las 50 ordenes del
experimento (Tabla 32 del Anexo V) y la salida del motor en las Fases 0 y 4
(Tabla 33 del Anexo V), y recalcula, sin depender de ninguna cifra publicada
en el texto:

  1. El patron de referencia (moda de los 17 votos; empate -> nivel mas severo)
     y su coincidencia con la columna "Patron" de la Tabla 32.
  2. La matriz de confusion y la coincidencia exacta del motor contra ese
     patron, en la Fase 0 (medicion ciega) y en la Fase 4 (calibrada).
  3. El kappa de Fleiss entre los 17 evaluadores.
  4. La concordancia de cada uno de E02, E09 y E12 (a) contra la salida del
     motor en Fase 4 y (b) contra el patron de referencia reconstruido sin
     ellos tres (panel de 14), que es la comparacion que la seccion 6.9
     de la tesis llama "patron de referencia previo".
  5. La prueba de exclusion sistematica: recalcula el patron y la coincidencia
     excluyendo un evaluador a la vez (17 iteraciones) y reporta el rango.

No usa ningun dato fuera de los dos CSV de entrada. Sirve para que cualquier
lector reproduzca, con un solo comando, las cifras de las secciones 6.7 a 6.9.

Uso:
    python benchmark/verify_chapter6_panel.py
    python benchmark/verify_chapter6_panel.py --panel otro.csv --motor otro2.csv
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stats import LEVELS, SEVERITY, fleiss_kappa, reference_label  # solo funciones puras; sin dependencias del backend

RATERS = [f"E{i:02d}" for i in range(1, 18)]

def canon(v: str) -> str:
    key = "".join(c for c in unicodedata.normalize("NFD", v.strip().upper()) if unicodedata.category(c) != "Mn")
    return {"C": "Crítico", "U": "Urgente", "P": "Prioritario", "R": "Rutina"}[key]


def load_panel(path: str):
    rows = list(csv.DictReader(open(path, encoding="utf-8-sig")))
    orders, votes, published_pattern = [], [], []
    for r in rows:
        orders.append(r["Orden"])
        votes.append([canon(r[c]) for c in RATERS])
        published_pattern.append(canon(r["Patrón"]))
    return orders, votes, published_pattern


def load_motor(path: str):
    rows = list(csv.DictReader(open(path, encoding="utf-8-sig")))
    return {r["Orden"]: (r["Patrón de referencia"], r["Fase 0 · nivel"], r["Fase 4 · nivel"]) for r in rows}


def confusion(ref: list[str], pred: list[str]):
    m = {a: {b: 0 for b in LEVELS} for a in LEVELS}
    for r, p in zip(ref, pred):
        m[r][p] += 1
    return m


def print_confusion(title: str, m: dict):
    print(f"\n{title} (filas = patrón; columnas = motor)")
    print("        " + "  ".join(f"{l:11s}" for l in LEVELS))
    for a in LEVELS:
        print(f"{a:8s}" + "  ".join(f"{m[a][b]:11d}" for b in LEVELS))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--panel", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "panel_votos_50_ordenes.csv"))
    ap.add_argument("--motor", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "motor_salida_fases_50_ordenes.csv"))
    a = ap.parse_args()

    orders, votes, published_pattern = load_panel(a.panel)
    motor = load_motor(a.motor)
    n = len(orders)
    assert n == 50, f"se esperaban 50 órdenes, se leyeron {n}"

    # 1) Patrón de referencia (los 17) vs. columna publicada
    recon17, ties17 = zip(*(reference_label(v) for v in votes))
    mism = [o for o, r, p in zip(orders, recon17, published_pattern) if r != p]
    print("=== 1) Reconstrucción del patrón de referencia (17 evaluadores) ===")
    print(f"Coincide con la columna «Patrón» publicada en {n - len(mism)}/{n} órdenes.")
    if mism:
        print("  Discrepancias:", ", ".join(mism))

    # 2) Motor vs. patrón, Fase 0 y Fase 4
    fase0 = [motor[o][1] for o in orders]
    fase4 = [motor[o][2] for o in orders]
    ref_pub = list(published_pattern)
    for fase, pred in (("Fase 0 (medición ciega)", fase0), ("Fase 4 (calibrada)", fase4)):
        exact = sum(r == p for r, p in zip(ref_pub, pred))
        print(f"\n=== 2) Motor vs. patrón — {fase} ===")
        print(f"Coincidencia exacta: {exact}/{n} = {100*exact/n:.1f} %")
        print_confusion(fase, confusion(ref_pub, pred))

    # 3) Kappa de Fleiss entre los 17
    kf = fleiss_kappa(votes)
    print(f"\n=== 3) Acuerdo entre evaluadores ===\nκ de Fleiss (17 evaluadores): {kf:.4f}")

    # 4) E02, E09, E12: concordancia con el motor (Fase 4) y con el patrón de 14
    idx = {r: i for i, r in enumerate(RATERS)}
    added = ["E02", "E09", "E12"]
    votes14 = [[v[idx[r]] for r in RATERS if r not in added] for v in votes]
    ref14, _ = zip(*(reference_label(v) for v in votes14))
    print("\n=== 4) Evaluadores incorporados en Fase 4 ===")
    for r in added:
        col = [v[idx[r]] for v in votes]
        vs_motor = sum(c == p for c, p in zip(col, fase4))
        vs_pat14 = sum(c == p for c, p in zip(col, ref14))
        print(f"  {r}: vs. motor (Fase 4) {vs_motor}/{n} = {100*vs_motor/n:.1f} %   "
              f"vs. patrón de 14 (sin E02/E09/E12) {vs_pat14}/{n} = {100*vs_pat14/n:.1f} %")

    # 5) Exclusión sistemática: 17 iteraciones, dejando afuera un evaluador cada vez
    print("\n=== 5) Exclusión sistemática (leave-one-out, 17 iteraciones) ===")
    exacts = []
    crit_fn_counts = []
    for excl in RATERS:
        v_loo = [[v[idx[r]] for r in RATERS if r != excl] for v in votes]
        ref_loo, _ = zip(*(reference_label(v) for v in v_loo))
        exact = sum(r == p for r, p in zip(ref_loo, fase4))
        exacts.append(exact)
        crit_fn = sum(1 for r, p in zip(ref_loo, fase4) if r == "Crítico" and p != "Crítico")
        crit_fn_counts.append(crit_fn)
    print(f"Coincidencia exacta motor-Fase4 vs. patrón (excluyendo 1 evaluador por vez): "
          f"mínimo {min(exacts)}/{n} ({100*min(exacts)/n:.1f} %), máximo {max(exacts)}/{n} ({100*max(exacts)/n:.1f} %)")
    print(f"Falsos negativos críticos por iteración: mínimo {min(crit_fn_counts)}, máximo {max(crit_fn_counts)} "
          f"(constante en las 17 iteraciones: {'sí' if len(set(crit_fn_counts))==1 else 'no'})")

    ok = not mism
    print(f"\n{'VERIFICACIÓN OK' if ok else 'REVISAR: el patrón reconstruido no coincide con el publicado'}: "
          f"todas las cifras de esta sección se derivan únicamente de {os.path.basename(a.panel)} y {os.path.basename(a.motor)}.")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
