#!/usr/bin/env python3
"""Suite de test de carga concurrente — Prioridad 1 del Plan de Mejora.

Ejecuta 5 niveles de concurrencia (1, 5, 10, 25, 50 clientes) con 100 solicitudes
por nivel y captura P50/P95/P99, tasa de error, throughput y métricas de recursos
Docker (CPU/RAM). Genera datos crudos por nivel y una tabla consolidada.

Evidencia generada:
  benchmark/results/load_suite/raw/load_Nc_YYYY-MM-DD.csv   (por nivel)
  benchmark/results/load_suite/results/load_consolidated_YYYY-MM-DD.json
  benchmark/results/load_suite/results/load_consolidated_YYYY-MM-DD.md  (tabla para tesis)

Uso:
    python benchmark/run_load_suite.py
    python benchmark/run_load_suite.py --clients 1 5 10 --requests 200
    python benchmark/run_load_suite.py --skip-docker-stats   # si no hay acceso a docker stats
"""
from __future__ import annotations
import argparse
import csv
import json
import os
import statistics
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_RAW = os.path.join(BASE_DIR, "results", "load_suite", "raw")
RESULTS_DIR = os.path.join(BASE_DIR, "results", "load_suite", "results")
ENDPOINTS = ["/orders?limit=10&offset=0", "/orders/stats", "/orders/notifications"]

DEFAULT_LEVELS = [1, 5, 10, 25, 50]
DEFAULT_REQUESTS = 100


# ── Helpers ───────────────────────────────────────────────────────────────────

def login(base: str, user: str, pwd: str) -> str:
    body = json.dumps({"username": user, "password": pwd}).encode()
    req = urllib.request.Request(
        f"{base}/auth/login", data=body,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())["access_token"]


def worker(base: str, token: str, n_requests: int, out: list, lock: threading.Lock, idx: int):
    """Ejecuta n_requests distribuidos entre endpoints ciclicamente."""
    for i in range(n_requests):
        path = ENDPOINTS[(idx + i) % len(ENDPOINTS)]
        t0 = time.perf_counter()
        status = 0
        try:
            req = urllib.request.Request(
                base + path, headers={"Authorization": f"Bearer {token}"}
            )
            with urllib.request.urlopen(req, timeout=15) as r:
                r.read()
                status = r.status
        except urllib.error.HTTPError as e:
            status = e.code
        except Exception:
            status = 0
        ms = (time.perf_counter() - t0) * 1000
        with lock:
            out.append((time.time(), path, status, round(ms, 3)))


def pct(values: list, q: int) -> float:
    if not values:
        return float("nan")
    if len(values) < 2:
        return values[0]
    return statistics.quantiles(values, n=100, method="inclusive")[q - 1]


def get_docker_stats(service: str = "backend") -> dict:
    """Captura CPU y RAM del servicio via docker stats --no-stream."""
    try:
        result = subprocess.run(
            ["docker", "stats", "--no-stream", "--format",
             "{{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}", service],
            capture_output=True, text=True, timeout=10,
        )
        for line in result.stdout.splitlines():
            if service in line or "fastapi" in line.lower() or "backend" in line.lower():
                parts = line.split("\t")
                if len(parts) >= 3:
                    return {"cpu_perc": parts[1].strip(), "mem_usage": parts[2].strip()}
    except Exception:
        pass
    return {"cpu_perc": "N/D", "mem_usage": "N/D"}


