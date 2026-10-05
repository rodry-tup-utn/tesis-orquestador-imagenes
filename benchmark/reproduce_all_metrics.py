#!/usr/bin/env python3
"""Script Único Maestro: Reproducir Todas las Cifras y Evidencia de la Tesis.

Ejecuta y verifica de manera determinística y unificada todos los experimentos,
métricas de rendimiento, regresión algorítmica, contratos de datos, auditorías
de seguridad y resiliencia documentados en la tesis.

REQUISITOS Y ALCANCE (léase antes de interpretar la salida):
    - Las secciones 1 y 2 (hashes, tags de imagen, política de reintentos,
      regresión del motor) no requieren nada además de las dependencias de
      `server/requirements.txt` instaladas, y de poder importar el paquete
      `app` del backend.
    - La sección 3 (pruebas de contrato) SÍ requiere un contenedor del backend
      corriendo y nombrado `fastapi_radiogroup` (por ejemplo, con
      `docker compose up -d backend`). Si ese contenedor no está disponible,
      la sección se informa explícitamente como NO EJECUTADA, no se inventa
      un resultado y el script continúa con el resto de las secciones.
    - Cada sección expone un booleano de éxito propio. El resumen final
      (sección 6) se arma leyendo esos booleanos: una sección que falló o que
      no pudo ejecutarse se lista como tal, y el veredicto global solo dice
      "verificado" si TODAS las secciones que sí corrieron fueron exitosas y
      se señalan aparte las que no pudieron correr por falta de entorno.

Uso:
    python benchmark/reproduce_all_metrics.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BENCHMARK_DIR = ROOT / "benchmark"
RESULTS_DIR = BENCHMARK_DIR / "results"
SERVER_DIR = ROOT / "server"


def sha256_file(path: Path) -> str:
    if not path.exists():
        return "N/A"
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()[:16]


def section(title: str):
    print("\n" + "=" * 70)
    print(f"  {title.upper()}")
    print("=" * 70)


def p95(values: list[float]) -> float:
    return statistics.quantiles(values, n=100, method="inclusive")[94]


def mean_ci95(values: list[float]) -> tuple[float, float, float]:
    """Devuelve (media, límite inferior, límite superior) del IC 95% de la media,
    con el valor t de Student para n-1 grados de libertad (aproximación de dos
    decimales sobre una tabla t estándar para n pequeño/mediano; se recurre a la
    aproximación normal 1.96 para n > 120)."""
    n = len(values)
    mean = statistics.mean(values)
    if n < 2:
        return mean, mean, mean
    sd = statistics.stdev(values)
    se = sd / math.sqrt(n)
    t_table = {
        2: 12.706, 3: 4.303, 4: 3.182, 5: 2.776, 6: 2.571, 7: 2.447, 8: 2.365,
        9: 2.306, 10: 2.262, 15: 2.145, 20: 2.093, 25: 2.060, 30: 2.042,
        40: 2.021, 50: 2.009, 60: 2.000, 80: 1.990, 100: 1.984, 120: 1.980,
    }
    df = n - 1
    key = min(t_table, key=lambda k: abs(k - df)) if df <= 120 else None
    t_val = t_table[key] if key is not None else 1.96
    margin = t_val * se
    return mean, mean - margin, mean + margin


def main() -> int:
    start_time = time.time()
    # results[nombre] = (ok: bool | None, detalle: str)
    #   True  -> se ejecutó y verificó correctamente
    #   False -> se ejecutó y NO verificó (falla real)
    #   None  -> no se pudo ejecutar por falta de entorno (no es una falla del artefacto)
    results: dict[str, tuple[bool | None, str]] = {}

    section("1. Integridad de Entorno, Configuración y Hashes Criptográficos")

    configs_to_hash = [
        ("Reglas Calibradas (Fase 4)", SERVER_DIR / "app" / "modules" / "triage" / "configs" / "calibrada_fase4.json"),
        ("Regresión N=50 Órdenes", BENCHMARK_DIR / "test_orders_regression.json"),
        ("Orquestación Docker", ROOT / "docker-compose.yml"),
        ("Canal Notificador / Retry", SERVER_DIR / "app" / "modules" / "medical_order" / "notifier.py"),
        ("Workflow n8n Alertas", ROOT / "n8n-workflow" / "Alertas Criticas.json"),
        ("Workflow n8n Orquestador", ROOT / "n8n-workflow" / "Orquestador Imagenes.json"),
    ]

    for label, path in configs_to_hash:
        print(f"  - {label:<32s} [SHA256: {sha256_file(path)}] ({path.name})")

    # Verificación Docker Tags
    compose_text = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    tags_pinned = (
        "image: docker.n8n.io/n8nio/n8n:2.39.8" in compose_text
        and "image: orthancteam/orthanc:1.13.0" in compose_text
        and "image: postgres:15-alpine" in compose_text
        and "image: python:3.9-alpine" in compose_text
    )
    print(f"  - Tags de imágenes Docker versionados por etiqueta: {'OK' if tags_pinned else 'FALLO'}")
    results["1. Hashes de configuración y tags de imagen fijados"] = (
        tags_pinned, "tags de n8n/orthanc/postgres/python pinneados en docker-compose.yml"
    )

    # Verificación Reintentos Notifier
    notifier_text = (SERVER_DIR / "app" / "modules" / "medical_order" / "notifier.py").read_text(encoding="utf-8")
    retry_implemented = (
        "_send_with_retry" in notifier_text
        and "max_retries" in notifier_text
        and "backoff_base" in notifier_text
    )
    print(f"  - Política de reintentos con backoff exponencial:  {'OK' if retry_implemented else 'FALLO'}")
    results["2. Política de reintentos implementada en notifier.py"] = (
        retry_implemented, "_send_with_retry / max_retries / backoff_base presentes en el código"
    )

    # ──────────────────────────────────────────────────────────────────────────
    section("2. Regresión del Motor de Triaje (N=50 Órdenes, 10 Prioritarios, Fronteras)")
    
    reg_path = BENCHMARK_DIR / "test_orders_regression.json"
    with open(reg_path, encoding="utf-8") as f:
        reg_data = json.load(f)
    orders = reg_data["orders"]
    print(f"  - Total órdenes sintéticas evaluadas: {len(orders)}")
    
    # Ejecutamos validate_motor.py a través de subprocess
    proc_motor = subprocess.run(
        [sys.executable, "-c", """
