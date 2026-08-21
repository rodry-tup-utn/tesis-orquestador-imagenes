"""
Fase 0 - Ejecución del Motor de Triaje sobre 50 órdenes de evaluación.

Reimplementa la lógica de TriageEngine.evaluate() de forma autocontenida
(sin dependencias de sqlmodel/SQLAlchemy) para facilitar la ejecución
aislada. La lógica es idéntica a server/app/modules/triage/triage.py.

Uso:
    cd tesis-orquestador-imagenes
    python3 benchmark/triage_evaluation/run_engine.py
"""
import csv
import os
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Configuración del motor (replicada del seed y SystemSettings por defecto)
# ---------------------------------------------------------------------------

TRIAGE_CRITICAL_THRESHOLD = 25
TRIAGE_URGENT_THRESHOLD = 12
TRIAGE_PRIORITY_THRESHOLD = 10


@dataclass
class TriageRule:
    id: int
    name: str
    field: str
    operator: str
    value: str
    weight: int
    enabled: bool = True


SEED_RULES = [
    TriageRule(id=1,  name="ACV",                 field="diagnosis",       operator="contains",   value="ACV",          weight=20),
    TriageRule(id=2,  name="Politraumatismo",     field="diagnosis",       operator="contains",   value="politrauma",   weight=18),
    TriageRule(id=3,  name="Hemorragia",          field="diagnosis",       operator="contains",   value="hemorragia",   weight=12),
    TriageRule(id=4,  name="TEP",                 field="diagnosis",       operator="contains",   value="TEP",          weight=10),
    TriageRule(id=5,  name="Colecistitis aguda",  field="diagnosis",       operator="contains",   value="colecistitis", weight=10),
    TriageRule(id=6,  name="Apendicitis",         field="diagnosis",       operator="contains",   value="apendicitis",  weight=10),
    TriageRule(id=7,  name="Fractura",            field="diagnosis",       operator="contains",   value="fractura",     weight=9),
    TriageRule(id=8,  name="Tomografia (CT)",     field="modality",        operator="equals",     value="CT",           weight=6),
    TriageRule(id=9,  name="Resonancia (MR)",     field="modality",        operator="equals",     value="MR",           weight=5),
    TriageRule(id=10, name="Ecografia (US)",      field="modality",        operator="equals",     value="US",           weight=2),
    TriageRule(id=11, name="Radiografia (DX)",    field="modality",        operator="equals",     value="DX",           weight=1),
    TriageRule(id=12, name="Ubicacion en UTI",    field="patient_location",operator="contains",   value="UTI",          weight=6),
    TriageRule(id=13, name="Ubicacion Shock Room",field="patient_location",operator="contains",   value="Shock Room",   weight=8),
    TriageRule(id=14, name="Ubicacion Box Rojo",  field="patient_location",operator="contains",   value="Box Rojo",     weight=6),
    TriageRule(id=15, name="Servicio: Guardia",   field="origin_service",  operator="contains",   value="guardia",      weight=4),
    TriageRule(id=16, name="Servicio: Internacion",field="origin_service", operator="contains",   value="internacion",  weight=4),
    TriageRule(id=17, name="Servicio: Ambulatorio",field="origin_service", operator="contains",   value="ambulatorio",  weight=-50),
    TriageRule(id=18, name="Urgente desde origen", field="is_urgent", operator="equals", value="True", weight=4),
    TriageRule(id=19, name="Control de patología", field="diagnosis", operator="contains", value="control", weight=-5),
    TriageRule(id=20, name="Seguimiento", field="diagnosis", operator="contains", value="seguimiento", weight=-5),
    TriageRule(id=21, name="Evolución", field="diagnosis", operator="contains", value="evolución", weight=-5),
]


# ---------------------------------------------------------------------------
# Lógica del motor (idéntica a triage.py)
# ---------------------------------------------------------------------------

def _matches(field_value: str, operator: str, pattern: str) -> bool:
    if operator == "equals":
        return field_value.lower() == pattern.lower()
    elif operator == "contains":
        return pattern.lower() in field_value.lower()
    elif operator == "startswith":
        return field_value.lower().startswith(pattern.lower())
    return False


def evaluate(order: dict, rules: list[TriageRule]) -> tuple[str, int, list[str]]:
    score = 0
    matched = []
    for rule in rules:
        if not rule.enabled:
            continue
        field_value = order.get(rule.field, "")
        if isinstance(field_value, bool):
            field_value = str(field_value)
        if _matches(str(field_value), rule.operator, rule.value):
            score += rule.weight
            matched.append(f"{rule.field}='{rule.value}'(+{rule.weight})")

    if score >= TRIAGE_CRITICAL_THRESHOLD:
        priority = "Crítico"
    elif score >= TRIAGE_URGENT_THRESHOLD:
        priority = "Urgente"
    elif score >= TRIAGE_PRIORITY_THRESHOLD:
        priority = "Prioritario"
    else:
        priority = "Rutina"

    return priority, score, matched