def run_level(base: str, token: str, n_clients: int, n_requests: int,
              stamp: str, skip_docker: bool) -> dict:
    """Ejecuta un nivel de concurrencia y devuelve métricas."""
    print(f"\n  ▶ Nivel {n_clients} clientes × {n_requests} req/cliente "
          f"= {n_clients * n_requests} solicitudes totales...")

    out: list = []
    lock = threading.Lock()

    # Warmup de 5 req por cliente (descartar)
    warmup_threads = [
        threading.Thread(target=worker, args=(base, token, 5, [], threading.Lock(), i))
        for i in range(min(n_clients, 3))
    ]
    [t.start() for t in warmup_threads]
    [t.join() for t in warmup_threads]

    # Estadísticas Docker previas
    docker_pre = {} if skip_docker else get_docker_stats()

    t_start = time.time()
    threads = [
        threading.Thread(target=worker, args=(base, token, n_requests, out, lock, i))
        for i in range(n_clients)
    ]
    [t.start() for t in threads]
    [t.join() for t in threads]
    elapsed = time.time() - t_start

    # Estadísticas Docker posteriores
    docker_post = {} if skip_docker else get_docker_stats()

    # Guardar CSV crudo
    os.makedirs(RESULTS_RAW, exist_ok=True)
    csv_path = os.path.join(RESULTS_RAW, f"load_{n_clients}c_{stamp}.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ts", "endpoint", "status", "latency_ms"])
        w.writerows(out)

    # Calcular métricas
    ok = [r for r in out if r[2] == 200]
    err = [r for r in out if r[2] != 200]
    latencies_ok = [r[3] for r in ok]

    metrics: dict = {
        "clients": n_clients,
        "total_requests": len(out),
        "successful": len(ok),
        "failed": len(err),
        "error_rate_pct": round(100 * len(err) / len(out), 3) if out else 0,
        "elapsed_s": round(elapsed, 2),
        "throughput_rps": round(len(out) / elapsed, 2) if elapsed > 0 else 0,
        "csv_raw": csv_path,
        "docker_cpu_post": docker_post.get("cpu_perc", "N/D"),
        "docker_mem_post": docker_post.get("mem_usage", "N/D"),
    }

    if latencies_ok:
        metrics.update({
            "p50_ms": round(pct(latencies_ok, 50), 2),
            "p95_ms": round(pct(latencies_ok, 95), 2),
            "p99_ms": round(pct(latencies_ok, 99), 2),
            "mean_ms": round(statistics.mean(latencies_ok), 2),
            "median_ms": round(statistics.median(latencies_ok), 2),
            "min_ms": round(min(latencies_ok), 2),
            "max_ms": round(max(latencies_ok), 2),
            "stdev_ms": round(statistics.stdev(latencies_ok), 2) if len(latencies_ok) > 1 else 0,
            "rnf01_p95_cumple": pct(latencies_ok, 95) < 500,
        })
    else:
        metrics.update({
            "p50_ms": "N/D", "p95_ms": "N/D", "p99_ms": "N/D",
            "mean_ms": "N/D", "median_ms": "N/D",
            "min_ms": "N/D", "max_ms": "N/D", "stdev_ms": "N/D",
            "rnf01_p95_cumple": False,
        })

    # Por endpoint
    ep_metrics = {}
    for ep in ENDPOINTS:
        v = [r[3] for r in out if r[1] == ep and r[2] == 200]
        ep_metrics[ep] = {
            "n": len(v),
            "p50": round(pct(v, 50), 2) if v else "N/D",
            "p95": round(pct(v, 95), 2) if v else "N/D",
            "p99": round(pct(v, 99), 2) if v else "N/D",
        }
    metrics["by_endpoint"] = ep_metrics

    cumple = "✓ CUMPLE" if metrics.get("rnf01_p95_cumple") else "✗ NO CUMPLE"
    print(f"     total={len(out)} ok={len(ok)} err={len(err)} "
          f"tput={metrics['throughput_rps']}req/s "
          f"P50={metrics.get('p50_ms','N/D')}ms "
          f"P95={metrics.get('p95_ms','N/D')}ms "
          f"P99={metrics.get('p99_ms','N/D')}ms  RNF-01: {cumple}")

    return metrics


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--backend", default=os.environ.get("BACKEND_URL", "http://localhost:8000"))
    ap.add_argument("--clients", nargs="+", type=int, default=DEFAULT_LEVELS)
    ap.add_argument("--requests", type=int, default=DEFAULT_REQUESTS,
                    help="Solicitudes por cliente por nivel")
    ap.add_argument("--skip-docker-stats", action="store_true",
                    help="Omitir captura de CPU/RAM via docker stats")
    a = ap.parse_args()

    env = common.load_env()
    user = os.environ.get("AUTH_USERNAME") or env.get("AUTH_USERNAME", "admin")
    pwd = os.environ.get("AUTH_PASSWORD") or env.get("AUTH_PASSWORD", "")
    if not pwd:
        sys.exit("Falta AUTH_PASSWORD en .env o entorno.")

    print(f"\n{'='*70}")
    print(f"  SUITE DE CARGA CONCURRENTE — Plan de Mejora Prioridad 1")
    print(f"  Backend: {a.backend}")
    print(f"  Niveles: {a.clients}  |  Req/cliente: {a.requests}")
    print(f"  Fecha/hora: {datetime.now(timezone.utc).isoformat()}")
    print(f"{'='*70}")

    token = login(a.backend, user, pwd)
    stamp = time.strftime("%Y-%m-%d")
    all_metrics = []

    for n in a.clients:
        m = run_level(a.backend, token, n, a.requests, stamp, a.skip_docker_stats)
        all_metrics.append(m)

    # Guardar JSON consolidado
    os.makedirs(RESULTS_DIR, exist_ok=True)
    json_path = os.path.join(RESULTS_DIR, f"load_consolidated_{stamp}.json")
    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "backend": a.backend,
        "requests_per_client": a.requests,
        "levels_tested": a.clients,
        "plan_reference": "Sección 4 — Prioridad 1 del Plan de Mejora",
        "results": all_metrics,
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    # Tabla Markdown para la tesis
    md_path = os.path.join(RESULTS_DIR, f"load_consolidated_{stamp}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("## Resultados del Test de Carga Concurrente\n\n")
        f.write(f"**Fecha:** {datetime.now(timezone.utc).strftime('%Y-%m-%d')}  \n")
        f.write(f"**Backend:** {a.backend}  \n")
        f.write(f"**Solicitudes por cliente por nivel:** {a.requests}  \n\n")
        f.write("| Clientes | Total req | Exitosas | Fallidas | Error % | "
                "P50 (ms) | P95 (ms) | P99 (ms) | Throughput (req/s) | RNF-01 P95<500ms |\n")
        f.write("|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|\n")
        for m in all_metrics:
            cumple = "✓" if m.get("rnf01_p95_cumple") else "✗"
            f.write(f"| {m['clients']} | {m['total_requests']} | {m['successful']} | "
                    f"{m['failed']} | {m['error_rate_pct']} | {m.get('p50_ms','N/D')} | "
                    f"{m.get('p95_ms','N/D')} | {m.get('p99_ms','N/D')} | "
                    f"{m['throughput_rps']} | {cumple} |\n")
        f.write("\n")
        f.write("**Interpretación:** La disponibilidad reportada corresponde a la API bajo "
                "carga sintética de lectura bajo las condiciones experimentales definidas. "
                "No incluye Orthanc ni n8n y no caracteriza carga clínica real.\n")

    print(f"\n{'='*70}")
    print(f"  TABLA CONSOLIDADA\n")
    print(f"  {'Clientes':>8} | {'Total':>6} | {'Exitosas':>8} | {'Error%':>6} | "
          f"{'P50ms':>7} | {'P95ms':>7} | {'P99ms':>7} | {'RPS':>6} | RNF-01")
    print(f"  {'-'*80}")
    for m in all_metrics:
        cumple = "CUMPLE" if m.get("rnf01_p95_cumple") else "NO CMP"
        print(f"  {m['clients']:>8} | {m['total_requests']:>6} | {m['successful']:>8} | "
              f"{m['error_rate_pct']:>6} | {str(m.get('p50_ms','N/D')):>7} | "
              f"{str(m.get('p95_ms','N/D')):>7} | {str(m.get('p99_ms','N/D')):>7} | "
              f"{m['throughput_rps']:>6} | {cumple}")

    print(f"\n  JSON: {json_path}")
    print(f"  MD:   {md_path}")
    print(f"{'='*70}")
    print("\nInterpretación: capacidad observada bajo los escenarios ensayados, "
          "no capacidad garantizada bajo carga hospitalaria real.")


if __name__ == "__main__":
    main()
