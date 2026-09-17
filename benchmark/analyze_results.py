#!/usr/bin/env python3
"""Análisis estadístico completo sobre los CSVs de benchmark existentes.

Lee los resultados de ejecuciones anteriores en benchmark/results/ y computa:
    - T_proc, T_n8n, T_server: media, mediana, P95, min, max, std
    - TDCC: ídem
    - Verificación de RNF-01: T_proc P95 < 500 ms
    - Verificación de RNF-02: tasa de éxito de notificaciones >= 99 %

No requiere Docker ni el sistema en ejecución. Opera únicamente sobre los
archivos CSV ya generados.

Uso:
    python benchmark/analyze_results.py
    python benchmark/analyze_results.py --tproc results/results_tproc_2026-08-16.csv
                                        --tdcc  results/results_tdcc_2026-08-13.csv
"""
import argparse
import csv
import os
import statistics
import sys

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")

RNF_01_P95_THRESHOLD_MS = 500.0   # RNF-01: P95 de T_proc < 500 ms
RNF_02_SUCCESS_RATE = 0.99         # RNF-02: tasa de éxito de notificaciones >= 99 %


def _find_latest(prefix: str):
    """Retorna el CSV más reciente con el prefijo dado en RESULTS_DIR."""
    candidates = [
        f for f in os.listdir(RESULTS_DIR)
        if f.startswith(prefix) and f.endswith(".csv")
    ]
    return os.path.join(RESULTS_DIR, sorted(candidates)[-1]) if candidates else None


def _read_csv(path: str) -> list:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _percentile95(values: list) -> float:
    """P95 usando statistics.quantiles (método 'exclusive', Python 3.8+)."""
    if len(values) < 2:
        return values[0] if values else 0.0
    return statistics.quantiles(values, n=100)[94]


def _print_stats(label: str, values: list) -> None:
    if not values:
        print(f"  {label}: sin datos")
        return
    p95 = _percentile95(values)
    p95_flag = ""
    if label == "T_proc":
        if p95 < RNF_01_P95_THRESHOLD_MS:
            p95_flag = f"  -> RNF-01 VERIFICADO (P95={p95:.1f} ms < {RNF_01_P95_THRESHOLD_MS:.0f} ms)"
        else:
            p95_flag = f"  -> RNF-01 FALLIDO (P95={p95:.1f} ms >= {RNF_01_P95_THRESHOLD_MS:.0f} ms)"
    print(
        f"  {label}: n={len(values)}  "
        f"media={statistics.mean(values):.2f}  mediana={statistics.median(values):.2f}  "
        f"P95={p95:.2f}  min={min(values):.2f}  max={max(values):.2f}  "
        f"std={statistics.pstdev(values):.2f}  (ms)"
    )
    if p95_flag:
        print(p95_flag)


def analyze_tproc(path: str) -> None:
    print(f"\n{'='*60}")
    print(f"  ANALISIS T_PROC  --  {os.path.basename(path)}")
    print(f"{'='*60}")

    rows = _read_csv(path)
    for key in ("T_proc", "T_n8n", "T_server"):
        vals = [float(r[key]) for r in rows if r.get(key) not in (None, "")]
        _print_stats(key, vals)

    # Tasa de exito HTTP
    statuses = [r.get("status", "") for r in rows]
    ok = sum(1 for s in statuses if s == "200")
    rate = ok / len(statuses) if statuses else 0
    print(f"\n  Ciclos totales: {len(rows)}  |  HTTP 200: {ok}  |  Tasa exito: {rate*100:.1f}%")
    if rate >= RNF_02_SUCCESS_RATE:
        print(f"  -> RNF-02 DISPONIBILIDAD: tasa de procesamiento {rate*100:.1f}% >= {RNF_02_SUCCESS_RATE*100:.0f}%")
    else:
        print(f"  -> RNF-02: tasa {rate*100:.1f}% < {RNF_02_SUCCESS_RATE*100:.0f}%")

    # Nota sobre el cold-start
    tproc_vals = [float(r["T_proc"]) for r in rows if r.get("T_proc") not in (None, "")]
    if tproc_vals and tproc_vals[0] == max(tproc_vals):
        print(
            f"\n  Nota: el ciclo T-001 (T_proc={tproc_vals[0]:.1f} ms) es el arranque en frio "
            f"(cold-start). Los {len(tproc_vals)-1} ciclos restantes tienen "
            f"T_proc max={sorted(tproc_vals)[:-1][-1]:.1f} ms."
        )


def analyze_tdcc(path: str) -> None:
    print(f"\n{'='*60}")
    print(f"  ANALISIS TDCC  --  {os.path.basename(path)}")
    print(f"{'='*60}")

    rows = _read_csv(path)
    tdcc_vals = [float(r["TDCC"]) for r in rows if r.get("TDCC") not in (None, "")]
    _print_stats("TDCC", tdcc_vals)

    # Tasa de exito de notificaciones (RNF-02 parcial)
    success = sum(1 for r in rows if r.get("status") == "SUCCESS")
    rate = success / len(rows) if rows else 0
    print(f"\n  Ordenes criticas: {len(rows)}  |  Notificadas: {success}  |  Tasa: {rate*100:.1f}%")
    if rate >= RNF_02_SUCCESS_RATE:
        print(f"  -> RNF-02 NOTIFICACIONES CRITICAS: {rate*100:.1f}% >= {RNF_02_SUCCESS_RATE*100:.0f}%")
    else:
        print(f"  -> RNF-02: tasa {rate*100:.1f}% < {RNF_02_SUCCESS_RATE*100:.0f}%")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tproc", default=None, help="CSV de T_proc (default: mas reciente en results/)")
    parser.add_argument("--tdcc",  default=None, help="CSV de TDCC  (default: mas reciente en results/)")
    args = parser.parse_args()

    tproc_path = args.tproc or _find_latest("results_tproc")
    tdcc_path  = args.tdcc  or _find_latest("results_tdcc")

    print("\n========================================")
    print("  REPORTE DE BENCHMARKS -- ESCENARIO B  ")
    print("  Verificacion de RNF-01 y RNF-02       ")
    print("========================================")

    if tproc_path and os.path.exists(tproc_path):
        analyze_tproc(tproc_path)
    else:
        print("\n[AVISO] No se encontro CSV de T_proc. Ejecuta benchmark/tproc.py primero.")

    if tdcc_path and os.path.exists(tdcc_path):
        analyze_tdcc(tdcc_path)
    else:
        print("\n[AVISO] No se encontro CSV de TDCC. Ejecuta benchmark/tdcc.py primero.")

    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
