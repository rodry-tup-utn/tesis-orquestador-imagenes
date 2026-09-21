"""Verificación estructural de la entrega de software.

No reemplaza una ejecución funcional del stack Docker. Comprueba que los artefactos
mínimos de la entrega estén presentes, que el recuento estático de tests sea coherente
y que los CSV de evidencia tengan los tamaños documentados.
"""
from __future__ import annotations

import ast
import builtins
import csv
import json
import math
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def test_count(path: Path) -> int:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return sum(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")
        for node in ast.walk(tree)
    )


def undefined_names(path: Path) -> list[str]:
    """Nombres leidos que no se definen en ningun lugar del modulo (detecta NameError obvios)."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    defined = set(dir(builtins)) | {"__file__"}
    for n in ast.walk(tree):
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            defined.update((a.asname or a.name).split(".")[0] for a in n.names)
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defined.add(n.name)
        elif isinstance(n, ast.arg):
            defined.add(n.arg)
        elif isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)):
            defined.add(n.id)
        elif isinstance(n, ast.ExceptHandler) and n.name:
            defined.add(n.name)
    return sorted({n.id for n in ast.walk(tree)
                   if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) and n.id not in defined})


def p95(values: list[float]) -> float:
    return statistics.quantiles(values, n=100, method="inclusive")[94]


def csv_rows(path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as fh:
        return sum(1 for _ in csv.DictReader(fh))


def main() -> int:
    required = [
        ROOT / "docker-compose.yml",
        ROOT / "README.md",
        ROOT / "REPRODUCIBILITY.md",
        ROOT / "benchmark" / "results" / "results_api_latency_2026-09-20.csv",
        ROOT / "benchmark" / "results" / "results_ws_latency_2026-09-20.csv",
        ROOT / "benchmark" / "results" / "results_worklist_equivalence_2026-09-20.csv",
        ROOT / "benchmark" / "test_orders_regression.json",
        ROOT / "server" / "tests" / "test_triage_engine.py",
        ROOT / "server" / "tests" / "test_security.py",
    ]
    missing = [str(p.relative_to(ROOT)) for p in required if not p.exists()]
    if missing:
        print("FALTAN:")
        print("\n".join(missing))
        return 1

    engine_tests = test_count(ROOT / "server" / "tests" / "test_triage_engine.py")
    security_tests = test_count(ROOT / "server" / "tests" / "test_security.py")
    regression = json.loads((ROOT / "benchmark" / "test_orders_regression.json").read_text(encoding="utf-8"))
    api_rows = csv_rows(ROOT / "benchmark" / "results" / "results_api_latency_2026-09-20.csv")
    ws_rows = csv_rows(ROOT / "benchmark" / "results" / "results_ws_latency_2026-09-20.csv")
    wl_rows = csv_rows(ROOT / "benchmark" / "results" / "results_worklist_equivalence_2026-09-20.csv")

    # Verificación estructural de minimización del payload externo de alertas.
    notifier_source = (ROOT / "server" / "app" / "modules" / "medical_order" / "notifier.py").read_text(encoding="utf-8")
    m = re.search(r"def _build_payload\(.*?\n    async def notify", notifier_source, re.S)
    payload_block = m.group(0) if m else ""
    privacy_backend_ok = (
        "patient_pseudonym" in payload_block
        and "patient_name" not in payload_block
        and "patient_dni" not in payload_block
    )

    workflow = json.loads((ROOT / "n8n-workflow" / "Alertas Criticas.json").read_text(encoding="utf-8"))
    telegram_texts = [
        node.get("parameters", {}).get("text", "")
        for node in workflow.get("nodes", [])
        if node.get("type") == "n8n-nodes-base.telegram"
    ]
    privacy_workflow_ok = any(
        "patient_pseudonym" in txt and "patient_name" not in txt and "patient_dni" not in txt
        for txt in telegram_texts
    )

    # 1) Todos los scripts de benchmark compilan y no leen nombres indefinidos.
    script_problems = {}
    for script in sorted((ROOT / "benchmark").glob("*.py")):
        try:
            names = undefined_names(script)
        except SyntaxError as exc:
            names = [f"SyntaxError: {exc}"]
        if names:
            script_problems[script.name] = names

    # 2) Las cifras documentadas se recomputan desde los CSV crudos.
    res = ROOT / "benchmark" / "results"
    api = list(csv.DictReader((res / "results_api_latency_2026-09-20.csv").open(encoding="utf-8")))
    by_ep: dict[str, list[float]] = {}
    for r in api:
        if r["status"] == "200":
            by_ep.setdefault(r["endpoint"], []).append(float(r["latency_ms"]))
    api_p95 = [round(p95(v), 2) for v in by_ep.values()]
    ws = [float(r["latency_ms"]) for r in csv.DictReader((res / "results_ws_latency_2026-09-20.csv").open(encoding="utf-8"))]
    ws_mean, ws_med = round(statistics.mean(ws), 2), round(statistics.median(ws), 2)
    ws_half = 2.262 * statistics.stdev(ws) / math.sqrt(len(ws))
    ws_ci = (round(statistics.mean(ws) - ws_half, 2), round(statistics.mean(ws) + ws_half, 2))
    wl = list(csv.DictReader((res / "results_worklist_equivalence_2026-09-20.csv").open(encoding="utf-8")))
    wl_fields = [k for k in wl[0] if k.endswith("_ok")]
    wl_bad = sum(1 for r in wl for k in wl_fields if r[k] != "True")
    figures_ok = (
        api_p95 == [11.57, 16.08, 10.36]
        and (ws_mean, ws_med, ws_ci) == (43.64, 26.71, (7.93, 79.34))
        and len(wl) * len(wl_fields) == 140 and wl_bad == 0
    )

    print(f"Scripts de benchmark sin nombres indefinidos: {'OK' if not script_problems else script_problems}")
    # 2 bis) Capitulo 6: se reconstruye el patron de referencia y la concordancia
    # de E02/E09/E12 unicamente a partir de las tablas crudas del panel (Anexo V).
    import subprocess
    panel_check = subprocess.run(
        [sys.executable, str(ROOT / "benchmark" / "verify_chapter6_panel.py")],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    panel_ok = panel_check.returncode == 0
    print(f"Capítulo 6 recomputado desde panel_votos_50_ordenes.csv y motor_salida_fases_50_ordenes.csv: "
          f"{'OK' if panel_ok else 'REVISAR'}")
    if not panel_ok:
        print(panel_check.stdout[-1500:], panel_check.stderr[-1500:])

    print(f"Cifras recomputadas (RNF-01 {api_p95}; RF-04 {ws_mean}/{ws_med}/{ws_ci}; mapeo {len(wl)*len(wl_fields)-wl_bad}/{len(wl)*len(wl_fields)}): {'OK' if figures_ok else 'REVISAR'}")
    print(f"Pruebas del motor: {engine_tests}")
    print(f"Pruebas de seguridad: {security_tests}")
    print(f"Total estático: {engine_tests + security_tests}")
    print(f"Regresión adicional: {len(regression['orders'])} órdenes")
    print(f"RNF-01: {api_rows} observaciones")
    print(f"RF-04: {ws_rows} observaciones")
    print(f"BD ↔ DICOM: {wl_rows} órdenes auditadas")
    print(f"Privacidad de alerta (payload/backend): {'OK' if privacy_backend_ok else 'REVISAR'}")
    print(f"Privacidad de alerta (workflow Telegram): {'OK' if privacy_workflow_ok else 'REVISAR'}")

    ok = (
        engine_tests == 34
        and security_tests == 6
        and len(regression["orders"]) == 27
        and api_rows == 600
        and ws_rows == 10
        and wl_rows == 20
        and privacy_backend_ok
        and privacy_workflow_ok
        and not script_problems
        and figures_ok
        and panel_ok
    )
    print("VERIFICACIÓN ESTRUCTURAL:", "OK" if ok else "REVISAR")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
