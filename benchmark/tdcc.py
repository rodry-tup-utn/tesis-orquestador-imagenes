#!/usr/bin/env python3
"""Medicion de TDCC (tiempo de deteccion de caso critico) - Escenario B.

Envía N ordenes criticas directamente al backend (/orders/batch) y mide el
tiempo desde la recepcion del batch hasta que la notificacion de la alerta
critica responde 200 al webhook de n8n:

    TDCC = t_notify_end - t_received

La orden critica se construye con diagnostico "ACV" + modalidad CT + urgente +
servicio Guardia (score 34 >= umbral 25 -> MedicalPriority.CRITICAL).

Precondiciones:
    - Contenedores levantados (docker compose up -d --build).
    - .env con URL_WEBHOOK_N8N apuntando al webhook del workflow "Alertas
      Criticas", y ese workflow activo (para que el notifier reciba 200).
"""
import argparse
import csv
import json
import os
import statistics
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

OUT_DEFAULT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results_tdcc.csv")


def critical_order(n: int) -> dict:
    return {
        "external_id": f"CRIT-{n:03d}",
        "source_system": "GUARDIA",
        "description": "TC de Cerebro",
        "modality": "CT",
        "origin_service": "Guardia",
        "patient_location": "Box Rojo",
        "study_setting": "En Efector",
        "diagnosis": "ACV",
        "observations": "Caso critico de prueba TDCC",
        "order_date": "2026-04-09T08:00:00",
        "requesting_physician": "Dr. Benchmark",
        "patient_lastname": "Paciente",
        "patient_name": "Critico",
        "patient_pseudonym": "C.C.",
        "patient_dni": str(40000000 + n),
        "patient_dob": "1980-01-01",
        "patient_sex": "MALE",
        "is_urgent": True,
    }


def post_batch(backend_url: str, cycle_id: str, order: dict) -> dict:
    body = json.dumps({"cycle_id": cycle_id, "ts_start": common.now_ms(), "orders": [order]})
    req = urllib.request.Request(
        f"{backend_url}/orders/batch",
        data=body.encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def wait_tdcc(external_id: str, since_iso: str, timeout_s: float = 30):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        for name, fields in common.fetch_metric_lines("backend", since_iso, f"external_id={external_id}"):
            if name == "tdcc":
                return fields
        time.sleep(0.5)
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--backend", default=os.environ.get("BACKEND_URL", "http://localhost:8000"))
    parser.add_argument("--out", default=OUT_DEFAULT)
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args()

    fields_csv = ["run", "cycle_id", "external_id", "order_id", "priority", "status", "t_notify_end", "TDCC"]
    rows = []

    print(f"Ejecutando {args.runs} ordenes criticas sobre el backend...")
    for n in range(1, args.runs + 1):
        cycle_id = f"C-{n:03d}"
        since_iso = common.iso_now()
        order = critical_order(n)
        resp = post_batch(args.backend, cycle_id, order)
        created_ids = resp.get("created_ids") or []
        fields = wait_tdcc(order["external_id"], since_iso, args.timeout)

        row = {
            "run": n,
            "cycle_id": cycle_id,
            "external_id": order["external_id"],
            "order_id": created_ids[0] if created_ids else "",
            "priority": fields.get("priority", "") if fields else "",
            "status": fields.get("status", "") if fields else "",
            "t_notify_end": fields.get("t_notify_end", "") if fields else "",
            "TDCC": fields.get("TDCC", "") if fields else "",
        }
        rows.append(row)
        print(f"{cycle_id}: order_id={row['order_id']} priority={row['priority']} status={row['status']} TDCC={row['TDCC']}ms")

    with open(args.out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields_csv)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nCSV guardado en {args.out}")

    values = [float(r["TDCC"]) for r in rows if r.get("TDCC") not in (None, "")]
    if not values:
        print("\nSin muestras de TDCC. Verifica URL_WEBHOOK_N8N y que el workflow 'Alertas Criticas' este activo.")
        return
    print(
        "\n--- Resumen TDCC (milisegundos) ---\n"
        f"n={len(values)} media={statistics.mean(values):.3f} "
        f"mediana={statistics.median(values):.3f} min={min(values):.3f} "
        f"max={max(values):.3f} std={statistics.pstdev(values):.3f}"
    )


if __name__ == "__main__":
    main()
