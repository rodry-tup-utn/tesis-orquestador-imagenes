#!/usr/bin/env python3
"""Pruebas de recuperación ante fallos — Prioridad 7 del Plan de Mejora.

Prueba cinco escenarios de resiliencia del sistema usando docker compose:
  1. Caída de PostgreSQL → detección y recuperación
  2. Reinicio del backend → tiempo de reconexión
  3. Caída temporal de Orthanc → verificar comportamiento
  4. Recuperación de PostgreSQL → verificar que no se perdieron datos
  5. Reinicio simultáneo backend + DB → recuperación total

Genera:
  benchmark/results/resilience/raw/resilience_YYYY-MM-DD.json
  benchmark/results/resilience/results/resilience_report_YYYY-MM-DD.md

Uso:
    python benchmark/run_resilience.py
    python benchmark/run_resilience.py --skip-orthanc    # si Orthanc no está disponible
"""
from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(BASE_DIR)
RESULTS_RAW = os.path.join(BASE_DIR, "results", "resilience", "raw")
RESULTS_DIR = os.path.join(BASE_DIR, "results", "resilience", "results")


def login(base: str, user: str, pwd: str, timeout: int = 10) -> str | None:
    try:
        body = json.dumps({"username": user, "password": pwd}).encode()
        req = urllib.request.Request(
            f"{base}/auth/login", data=body,
            headers={"Content-Type": "application/json"}, method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())["access_token"]
    except Exception:
        return None


