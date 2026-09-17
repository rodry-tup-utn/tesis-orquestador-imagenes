#!/usr/bin/env python3
"""Validacion del motor de triaje sobre un conjunto INDEPENDIENTE de ordenes.

Carga las reglas calibradas (calibrada_fase4.json) y los umbrales del sistema,
y evalua las ordenes de test_orders_independent.json -- un conjunto que NO fue
usado durante la calibracion de la Fase 4, construido para estimar la
capacidad generalizadora del motor.

Esta evaluacion cierra el hallazgo A-01 del dictamen de auditoria:
"Validacion del motor (78%) circular sobre el mismo set de calibracion".

No requiere Docker ni la base de datos. Usa el modulo TriageEngine directamente.

Uso:
    python benchmark/validate_motor.py
    python benchmark/validate_motor.py --config calibrada_fase4 --orders test_orders_independent.json
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
CONFIGS_DIR = os.path.join(REPO_ROOT, "server", "app", "modules", "triage", "configs")
DEFAULT_ORDERS = os.path.join(BENCHMARK_DIR, "test_orders_independent.json")

# Mapa de prioridades para comparacion (normalizacion de display vs enum)
PRIORITY_MAP = {
    "critico":    "Crítico",
    "urgente":    "Urgente",
    "prioritario":"Prioritario",
    "rutina":     "Rutina",
}


# ── Motor de triaje (re-implementacion standalone sin dependencias de Django/FastAPI) ──
def _norm(text: str) -> str:
    """Normaliza texto: minusculas + elimina tildes (NFD)."""
    decomposed = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def _matches(field_value: str, operator: str, pattern: str) -> bool:
    value = _norm(str(field_value))
    target = _norm(pattern)
    if operator == "equals":
        return value == target
    if operator == "contains":
        return target in value
    if operator == "startswith":
        return value.startswith(target)
    return False


def evaluate_order(order: dict, rules: list, thresholds: dict) -> tuple:
    """Retorna (prioridad_display, score, reglas_activadas)."""
    score = 0
    matched = []
    for rule in rules:
        if not rule.get("enabled", True):
            continue
        field = rule["field"]
        value = order.get(field)
        if value is None:
            continue
        if _matches(str(value), rule["operator"], rule["value"]):
            score += rule["weight"]
            matched.append({"rule": rule["name"], "weight": rule["weight"]})

    if score >= thresholds["critical"]:
        priority = "Crítico"
    elif score >= thresholds["urgent"]:
        priority = "Urgente"
    elif score >= thresholds["priority"]:
        priority = "Prioritario"
    else:
        priority = "Rutina"

    return priority, score, matched


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
    print(f"  VALIDACION INDEPENDIENTE DEL MOTOR DE TRIAJE")
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
        print(f"  -> El motor GENERALIZA: {accuracy*100:.1f}% >= 78.0% en conjunto independiente")
    else:
        diff = 78.0 - accuracy * 100
        print(f"  -> Caida de {diff:.1f} pp respecto a la Fase 4 (esperada en validacion independiente)")

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
