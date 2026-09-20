#!/usr/bin/env python3
"""Medicion del tiempo de respuesta de la API en su limite de red (RNF-01).

RNF-01 exige un tiempo de respuesta de la API inferior a 500 ms en el P95.
T_proc y T_server (Capitulo 5) no equivalen a esa magnitud: la primera incluye
el ciclo de n8n y la segunda excluye la red y el framework HTTP. Este guion
mide el tiempo que percibe un cliente HTTP, desde que envia la peticion hasta
que recibe la respuesta completa, sobre los endpoints de lectura que usa el
tablero.

Precondiciones:
    - Contenedores levantados y con ordenes cargadas (por ejemplo, tras un ciclo
      de benchmark/tproc.py).
    - AUTH_USERNAME y AUTH_PASSWORD definidos en .env o en el entorno.

Uso:
    python benchmark/api_latency.py
    python benchmark/api_latency.py --requests 200 --backend http://localhost:8000

Salida: CSV en benchmark/results/ con una fila por peticion y un resumen por
endpoint (n, media, mediana, P95, max). El P95 usa statistics.quantiles con el
metodo 'inclusive', apropiado para muestras finitas.
"""
import argparse
import csv
import json
import os
import statistics
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

ENDPOINTS = ["/orders?limit=10&offset=0", "/orders/stats", "/orders/notifications"]


def login(backend: str, user: str, password: str) -> str:
    body = json.dumps({"username": user, "password": password}).encode("utf-8")
    req = urllib.request.Request(
        f"{backend}/auth/login", data=body,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())["access_token"]


def timed_get(url: str, token: str):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp.read()
            status = resp.status
    except urllib.error.HTTPError as exc:
        status = exc.code
    return (time.perf_counter() - t0) * 1000.0, status


def p95(values):
    return statistics.quantiles(values, n=100, method="inclusive")[94] if len(values) >= 2 else values[0]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", default=os.environ.get("BACKEND_URL", "http://localhost:8000"))
    parser.add_argument("--requests", type=int, default=200, help="peticiones por endpoint")
    parser.add_argument("--warmup", type=int, default=10, help="peticiones de calentamiento descartadas")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    env = common.load_env()
    user = os.environ.get("AUTH_USERNAME") or env.get("AUTH_USERNAME", "admin")
    password = os.environ.get("AUTH_PASSWORD") or env.get("AUTH_PASSWORD", "")
    if not password:
        sys.exit("Falta AUTH_PASSWORD (entorno o .env).")

    token = login(args.backend, user, password)
    stamp = time.strftime("%Y-%m-%d")
    out = args.out or os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", f"results_api_latency_{stamp}.csv")
    os.makedirs(os.path.dirname(out), exist_ok=True)

    rows, summary = [], []
    for path in ENDPOINTS:
        url = f"{args.backend}{path}"
        for _ in range(args.warmup):
            timed_get(url, token)
        values, errors = [], 0
        for i in range(1, args.requests + 1):
            ms, status = timed_get(url, token)
            rows.append({"endpoint": path, "n": i, "status": status, "latency_ms": round(ms, 3)})
            if status == 200:
                values.append(ms)
            else:
                errors += 1
        if values:
            summary.append((path, len(values), errors, statistics.mean(values),
                            statistics.median(values), p95(values), max(values)))

    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["endpoint", "n", "status", "latency_ms"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nCSV guardado en {out}\n--- Tiempo de respuesta en el limite de la API (ms) ---")
    for path, n, err, mean, med, q95, mx in summary:
        flag = "cumple" if q95 < 500 else "NO cumple"
        print(f"{path:32s} n={n} err={err} media={mean:.2f} mediana={med:.2f} P95={q95:.2f} max={mx:.2f}  -> RNF-01 {flag}")
    print("\nInterpretacion: la medicion vale para las condiciones de carga secuencial, un solo cliente"
          " y el volumen de datos presente; no caracteriza concurrencia (recomendacion 3 del Capitulo 9).")


if __name__ == "__main__":
    main()