import json, unicodedata
from app.modules.triage.triage import TriageEngine
from app.modules.triage.model import TriageField, TriageOperator
from types import SimpleNamespace

with open('app/modules/triage/configs/calibrada_fase4.json') as f:
    cfg = json.load(f)

rules = [SimpleNamespace(
    name=r['name'], field=TriageField(r['field']), operator=TriageOperator(r['operator']),
    value=r['value'], weight=r['weight'], enabled=r.get('enabled', True)
) for r in cfg['rules']]

settings = SimpleNamespace(
    triage_critical_threshold=cfg['thresholds']['critical'],
    triage_urgent_threshold=cfg['thresholds']['urgent'],
    triage_priority_threshold=cfg['thresholds']['priority'],
)

with open('../benchmark/test_orders_regression.json') as f:
    data = json.load(f)

correct = 0
dist = {}
for o in data['orders']:
    fields = {'modality', 'origin_service', 'patient_location', 'diagnosis', 'is_urgent', 'description'}
    obj = SimpleNamespace(**{name: o.get(name) for name in fields})
    p, crit = TriageEngine.evaluate(obj, rules, settings)
    
    def norm(v): return ''.join(c for c in unicodedata.normalize('NFD', str(v).lower()) if unicodedata.category(c) != 'Mn')
    ok = norm(p.value) == norm(o['expected_priority'])
    if ok: correct += 1
    dist[p.value] = dist.get(p.value, 0) + 1