# ---------------------------------------------------------------------------
# Carga de datos y ejecución
# ---------------------------------------------------------------------------

def load_orders(csv_path: str) -> list[dict]:
    with open(csv_path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def run_engine(orders: list[dict]) -> list[dict]:
    results = []
    for row in orders:
        order = {
            "modality": row["modality"],
            "diagnosis": row["diagnosis"],
            "origin_service": row["origin_service"],
            "patient_location": row["patient_location"],
            "is_urgent": row["is_urgent"].strip(),
        }
        priority, score, matched = evaluate(order, SEED_RULES)
        results.append({
            "order_id": row["order_id"],
            "modality": row["modality"],
            "diagnosis": row["diagnosis"],
            "origin_service": row["origin_service"],
            "patient_location": row["patient_location"],
            "is_urgent": row["is_urgent"].strip(),
            "score": score,
            "engine_priority": priority,
            "rules_matched": "; ".join(matched),
        })
    return results


# ---------------------------------------------------------------------------
# Presentación
# ---------------------------------------------------------------------------

def print_table(results: list[dict]) -> None:
    print("=" * 160)
    print(f"{'ID':<16} {'Mod':<4} {'Diagnóstico':<35} {'Servicio':<13} {'Ubicación':<22} {'Urg':<4} {'Score':>5} {'Motor':<14} {'Reglas activadas'}")
    print("=" * 160)
    for r in results:
        diag = r["diagnosis"][:33] + ".." if len(r["diagnosis"]) > 35 else r["diagnosis"]
        loc = r["patient_location"][:20] + ".." if len(r["patient_location"]) > 22 else r["patient_location"]
        urg = "Sí" if r["is_urgent"] == "True" else "No"
        print(
            f"{r['order_id']:<16} {r['modality']:<4} {diag:<35} {r['origin_service']:<13} {loc:<22} {urg:<4} {r['score']:>5} {r['engine_priority']:<14} {r['rules_matched']}"
        )
    print("=" * 160)


def print_summary(results: list[dict]) -> None:
    dist = {}
    for r in results:
        p = r["engine_priority"]
        dist[p] = dist.get(p, 0) + 1

    print("\n╔══════════════════════════════════════════════╗")
    print("║   DISTRIBUCIÓN DE PRIORIDADES (Motor)        ║")
    print("╠══════════════════════════════════════════════╣")
    for level in ["Crítico", "Urgente", "Prioritario", "Rutina"]:
        count = dist.get(level, 0)
        pct = count / len(results) * 100
        bar = "█" * int(pct / 2)
        print(f"║  {level:<14} {count:>3}  ({pct:5.1f}%)  {bar:<25}║")
    print(f"║  {'TOTAL':<14} {len(results):>3}                         ║")
    print("╚══════════════════════════════════════════════╝")

    scores = [r["score"] for r in results]
    print(f"\n--- Estadísticas de Score ---")
    print(f"  Mínimo:   {min(scores)}")
    print(f"  Máximo:   {max(scores)}")
    print(f"  Promedio: {sum(scores)/len(scores):.1f}")
    print(f"  Mediana:  {sorted(scores)[len(scores)//2]}")

    print(f"\n--- Umbrales configurados ---")
    print(f"  >= {TRIAGE_CRITICAL_THRESHOLD} → Crítico")
    print(f"  >= {TRIAGE_URGENT_THRESHOLD} → Urgente")
    print(f"  >= {TRIAGE_PRIORITY_THRESHOLD} → Prioritario")
    print(f"  <  {TRIAGE_PRIORITY_THRESHOLD} → Rutina")


def print_by_service(results: list[dict]) -> None:
    print("\n--- Distribución por servicio de origen ---")
    services = {}
    for r in results:
        svc = r["origin_service"]
        if svc not in services:
            services[svc] = []
        services[svc].append(r)

    for svc, orders in sorted(services.items()):
        dist = {}
        for o in orders:
            p = o["engine_priority"]
            dist[p] = dist.get(p, 0) + 1
        print(f"\n  {svc} ({len(orders)} órdenes):")
        for level in ["Crítico", "Urgente", "Prioritario", "Rutina"]:
            count = dist.get(level, 0)
            if count > 0:
                print(f"    {level:<14} {count}")


def save_results(results: list[dict], output_path: str) -> None:
    fieldnames = ["order_id", "modality", "diagnosis", "origin_service",
                  "patient_location", "is_urgent", "score", "engine_priority",
                  "rules_matched"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    print(f"\nResultados guardados en: {output_path}")


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, "orders_for_evaluation.csv")
    output_path = os.path.join(base_dir, "engine_results_preliminary.csv")

    orders = load_orders(csv_path)
    print(f"Cargadas {len(orders)} órdenes desde {csv_path}\n")

    results = run_engine(orders)
    print_table(results)
    print_summary(results)
    print_by_service(results)
    save_results(results, output_path)


if __name__ == "__main__":
    main()
