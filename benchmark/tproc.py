#!/usr/bin/env python3
"""Medicion de T_proc (tiempo de procesamiento automatizado) - Escenario B.

Ejecuta N ciclos completos del pipeline (n8n: GET mocks -> normalizacion ->
aggregate -> POST /orders/batch) y recolecta desde los logs del backend las
marcas de tiempo para descomponer:

    T_n8n    = t_received - ts_start     (transformacion en n8n + transferencia)
    T_server = t_done    - t_received    (persistencia + triage en FastAPI)
    T_proc   = t_done    - ts_start      (ciclo completo, end-to-end)

Precondiciones:
    - Contenedores levantados (docker compose up -d --build).
    - Workflow "Orquestador Imagenes" importado, activo y con el webhook
      "medir-ciclo" publicado (n8n-workflow/Orquestador Imagenes.json).
"""
import argparse
import csv
import os
import statistics
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

OUT_DEFAULT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results_tproc.csv")


def trigger_cycle(n8n_url: str, cycle_id: str, ts_start: int) -> int:
    body = '{"cycle_id": "%s", "ts_start": %d}' % (cycle_id, ts_start)
    req = urllib.request.Request(
        f"{n8n_url}/webhook/medir-ciclo",
        data=body.encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        return resp.status


def wait_done(cycle_id: str, since_iso: str, timeout_s: float = 30):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        for name, fields in common.fetch_metric_lines("backend", since_iso, f"cycle_id={cycle_id}"):
            if name == "t_proc" and fields.get("event") == "done":
                return fields
        time.sleep(0.5)
    return None


def summarize(rows: list[dict], keys: list[str]):
    print("\n--- Resumen (milisegundos) ---")
    for key in keys:
        values = [float(r[key]) for r in rows if r.get(key) not in (None, "")]
        if not values:
            print(f"{key}: sin datos")
            continue
        print(
            f"{key}: n={len(values)} media={statistics.mean(values):.3f} "
            f"mediana={statistics.median(values):.3f} min={min(values):.3f} "
            f"max={max(values):.3f} std={statistics.pstdev(values):.3f}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cycles", type=int, default=50)
    parser.add_argument("--n8n", default=os.environ.get("N8N_URL", "http://localhost:5678"))
    parser.add_argument("--out", default=OUT_DEFAULT)
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args()

    env = common.load_env()
    fields_csv = ["cycle_id", "ts_start", "status", "t_received", "t_done", "T_n8n", "T_server", "T_proc", "created"]
    rows = []

    print(f"Ejecutando {args.cycles} ciclos del pipeline (n8n -> FastAPI)...")
    for i in range(1, args.cycles + 1):
        cycle_id = f"T-{i:03d}"
        common.truncate_orders(env)
        since_iso = common.iso_now()
        ts_start = common.now_ms()
        status = trigger_cycle(args.n8n, cycle_id, ts_start)
        fields = wait_done(cycle_id, since_iso, args.timeout)

        row = {"cycle_id": cycle_id, "ts_start": ts_start, "status": status}
        if fields:
            for k in ("t_received", "t_done", "T_n8n", "T_server", "T_proc", "created"):
                row[k] = fields.get(k, "")
        else:
            for k in ("t_received", "t_done", "T_n8n", "T_server", "T_proc", "created"):
                row[k] = ""
        rows.append(row)
        print(
            f"{cycle_id}: status={status} T_n8n={row['T_n8n']}ms "
            f"T_server={row['T_server']}ms T_proc={row['T_proc']}ms created={row['created']}"
        )

    with open(args.out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields_csv)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nCSV guardado en {args.out}")

    summarize(rows, ["T_n8n", "T_server", "T_proc"])


if __name__ == "__main__":
    main()
