#!/usr/bin/env python3
from __future__ import annotations
"""Prueba de regresión/consistencia del motor de triaje sobre un conjunto adicional.

Carga las reglas calibradas y la implementación productiva de ``TriageEngine`` y
las ejecuta sobre ``test_orders_regression.json``. El conjunto no intervino en
la calibración, pero sus etiquetas esperadas se derivan de la misma configuración
de reglas; por ello el resultado no constituye validación predictiva independiente.

La función del benchmark es verificar determinismo, reproducibilidad y ausencia
de regresiones sobre casos adicionales.

La ejecucion complementa la medicion de calibracion con un conjunto adicional no utilizado durante la calibracion.

No requiere Docker ni la base de datos. Usa el modulo TriageEngine directamente.

Uso:
    python benchmark/validate_motor.py
    python benchmark/validate_motor.py --config calibrada_fase4 --orders test_orders_regression.json
"""
import argparse
import json
import os
import sys
import unicodedata
from enum import Enum

# ── Configuracion de paths ──────────────────────────────────────────────────
BENCHMARK_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(BENCHMARK_DIR)
DEFAULT_ORDERS = os.path.join(BENCHMARK_DIR, "test_orders_regression.json")

# Soporte para ejecucion local o dentro del contenedor Docker (/app)
if os.path.exists("/app/app/modules/triage"):
    SERVER_DIR = "/app"
    CONFIGS_DIR = "/app/app/modules/triage/configs"
else:
    SERVER_DIR = os.path.join(REPO_ROOT, "server")
    CONFIGS_DIR = os.path.join(REPO_ROOT, "server", "app", "modules", "triage", "configs")

# Mapa de prioridades para comparacion (normalizacion de display vs enum)
PRIORITY_MAP = {
    "critico":    "Crítico",
    "urgente":    "Urgente",
    "prioritario":"Prioritario",
    "rutina":     "Rutina",
}


def _norm(value: str | None) -> str:
    """Normaliza texto para comparar las etiquetas de prioridad sin acentos."""
    if value is None:
        return ""
    return "".join(
        ch for ch in unicodedata.normalize("NFD", str(value).strip().lower())
        if unicodedata.category(ch) != "Mn"
    )



# ── Motor de triaje: implementación de producción ──────────────────────────
# Se utiliza la misma clase TriageEngine del artefacto. El benchmark crea
# objetos mínimos en memoria y no levanta la base de datos.
if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)
# El módulo de configuración del backend exige SECRET_KEY; el benchmark no
# envía ninguna credencial y utiliza este valor solo para inicializar settings
# durante la prueba local. No sustituye la configuración del entorno de ejecución.
os.environ.setdefault("SECRET_KEY", "benchmark-script-only")
os.environ.setdefault("PSEUDONYM_SECRET", "benchmark-script-only")

from types import SimpleNamespace
from app.modules.triage.triage import TriageEngine
from app.modules.triage.model import TriageField, TriageOperator


def build_rule(raw: dict):
    return SimpleNamespace(
        name=raw["name"],
        field=TriageField(raw["field"]),
        operator=TriageOperator(raw["operator"]),
        value=raw["value"],
        weight=raw["weight"],
        enabled=raw.get("enabled", True),
    )


def build_order(raw: dict):
    fields = {
        "modality", "origin_service", "patient_location", "diagnosis",
        "is_urgent", "description", "observations", "study_setting",
    }
    return SimpleNamespace(**{name: raw.get(name) for name in fields})


def build_settings(thresholds: dict):
    return SimpleNamespace(
        triage_critical_threshold=thresholds["critical"],
        triage_urgent_threshold=thresholds["urgent"],
        triage_priority_threshold=thresholds["priority"],
    )


def evaluate_order(order: dict, rules: list, thresholds: dict) -> tuple:
    model_order = build_order(order)
    model_rules = [build_rule(r) for r in rules]
    model_settings = build_settings(thresholds)
    priority, details = TriageEngine.evaluate(model_order, model_rules, model_settings)
    return priority.value, details["total_score"], details["rules_matched"]


# ── Main ────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config",  default="calibrada_fase4",  help="Nombre del config JSON (sin extension)")
    parser.add_argument("--orders",  default=DEFAULT_ORDERS,     help="JSON con ordenes de prueba")
    parser.add_argument("--verbose", action="store_true",        help="Mostrar reglas activadas por orden")
    args = parser.parse_args()

    # Cargar configuracion del motor
    config_path = os.path.join(CONFIGS_DIR, f"{args.config}.json")
    if not os.path.exists(config_path):
        print(f"[ERROR] Config no encontrado: {config_path}")
        sys.exit(1)
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)
    rules      = config["rules"]
    thresholds = config["thresholds"]

    # Cargar ordenes de prueba
    if not os.path.exists(args.orders):
        print(f"[ERROR] Archivo de ordenes no encontrado: {args.orders}")
        sys.exit(1)
    with open(args.orders, encoding="utf-8") as f:
        test_data = json.load(f)
    orders = test_data["orders"]

    print(f"\n{'='*65}")
    print(f"  PRUEBA DE REGRESION / CONSISTENCIA DEL MOTOR DE TRIAJE")
    print(f"  Config: {args.config}  |  Umbrales: {thresholds}")
    print(f"  Ordenes: {len(orders)}  (conjunto NO usado en calibracion)")
    print(f"{'='*65}\n")

    correct = 0
    results = []
    for order in orders:
        predicted, score, matched = evaluate_order(order, rules, thresholds)
        expected_raw = order.get("expected_priority", "")
        expected = PRIORITY_MAP.get(_norm(expected_raw), expected_raw)

        ok = predicted == expected
        if ok:
            correct += 1

        results.append({
            "id": order["id"],
            "expected": expected,
            "predicted": predicted,
            "score": score,
            "ok": ok,
            "matched": matched,
        })

        status = "OK" if ok else "FAIL"
        print(f"  [{status}] {order['id']:10s}  esperado={expected:12s}  predicho={predicted:12s}  score={score:+d}")
        if args.verbose or not ok:
            for m in matched:
                print(f"           regla: {m['rule']:35s}  peso={m['weight']:+d}")
        if not ok:
            print(f"           ^ rationale: {order.get('rationale','')}")

    total = len(orders)
    accuracy = correct / total if total else 0

    print(f"\n{'='*65}")
    print(f"  RESULTADO FINAL")
    print(f"  Aciertos: {correct} / {total}  ({accuracy*100:.1f}%)")
    print(f"{'='*65}")

    # Comparacion con Fase 4 (78.0% sobre conjunto cerrado)
    print(f"\n  Referencia Fase 4 (conjunto de calibracion): 39/50 = 78.0%")
    if accuracy >= 0.78:
        print(f"  -> Consistencia: {accuracy*100:.1f}% de coincidencia con las etiquetas esperadas del conjunto adicional.")
    else:
        diff = 78.0 - accuracy * 100
        print(f"  -> Resultado inferior a la referencia cerrada de Fase 4; no se interpreta como estimación de desempeño predictivo.")

    # Distribucion por prioridad
    print(f"\n  Distribucion de predicciones:")
    from collections import Counter
    dist = Counter(r["predicted"] for r in results)
    for p in ["Crítico", "Urgente", "Prioritario", "Rutina"]:
        n = dist.get(p, 0)
        bar = "#" * n
        print(f"    {p:12s}: {n:2d}  {bar}")

    print()


if __name__ == "__main__":
    main()