def api_check(base: str, token: str, endpoint: str = "/orders/stats",
              timeout: int = 5) -> tuple[bool, float, int]:
    """Devuelve (success, latency_ms, status_code)."""
    t0 = time.perf_counter()
    try:
        req = urllib.request.Request(
            base + endpoint, headers={"Authorization": f"Bearer {token}"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            r.read()
            return True, (time.perf_counter() - t0) * 1000, r.status
    except urllib.error.HTTPError as e:
        return False, (time.perf_counter() - t0) * 1000, e.code
    except Exception:
        return False, (time.perf_counter() - t0) * 1000, 0


def wait_for_recovery(base: str, user: str, pwd: str, token: str, max_wait_s: int = 60,
                      poll_s: float = 2.0) -> tuple[bool, float, str]:
    """Espera hasta que la API vuelva a responder. Devuelve (recovered, time_s)."""
    t0 = time.time()
    while time.time() - t0 < max_wait_s:
        new_token = login(base, user, pwd, timeout=5) or token
        ok, _, status = api_check(base, new_token, timeout=5)
        if ok and status == 200:
            return True, time.time() - t0, new_token
        time.sleep(poll_s)
    return False, time.time() - t0, token


def docker_cmd(args: list[str]) -> tuple[int, str]:
    """Ejecuta docker compose con los args dados."""
    cmd = ["docker", "compose"] + args
    result = subprocess.run(
        cmd, cwd=REPO_ROOT, capture_output=True, text=True, timeout=60
    )
    return result.returncode, result.stdout + result.stderr


def count_orders(base: str, token: str) -> int:
    """Devuelve el número de órdenes en la base."""
    try:
        req = urllib.request.Request(
            base + "/orders/stats",
            headers={"Authorization": f"Bearer {token}"}
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
            return data.get("total", data.get("count", -1))
    except Exception:
        return -1


def run_scenario(name: str, fn, *args, **kwargs) -> dict:
    """Ejecuta un escenario y registra resultado."""
    print(f"\n  ▶ {name}")
    t0 = time.time()
    try:
        result = fn(*args, **kwargs)
        elapsed = time.time() - t0
        result["scenario"] = name
        result["duration_s"] = round(elapsed, 2)
        status = "✓ PASSED" if result.get("passed") is True else ("○ NO EJECUTADO" if result.get("passed") is None else "✗ FAILED")
        print(f"     → {status}  ({elapsed:.1f}s)")
        if result.get("notes"):
            print(f"     ℹ  {result['notes']}")
        return result
    except Exception as e:
        elapsed = time.time() - t0
        print(f"     → ✗ ERROR: {e}")
        return {"scenario": name, "passed": False, "error": str(e), "duration_s": round(elapsed, 2)}


def scenario_postgres_down(base: str, token: str, user: str, pwd: str) -> dict:
    """Detiene PostgreSQL y mide el tiempo hasta que la API detecta la caída y se recupera."""
    orders_before = count_orders(base, token)

    # Detener postgres
    rc, _ = docker_cmd(["stop", "db_hospital"])
    if rc != 0:
        return {"passed": None, "notes": "No se pudo detener db_hospital; escenario no ejecutado"}

    # Esperar hasta que la API falle
    t0 = time.time()
    detection_s = None
    for _ in range(20):
        ok, _, _ = api_check(base, token)
        if not ok:
            detection_s = time.time() - t0
            break
        time.sleep(1)

    # Reiniciar postgres
    docker_cmd(["start", "db_hospital"])
    time.sleep(5)  # Esperar que healthcheck pase

    # Esperar recuperación
    token2 = login(base, user, pwd) or token
    recovered, recovery_s, _ = wait_for_recovery(base, user, pwd, token2, max_wait_s=90)
    orders_after = count_orders(base, token2) if recovered else -1

    return {
        "passed": recovered,
        "detection_s": round(detection_s, 1) if detection_s else "N/D (no detectó)",
        "recovery_s": round(recovery_s, 1),
        "orders_before": orders_before,
        "orders_after": orders_after,
        "data_lost": (orders_before != orders_after) if orders_after >= 0 else "N/D",
        "notes": f"Detección en {detection_s:.1f}s, recuperación en {recovery_s:.1f}s" if detection_s else "La API no llegó a fallar visible.",
    }


def scenario_backend_restart(base: str, token: str, user: str, pwd: str) -> dict:
    """Reinicia el backend y mide el tiempo de reconexión."""
    orders_before = count_orders(base, token)

    rc, _ = docker_cmd(["restart", "backend"])
    if rc != 0:
        return {"passed": False, "notes": "No se pudo reiniciar backend"}

    t0 = time.time()
    # Esperar que deje de responder
    time.sleep(3)

    # Esperar recuperación
    token2 = login(base, user, pwd) or token
    recovered, recovery_s, _ = wait_for_recovery(base, user, pwd, token2, max_wait_s=60)
    orders_after = count_orders(base, token2) if recovered else -1

    return {
        "passed": recovered,
        "recovery_s": round(recovery_s, 1),
        "orders_before": orders_before,
        "orders_after": orders_after,
        "data_lost": (orders_before != orders_after) if orders_after >= 0 else "N/D",
        "notes": f"Backend recuperado en {recovery_s:.1f}s tras reinicio",
    }


def scenario_orthanc_down(base: str, token: str) -> dict:
    """Detiene Orthanc y verifica que el backend sigue funcionando."""
    rc, _ = docker_cmd(["stop", "servidor_dicom"])
    if rc != 0:
        return {"passed": None, "notes": "servidor_dicom no pudo detenerse; escenario no ejecutado"}

    time.sleep(3)
    ok, lat, status = api_check(base, token)

    # Reiniciar Orthanc
    docker_cmd(["start", "servidor_dicom"])

    return {
        "passed": ok and status == 200,
        "api_still_responds": ok,
        "latency_ms": round(lat, 2),
        "notes": f"Con Orthanc caído, la API {'sigue respondiendo' if ok else 'también falló'} (status={status})",
    }


def scenario_postgres_recovery_no_data_loss(base: str, token: str,
                                            user: str, pwd: str,
                                            api_key: str) -> dict:
    """Crea una orden, detiene DB, reinicia DB y verifica que la orden persiste."""
    # Crear orden de prueba
    order_id = None
    try:
        body = json.dumps({
            "cycle_id": "RESIL-TEST",
            "orders": [{
                "external_id": "RESIL-001",
                "source_system": "TEST",
                "description": "Orden de prueba resiliencia",
                "modality": "CT",
                "origin_service": "Guardia",
                "patient_location": "Box 1",
                "study_setting": "En Efector",
                "diagnosis": "Test resiliencia",
                "observations": "Verificación de persistencia ante caída de DB",
                "order_date": "2026-09-23T12:00:00",
                "requesting_physician": "Dr. Test",
                "patient_lastname": "Apellido",
                "patient_name": "Nombre",
                "patient_dni": "99999999",
                "patient_dob": "1990-01-01",
                "patient_sex": "MALE",
                "is_urgent": True,
            }]
        }).encode()
        req = urllib.request.Request(
            base + "/orders/batch", data=body,
            headers={"Content-Type": "application/json", "X-Internal-API-Key": api_key},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            order_id = "creada"
    except Exception as e:
        return {"passed": False, "notes": f"No se pudo crear orden: {e}"}

    orders_before = count_orders(base, token)

    # Simular caída y recuperación de DB
    stop_rc, _ = docker_cmd(["stop", "db_hospital"])
    if stop_rc != 0:
        return {"passed": None, "orders_before_failure": orders_before, "orders_after_recovery": "N/D",
                "data_lost": "N/D", "recovery_s": "N/D",
                "notes": "No se pudo detener db_hospital; escenario no ejecutado"}
    time.sleep(5)
    docker_cmd(["start", "db_hospital"])
    time.sleep(10)

    token2 = login(base, user, pwd) or token
    recovered, recovery_s, _ = wait_for_recovery(base, user, pwd, token2, max_wait_s=60)
    orders_after = count_orders(base, token2) if recovered else -1

    return {
        "passed": recovered and orders_after >= orders_before,
        "orders_before_failure": orders_before,
        "orders_after_recovery": orders_after,
        "data_lost": not (orders_after >= orders_before),
        "recovery_s": round(recovery_s, 1),
        "notes": f"Órdenes antes: {orders_before}, después: {orders_after}",
    }


def scenario_full_restart(base: str, user: str, pwd: str) -> dict:
    """Reinicia todos los servicios principales y verifica la recuperación."""
    docker_cmd(["restart", "backend"])
    docker_cmd(["restart", "db_hospital"])
    time.sleep(10)

    token = login(base, user, pwd)
    if not token:
        recovered, recovery_s, _ = wait_for_recovery(
            base, user, pwd, token or "", max_wait_s=120, poll_s=5
        )
        token = login(base, user, pwd)
    else:
        recovery_s = 0.0
        recovered = True

    if token:
        ok, lat, status = api_check(base, token)
    else:
        ok, lat, status = False, 0, 0

    return {
        "passed": ok and status == 200,
        "api_responsive": ok,
        "recovery_s": round(recovery_s + 10, 1),
        "final_status": status,
        "latency_ms": round(lat, 2),
        "notes": f"Tras reinicio completo, API responde {'OK' if ok else 'ERROR'} en {lat:.1f}ms",
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--backend", default=os.environ.get("BACKEND_URL", "http://localhost:8000"))
    ap.add_argument("--skip-orthanc", action="store_true")
    a = ap.parse_args()

    env = common.load_env()
    user = os.environ.get("AUTH_USERNAME") or env.get("AUTH_USERNAME", "admin")
    pwd = os.environ.get("AUTH_PASSWORD") or env.get("AUTH_PASSWORD", "")
    api_key = os.environ.get("INTERNAL_API_KEY") or env.get("INTERNAL_API_KEY", "")

    if not pwd:
        sys.exit("Falta AUTH_PASSWORD en .env o entorno.")

    os.makedirs(RESULTS_RAW, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    stamp = time.strftime("%Y-%m-%d_%H%M")

    print(f"\n{'='*70}")
    print(f"  PRUEBAS DE RESILIENCIA — Plan de Mejora Prioridad 7")
    print(f"  Fecha: {datetime.now(timezone.utc).isoformat()}")
    print(f"  Backend: {a.backend}")
    print(f"{'='*70}")

    token = login(a.backend, user, pwd)
    if not token:
        sys.exit(f"No se pudo autenticar contra {a.backend}. ¿Está el stack levantado?")

    scenarios_results = []

    scenarios_results.append(run_scenario(
        "Escenario 1: Caída de PostgreSQL → detección y recuperación",
        scenario_postgres_down, a.backend, token, user, pwd,
    ))
    token = login(a.backend, user, pwd) or token

    scenarios_results.append(run_scenario(
        "Escenario 2: Reinicio del backend → tiempo de reconexión",
        scenario_backend_restart, a.backend, token, user, pwd,
    ))
    token = login(a.backend, user, pwd) or token

    if not a.skip_orthanc:
        scenarios_results.append(run_scenario(
            "Escenario 3: Caída temporal de Orthanc → API sigue funcionando",
            scenario_orthanc_down, a.backend, token,
        ))

    scenarios_results.append(run_scenario(
        "Escenario 4: Persistencia de datos ante caída y recuperación de DB",
        scenario_postgres_recovery_no_data_loss, a.backend, token, user, pwd, api_key,
    ))
    token = login(a.backend, user, pwd) or token

    scenarios_results.append(run_scenario(
        "Escenario 5: Reinicio completo (backend + DB) → recuperación total",
        scenario_full_restart, a.backend, user, pwd,
    ))

    passed = sum(1 for r in scenarios_results if r.get("passed") is True)
    failed = sum(1 for r in scenarios_results if r.get("passed") is False)
    not_executed = sum(1 for r in scenarios_results if r.get("passed") is None)
    total = len(scenarios_results)

    # Guardar JSON crudo
    json_path = os.path.join(RESULTS_RAW, f"resilience_{stamp}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "backend": a.backend,
            "scenarios_passed": passed,
            "scenarios_failed": failed,
            "scenarios_not_executed": not_executed,
            "scenarios_total": total,
            "plan_reference": "Sección 10 — Prioridad 7 del Plan de Mejora",
            "results": scenarios_results,
        }, f, indent=2, ensure_ascii=False)

    # Markdown para la tesis
    md_path = os.path.join(RESULTS_DIR, f"resilience_report_{stamp}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("## Pruebas de Recuperación ante Fallos\n\n")
        f.write(f"**Fecha:** {datetime.now(timezone.utc).strftime('%Y-%m-%d')}  \n")
        f.write(f"**Escenarios pasados:** {passed}/{total}  \n\n")
        f.write("| Escenario | Resultado | T. Recuperación | Datos Perdidos | Notas |\n")
        f.write("|---|:---:|---:|:---:|---|\n")
        for r in scenarios_results:
            result_icon = "✓" if r.get("passed") is True else ("○" if r.get("passed") is None else "✗")
            rec_s = r.get("recovery_s", "N/D")
            data_lost = r.get("data_lost", "N/D")
            if isinstance(data_lost, bool):
                data_lost = "Sí" if data_lost else "No"
            notes = r.get("notes", "")[:80]
            f.write(f"| {r['scenario'][:50]} | {result_icon} | {rec_s}s | {data_lost} | {notes} |\n")
        f.write("\n**Interpretación:** los escenarios ejecutados y superados aportan evidencia de recuperación bajo las condiciones de prueba. "
                "Los escenarios marcados como no ejecutados no se contabilizan como éxitos ni como fallos y no sustentan una conclusión sobre el comportamiento no observado.\n")

    print(f"\n{'='*70}")
    print(f"  RESULTADO: {passed} PASS / {failed} FAIL / {not_executed} NO EJECUTADOS de {total}")
    print(f"  JSON: {json_path}")
    print(f"  MD:   {md_path}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
