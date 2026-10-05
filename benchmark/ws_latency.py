#!/usr/bin/env python3
"""Medicion de latencia de notificacion por WebSocket (RF-04).

RF-04 exige notificar las actualizaciones del estado de las ordenes al tablero
en tiempo real. Este script mide el tiempo transcurrido desde que se despacha
una peticion de persistencia/actualizacion hacia la API hasta que el cliente
WebSocket recibe el evento 'orders_updated' transmitido por el backend:

    Latencia = t_ws_receive - t_request_start

Advertencia de interpretacion: t_ws_receive se toma cuando la peticion de
persistencia ya retorno. El backend emite el evento antes de responder, por lo
que el mensaje ya esta en cola al llamar a recv(). La cifra es, por tanto, una
COTA SUPERIOR que incluye la duracion completa de la ingesta y no aisla el
tiempo de propagacion del evento por WebSocket.

Precondiciones:
    - Stack levantado (backend en http://localhost:8000).
    - AUTH_USERNAME, AUTH_PASSWORD e INTERNAL_API_KEY en .env o entorno.

Uso:
    python benchmark/ws_latency.py [--runs 10] [--backend http://localhost:8000]

Salida:
    CSV en benchmark/results/results_ws_latency_<fecha>.csv con estadísticos:
    n, media, mediana, desviacion estandar, IC 95% (t de Student) y maximo.
"""
from __future__ import annotations
import argparse
import asyncio
import csv
import json
import math
import os
import statistics
import sys
import time
import urllib.request
import websockets

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common


def get_jwt(backend_url: str, user: str, password: str) -> str:
    data = json.dumps({"username": user, "password": password}).encode("utf-8")
    req = urllib.request.Request(
        f"{backend_url}/auth/login",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())["access_token"]


def trigger_order(backend_url: str, run_id: int, api_key: str) -> None:
    order = {
        "external_id": f"WS-TEST-{run_id:04d}",
        "source_system": "AMBULATORIO",
        "description": "Rx Torax Frente",
        "modality": "DX",
        "origin_service": "Consultorio Externo",
        "patient_location": "Consultorio 4",
        "study_setting": "En Efector",
        "diagnosis": "Control de rutina",
        "observations": "Medicion RF-04 WebSocket",
        "order_date": "2026-09-20T10:00:00",
        "requesting_physician": "Dr. Benchmark",
        "patient_lastname": "TestWS",
        "patient_name": "Paciente",
        "patient_dni": str(50000000 + run_id),
        "patient_dob": "1995-05-15",
        "patient_sex": "FEMALE",
        "is_urgent": False,
    }
    body = json.dumps({"cycle_id": f"WSC-{run_id:03d}", "orders": [order]}).encode("utf-8")
    req = urllib.request.Request(
        f"{backend_url}/orders/batch",
        data=body,
        headers={"Content-Type": "application/json", "X-Internal-API-Key": api_key},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        resp.read()


async def measure_single_run(ws, backend_url: str, run_id: int, api_key: str) -> float:
    # Inicia medicion t0 justo antes de enviar la peticion
    t0 = time.perf_counter()
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, trigger_order, backend_url, run_id, api_key)

    # Espera recibir el mensaje del WebSocket
    msg = await asyncio.wait_for(ws.recv(), timeout=10.0)
    t1 = time.perf_counter()

    if "orders_updated" not in msg:
        # Puede haber quedado un mensaje anterior; leer el siguiente si aplica
        msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
        t1 = time.perf_counter()

    return (t1 - t0) * 1000.0


async def run_benchmark(backend_url: str, runs: int, out_csv: str) -> None:
    env = common.load_env()
    user = os.environ.get("AUTH_USERNAME") or env.get("AUTH_USERNAME", "admin")
    password = os.environ.get("AUTH_PASSWORD") or env.get("AUTH_PASSWORD", "")
    api_key = os.environ.get("INTERNAL_API_KEY") or env.get("INTERNAL_API_KEY", "")

    if not password:
        sys.exit("[ERROR] Falta AUTH_PASSWORD en .env")
    if not api_key:
        sys.exit("[ERROR] Falta INTERNAL_API_KEY en .env")

    print(f"\nAutenticando en {backend_url}...")
    token = get_jwt(backend_url, user, password)

    ws_url = backend_url.replace("http://", "ws://").replace("https://", "wss://") + "/ws"
    print(f"Conectando a WebSocket: {ws_url}...")

    async with websockets.connect(ws_url) as ws:
        # Autenticacion del socket segun protocolo del backend
        await ws.send(json.dumps({"type": "auth", "token": token}))
        auth_ack = await ws.recv()
        if "authenticated" not in auth_ack:
            sys.exit(f"[ERROR] Autenticacion WebSocket rechazada: {auth_ack}")
        print("WebSocket autenticado correctamente.")

        # Calentamiento (1 corrida descartada)
        print("Ejecutando ciclo de calentamiento...")
        await measure_single_run(ws, backend_url, 9999, api_key)
        await asyncio.sleep(0.5)

        print(f"\nEjecutando {runs} ciclos de medicion para RF-04...")
        latencies = []
        rows = []
        for i in range(1, runs + 1):
            ms = await measure_single_run(ws, backend_url, i, api_key)
            latencies.append(ms)
            rows.append({"run": i, "latency_ms": round(ms, 3)})
            print(f"  Ciclo {i:2d}/{runs}: {ms:6.2f} ms")
            await asyncio.sleep(0.2)

    # Estadisticas
    n = len(latencies)
    mean_val = statistics.mean(latencies)
    med_val = statistics.median(latencies)
    std_val = statistics.stdev(latencies) if n > 1 else 0.0
    min_val = min(latencies)
    max_val = max(latencies)

    # Intervalo t de Student al 95%
    # Valores criticos t(gl): gl=9 -> 2.262, gl=19 -> 2.093, aprox 1.96 para n grande
    t_crit_table = {9: 2.262, 10: 2.228, 14: 2.145, 19: 2.093, 29: 2.045}
    t_crit = t_crit_table.get(n - 1, 2.262)
    margin = t_crit * (std_val / math.sqrt(n)) if n > 1 else 0.0
    ci_lower = mean_val - margin
    ci_upper = mean_val + margin

    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["run", "latency_ms"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n{'='*65}")
    print("  RESULTADO MEDIDO RF-04 (LATENCIA WEBSOCKET BACKEND -> CLIENTE)")
    print(f"{'='*65}")
    print(f"  Muestras (n):        {n}")
    print(f"  Media:               {mean_val:.2f} ms")
    print(f"  Mediana:             {med_val:.2f} ms")
    print(f"  Desvio estandar:     {std_val:.2f} ms")
    print(f"  Rango:               [{min_val:.2f} ms; {max_val:.2f} ms]")
    print(f"  IC 95% (Student t):  [{ci_lower:.2f} ms; {ci_upper:.2f} ms]")
    print(f"  CSV guardado en:     {out_csv}")
    print(f"{'='*65}")
    verdict = "sub-segundo" if max_val < 1000.0 else "SUPERA 1 s en al menos una corrida"
    print(f"  -> RF-04 (cota superior, un cliente, carga secuencial): {verdict}\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=10, help="Cantidad de mediciones")
    parser.add_argument("--backend", default=os.environ.get("BACKEND_URL", "http://localhost:8000"))
    stamp = time.strftime("%Y-%m-%d")
    default_out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", f"results_ws_latency_{stamp}.csv")
    parser.add_argument("--out", default=default_out)
    args = parser.parse_args()

    asyncio.run(run_benchmark(args.backend, args.runs, args.out))


if __name__ == "__main__":
    main()