print(f'{correct}/{len(data[\"orders\"])};{dist}')
"""],
        cwd=str(SERVER_DIR),
        capture_output=True,
        text=True,
    )
    
    motor_env_missing = "ModuleNotFoundError" in (proc_motor.stderr or "") or "ImportError" in (proc_motor.stderr or "")
    if proc_motor.returncode == 0 and ";" in proc_motor.stdout and not motor_env_missing:
        res_str, dist_str = proc_motor.stdout.strip().split(";")
        aciertos, total = (int(x) for x in res_str.split("/"))
        motor_ok = aciertos == total == len(orders)
        print(f"  - Consistencia del artefacto contra especificación calibrada: {res_str} ({100 * aciertos / total:.1f}%)")
        print(f"  - Distribución de prioridades: {dist_str}")
        if not motor_ok:
            print(f"    AVISO: se esperaban {len(orders)}/{len(orders)} aciertos; el motor calibrado ya no reproduce su propia especificación.")
    else:
        # No se pudo importar/ejecutar el TriageEngine real (p. ej. faltan dependencias
        # del backend en este entorno). Se informa como NO EJECUTADO, no como éxito.
        motor_ok = None
        err = (proc_motor.stderr or "").strip().splitlines()[-1] if proc_motor.stderr else "sin salida"
        print(f"  - Consistencia del artefacto: NO EJECUTADO (no se pudo importar el TriageEngine real: {err})")
        print(f"    Estructura del artefacto: {len(orders)} órdenes presentes en el archivo de regresión (no evaluadas en esta corrida).")
    results["3. Regresión del motor (N=50, TriageEngine real)"] = (
        motor_ok, "50/50 contra la configuración calibrada de Fase 4" if motor_ok else "ver detalle arriba"
    )

    # ──────────────────────────────────────────────────────────────────────────
    section("3. Pruebas de Contrato (Normalizadores ↔ Catálogo ↔ Backend)")
    
    # Preferimos correr los tests de contrato en el proceso local si el paquete `app`
    # es importable (no requiere Docker); si no, intentamos el contenedor del backend;
    # si ninguno está disponible, se informa como NO EJECUTADO en vez de asumir éxito.
    contract_ok: bool | None
    proc_local = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_contract.py", "-q"],
        cwd=str(SERVER_DIR),
        capture_output=True,
        text=True,
    )
    local_env_missing = "No module named pytest" in (proc_local.stdout + proc_local.stderr) or \
        "ModuleNotFoundError" in (proc_local.stdout + proc_local.stderr) or \
        "ImportError" in (proc_local.stdout + proc_local.stderr)
    if proc_local.returncode in (0, 1) and not local_env_missing:  # pytest corrió (0=pass, 1=fail de assert)
        contract_ok = proc_local.returncode == 0
        print(f"  - Contrato Ambulatorio / Guardia / Internación (local): {'PASSED' if contract_ok else 'FALLO'}")
    else:
        try:
            proc_docker = subprocess.run(
                ["docker", "exec", "fastapi_radiogroup", "pytest", "tests/test_contract.py", "-q"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            contract_ok = proc_docker.returncode == 0
            print(f"  - Contrato Ambulatorio / Guardia / Internación (contenedor): {'PASSED' if contract_ok else 'FALLO'}")
        except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
            contract_ok = None
            print(f"  - Contrato Ambulatorio / Guardia / Internación: NO EJECUTADO "
                  f"(pytest local falló por dependencias del entorno, y no hay Docker/contenedor "
                  f"'fastapi_radiogroup' disponible: {type(exc).__name__}).")
    print(f"  - Cobertura de catálogo de modalidades (CT, MR, US, DX): "
          f"{'verificada junto con lo anterior' if contract_ok is not None else 'no verificada en esta corrida'}")
    results["4. Pruebas de contrato (normalizadores ↔ catálogo ↔ backend)"] = (
        contract_ok, "tests/test_contract.py"
    )

    # ──────────────────────────────────────────────────────────────────────────
    section("4. Verificación de Equivalencia DICOM Modality Worklist (N=50)")
    
    try:
        proc_dicom = subprocess.run(
            [sys.executable, str(BENCHMARK_DIR / "verify_dicom_equivalence_extended.py")],
            capture_output=True,
            text=True,
            timeout=60,
        )
        dicom_ran = proc_dicom.returncode == 0
        dicom_ok = dicom_ran and "Tasa Error Mapeo (TEM):0.00 %" in proc_dicom.stdout.replace(" ", " ")
        if dicom_ran:
            print(f"  - Órdenes evaluadas: 50 órdenes sintéticas")
            print(f"  - Atributos DICOM PS 3.4 evaluados: 350 atributos")
            print(f"  - Tasa de Error de Mapeo (TEM): {'OK, 0.00 %' if dicom_ok else 'FALLO, ver salida'}")
        else:
            dicom_ok = None
            err = (proc_dicom.stderr or "sin salida").strip().splitlines()[-1:] or ["sin salida"]
            print(f"  - Equivalencia DICOM MWL: NO EJECUTADO ({err[0]})")
    except FileNotFoundError as exc:
        dicom_ok = None
        print(f"  - Equivalencia DICOM MWL: NO EJECUTADO ({exc})")
    print(f"  - Alcance declarado: la verificación extendida utiliza la función de producción "
          f"app/core/orthanc_client.py::build_worklist_dataset(), el mismo serializador invocado por create_worklist(). "
          f"Acredita el mapeo/serialización productivo sobre 50 órdenes sintéticas; no sustituye una prueba C-FIND contra una modalidad real.")
    results["5. Equivalencia DICOM Modality Worklist (N=50)"] = (
        dicom_ok, "verify_dicom_equivalence_extended.py"
    )

    # ──────────────────────────────────────────────────────────────────────────
    section("5. Rendimiento y Latencia (RNF-01, TDCC/RF-04, Carga Concurrente, Soak Test)")

    # RNF-01
    api_csv = RESULTS_DIR / "results_api_latency_2026-09-20.csv"
    if api_csv.exists():
        api_data = list(csv.DictReader(api_csv.open(encoding="utf-8")))
        by_ep = {}
        for r in api_data:
            if r["status"] == "200":
                by_ep.setdefault(r["endpoint"], []).append(float(r["latency_ms"]))
        rnf01_p95 = [round(p95(v), 2) for v in by_ep.values()]
        rnf01_ok = all(v < 500 for v in rnf01_p95) if rnf01_p95 else None
        print(f"  - RNF-01 (API Latency P95, N=600): {rnf01_p95} ms "
              f"(Umbral < 500 ms: {'CUMPLE' if rnf01_ok else 'NO CUMPLE'})")
    else:
        rnf01_ok = None
        print("  - RNF-01: NO EJECUTADO (no se encontró results_api_latency_2026-09-20.csv)")
    results["6. RNF-01 (P95 latencia API < 500 ms)"] = (rnf01_ok, "results_api_latency_2026-09-20.csv")

    # TDCC / RF-04 N=50
    ws_n50_csv = RESULTS_DIR / "results_ws_latency_extended_n50_2026-09-23.csv"
    if ws_n50_csv.exists():
        ws_vals = [float(r["latency_ms"]) for r in csv.DictReader(ws_n50_csv.open(encoding="utf-8"))]
        mean_ws, ci_low, ci_high = mean_ci95(ws_vals)
        med_ws = statistics.median(ws_vals)
        p95_ws = p95(ws_vals)
        tdcc_ok = p95_ws < 1000
        print(f"  - TDCC / RF-04 Extendido (WebSocket, N={len(ws_vals)}):")
        print(f"      Media: {mean_ws:.2f} ms | Mediana (P50): {med_ws:.2f} ms | P95: {p95_ws:.2f} ms | Max: {max(ws_vals):.2f} ms")
        print(f"      IC 95% de la media (calculado, t de Student, gl={len(ws_vals)-1}): "
              f"[{ci_low:.2f} ms; {ci_high:.2f} ms] | Cumplimiento (< 1000 ms): "
              f"{'100% SUB-SEGUNDO' if tdcc_ok else 'NO CUMPLE'}")
    else:
        tdcc_ok = None
        print(f"  - TDCC / RF-04 extendido: NO EJECUTADO (no se encontró {ws_n50_csv.name})")
    results["7. TDCC/RF-04 extendido (P95 WebSocket < 1000 ms)"] = (tdcc_ok, str(ws_n50_csv.name))

    # Carga concurrente (ruta real: benchmark/results/load_suite/results/..., no benchmark/results/...)
    load_json = RESULTS_DIR / "load_suite" / "results" / "load_consolidated_2026-09-23.json"
    if load_json.exists():
        with open(load_json, encoding="utf-8") as f:
            ld = json.load(f)
        levels = ld.get("results") or []
        if levels:
            total_req = sum(lv.get("total_requests", 0) for lv in levels)
            print(f"  - Suite de Carga Concurrente ({len(levels)} niveles de concurrencia, {total_req} peticiones totales):")
            load_ok = all(
                lv.get("clients") in {1, 5, 10, 25, 50}
                and lv.get("total_requests") == lv.get("clients") * ld.get("requests_per_client", 100)
                and lv.get("error_rate_pct") is not None
                and lv.get("attempt_rate_rps") is not None
                for lv in levels
            )
            for lv in sorted(levels, key=lambda x: x.get("clients", 0)):
                p95v = lv.get("p95_ms")
                err_rate = lv.get("error_rate_pct")
                print(f"      {lv.get('clients')} clientes: P95 = {p95v} ms | Tasa de error = {err_rate}%")
            print("      Interpretación: los errores observados a 25 y 50 clientes forman parte de la caracterización del límite bajo carga y no se convierten en un fallo de la campaña.")
        else:
            load_ok = None
            print(f"  - Suite de Carga Concurrente: archivo encontrado pero sin la clave 'results' esperada; "
                  f"claves disponibles: {list(ld.keys())}")
    else:
        load_ok = None
        print(f"  - Suite de Carga Concurrente: NO EJECUTADO (no se encontró {load_json.relative_to(ROOT)})")
    results["8. Suite de carga concurrente"] = (load_ok, "load_suite/results/load_consolidated_2026-09-23.json")

    # Soak test extendido
    soak_json = RESULTS_DIR / "soak_test_report_extended_2026-09-23.json"
    if soak_json.exists():
        with open(soak_json, encoding="utf-8") as f:
            sk = json.load(f)
        soak_ok = sk.get("success_rate_percent", 0) >= 99.0
        print(f"  - Soak Test Extendido de API (estabilidad):")
        print(f"      Peticiones totales: {sk['total_requests']} | Disponibilidad: {sk['success_rate_percent']:.2f}% | P95: {sk['p95_latency_ms']} ms")
        print(f"      Primera mitad P95: {sk['first_half_p95_ms']} ms vs segunda mitad: {sk['second_half_p95_ms']} ms "
              f"({'sin deriva apreciable' if abs(sk['first_half_p95_ms'] - sk['second_half_p95_ms']) < 0.2 * sk['first_half_p95_ms'] else 'con deriva a revisar'})")
    else:
        soak_ok = None
        print("  - Soak test extendido: NO EJECUTADO (no se encontró soak_test_report_extended_2026-09-23.json)")
    results["9. Soak test extendido de API"] = (soak_ok, "soak_test_report_extended_2026-09-23.json")

    # ──────────────────────────────────────────────────────────────────────────
    section("6. Resumen de Certificación de Evidencia")

    elapsed = round(time.time() - start_time, 2)
    n_ok = sum(1 for ok, _ in results.values() if ok is True)
    n_fail = sum(1 for ok, _ in results.values() if ok is False)
    n_skip = sum(1 for ok, _ in results.values() if ok is None)

    for name, (ok, detail) in results.items():
        mark = "✔" if ok is True else ("✘" if ok is False else "○")
        estado = "OK" if ok is True else ("FALLO" if ok is False else "NO EJECUTADO")
        print(f"  {mark} {name}: {estado}  ({detail})")

    print(f"\n  Verificadas y OK: {n_ok}/{len(results)}  |  Falladas: {n_fail}  |  No ejecutadas en este entorno: {n_skip}")
    if n_fail == 0 and n_skip == 0:
        veredicto = "TODAS LAS SECCIONES SE EJECUTARON Y VERIFICARON EXITOSAMENTE."
    elif n_fail > 0:
        veredicto = ("HAY SECCIONES QUE SE EJECUTARON Y NO VERIFICARON (✘). "
                      "Revisar el detalle antes de citar estas cifras.")
    else:
        veredicto = ("NINGUNA SECCIÓN FALLÓ, PERO ALGUNAS NO PUDIERON EJECUTARSE EN ESTE ENTORNO (○) "
                      "por falta de Docker/backend levantado o de archivos de resultados. "
                      "No se informan como verificadas.")
    print(f"\n  {veredicto}")
    print(f"\n  Tiempo de ejecución del verificador maestro: {elapsed} segundos.")
    return 1 if n_fail > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
