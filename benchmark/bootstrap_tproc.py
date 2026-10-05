"""Intervalos de confianza por bootstrap para T_proc (sección 5.5 de la tesis).

Requiere numpy, que no forma parte de server/requirements.lock:
    pip install numpy

Uso (desde la raíz del repositorio):
    python benchmark/bootstrap_tproc.py
    python benchmark/bootstrap_tproc.py --csv benchmark/results/results_tproc_2026-08-16.csv

Convención declarada en la tesis:
  - B = 10.000 remuestras con reemplazo, numpy.random.default_rng(42).
  - P95 de cada remuestra con statistics.quantiles(..., n=100)[94] (método exclusivo),
    el mismo que usa benchmark/analyze_results.py para el P95 de la serie.
  - Intervalo por el método de percentiles (2,5 y 97,5) de la distribución remuestreada.
"""
import argparse
import csv
import statistics

import numpy as np


def p95_exclusive(values):
    return statistics.quantiles(list(values), n=100)[94]


def bootstrap(x, seed=42, b=10_000):
    rng = np.random.default_rng(seed)
    n = len(x)
    means, p95s = [], []
    for _ in range(b):
        s = x[rng.integers(0, n, n)]
        means.append(s.mean())
        p95s.append(p95_exclusive(s))
    return np.percentile(means, [2.5, 97.5]), np.percentile(p95s, [2.5, 97.5])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--csv', default='benchmark/results/results_tproc_2026-08-16.csv')
    args = ap.parse_args()
    with open(args.csv, newline='', encoding='utf-8') as f:
        rows = [r for r in csv.DictReader(f) if r['status'] == '200']
    x = np.array([float(r['T_proc']) for r in rows])
    ic_mu, ic_p95 = bootstrap(x)
    print(f'n = {len(x)} | media = {x.mean():.2f} ms | P95 (exclusivo) = {p95_exclusive(x):.2f} ms')
    print(f'IC95% media  = [{ic_mu[0]:.2f}; {ic_mu[1]:.2f}] ms')
    print(f'IC95% P95    = [{ic_p95[0]:.2f}; {ic_p95[1]:.2f}] ms')
    est = x[1:]  # sin el ciclo T-001 (arranque en frío)
    _, ic_p95_est = bootstrap(est)
    print(f'IC95% P95 sin T-001 = [{ic_p95_est[0]:.2f}; {ic_p95_est[1]:.2f}] ms')
    lin = []
    rng = np.random.default_rng(42)
    for _ in range(10_000):
        lin.append(np.percentile(x[rng.integers(0, len(x), len(x))], 95))
    print(f'(referencia) IC95% P95 con interpolación lineal = [{np.percentile(lin, 2.5):.2f}; {np.percentile(lin, 97.5):.2f}] ms')


if __name__ == '__main__':
    main()
