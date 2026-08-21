"""
Análisis de Evaluación del Motor de Triaje.

Calcula:
1. Concordancia entre evaluadores (Fleiss' Kappa)
2. Clasificación gold standard (mayoría)
3. Matriz de confusión motor vs. humano
4. Sensibilidad, especificidad y precisión por nivel
5. Análisis de falsos negativos críticos

Uso:
    cd tesis-orquestador-imagenes

    # Auto-busca CSVs en evaluadores/:
    python3 benchmark/triage_evaluation/analyze.py

    # O pasa explícitamente los archivos:
    python3 benchmark/triage_evaluation/analyze.py evaluadores/eval_1.csv evaluadores/eval_2.csv ...
"""
import csv
import math
import os
import sys
from collections import Counter, defaultdict

LEVELS = ["Crítico", "Urgente", "Prioritario", "Rutina"]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# Carga de datos
# ---------------------------------------------------------------------------

def load_evaluator_results(csv_paths: list[str]) -> dict[str, dict[str, str]]:
    """Carga resultados de múltiples evaluadores. Retorna {order_id: {evaluator: clasificacion}}."""
    # Normalización de tildes por si algún evaluador no las usa
    ACCENT_FIX = {"Critico": "Crítico"}

    evals: dict[str, dict[str, str]] = defaultdict(dict)
    for path in csv_paths:
        name = os.path.splitext(os.path.basename(path))[0]
        with open(path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                oid = row["order_id"].strip()
                cls = row["clasificacion"].strip()
                cls = ACCENT_FIX.get(cls, cls)
                if cls:
                    evals[oid][name] = cls
    return dict(evals)


def load_engine_results(csv_path: str) -> dict[str, str]:
    """Carga resultados del motor. Retorna {order_id: engine_priority}."""
    engine = {}
    with open(csv_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            engine[row["order_id"].strip()] = row["engine_priority"].strip()
    return engine


# ---------------------------------------------------------------------------
# Fleiss' Kappa
# ---------------------------------------------------------------------------

def compute_fleiss_kappa(evaluations: dict[str, dict[str, str]], levels: list[str]) -> float:
    """
    Calcula el kappa de Fleiss para más de 2 evaluadores.
    Referencia: Fleiss, J.L. (1971). Measuring nominal scale agreement
    among many raters. Psychological Bulletin, 76(5), 378-382.
    """
    order_ids = sorted(evaluations.keys())
    n_items = len(order_ids)
    n_raters = len(next(iter(evaluations.values())))
    n_categories = len(levels)

    if n_items == 0 or n_raters < 2:
        return 0.0

    level_to_idx = {l: i for i, l in enumerate(levels)}

    # Build rating matrix: n_items x n_categories
    matrix = []
    for oid in order_ids:
        row = [0] * n_categories
        for cls in evaluations[oid].values():
            if cls in level_to_idx:
                row[level_to_idx[cls]] += 1
        matrix.append(row)

    # P_i = proportion of agreeing pairs for item i
    P_items = []
    for row in matrix:
        ni = sum(row)
        Pi = (sum(ni_val ** 2 for ni_val in row) - ni) / (ni * (ni - 1)) if ni > 1 else 0
        P_items.append(Pi)

    P_bar = sum(P_items) / n_items  # Mean proportion of agreement

    # p_j = proportion of all assignments to category j
    p_j = []
    total_assignments = n_items * n_raters
    for j in range(n_categories):
        pj = sum(matrix[i][j] for i in range(n_items)) / total_assignments
        p_j.append(pj)

    P_e = sum(pj ** 2 for pj in p_j)  # Expected agreement by chance

    if P_e == 1.0:
        return 1.0

    kappa = (P_bar - P_e) / (1 - P_e)
    return kappa


def kappa_interpretation(kappa: float) -> str:
    if kappa < 0.20:
        return "Pobre"
    elif kappa < 0.40:
        return "Regular"
    elif kappa < 0.60:
        return "Moderado"
    elif kappa < 0.80:
        return "Sustancial"
    else:
        return "Casi perfecto"


# ---------------------------------------------------------------------------
# Gold standard (mayoría)
# ---------------------------------------------------------------------------

def compute_gold_standard(evaluations: dict[str, dict[str, str]], levels: list[str]) -> dict[str, str]:
    """Determina la clasificación gold standard por votación mayoritaria."""
    gold = {}
    for oid, evals in evaluations.items():
        counts = Counter(evals.values())
        # Mayoría; en empate, priorizar nivel más alto (Crítico > Urgente > Prioritario > Rutina)
        max_count = max(counts.values())
        candidates = [l for l in levels if counts.get(l, 0) == max_count]
        gold[oid] = candidates[0]  # levels ya está ordenado de mayor a menor
    return gold


# ---------------------------------------------------------------------------
# Matriz de confusión y métricas
# ---------------------------------------------------------------------------

def build_confusion_matrix(gold: dict[str, str], engine: dict[str, str], levels: list[str]) -> list[list[int]]:
    """Construye matriz de confusión: filas = humano (gold), columnas = motor."""
    n = len(levels)
    matrix = [[0] * n for _ in range(n)]
    level_to_idx = {l: i for i, l in enumerate(levels)}

    for oid in gold:
        if oid in engine:
            r = level_to_idx.get(gold[oid])
            c = level_to_idx.get(engine[oid])
            if r is not None and c is not None:
                matrix[r][c] += 1

    return matrix


def compute_metrics(confusion: list[list[int]], levels: list[str]) -> dict[str, dict[str, float]]:
    """Calcula sensibilidad, especificidad y precisión por nivel."""
    n = len(levels)
    metrics = {}

    for i, level in enumerate(levels):
        tp = confusion[i][i]
        fn = sum(confusion[i][j] for j in range(n)) - tp
        fp = sum(confusion[j][i] for j in range(n)) - tp
        tn = sum(confusion[j][k] for j in range(n) for k in range(n)) - tp - fn - fp

        sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        f1 = 2 * precision * sensitivity / (precision + sensitivity) if (precision + sensitivity) > 0 else 0.0

        metrics[level] = {
            "VP": tp, "FN": fn, "FP": fp, "VN": tn,
            "Sensibilidad": round(sensitivity, 4),
            "Especificidad": round(specificity, 4),
            "Precisión": round(precision, 4),
            "F1": round(f1, 4),
        }

    return metrics


def find_critical_false_negatives(gold: dict[str, str], engine: dict[str, str]) -> list[dict]:
    """Identifica órdenes que humanos marcaron como Crítico pero el motor no."""
    fn_critical = []
    for oid in sorted(gold.keys()):
        if gold[oid] == "Crítico" and engine.get(oid) != "Crítico":
            fn_critical.append({
                "order_id": oid,
                "human": gold[oid],
                "engine": engine.get(oid, "N/A"),
            })
    return fn_critical


# ---------------------------------------------------------------------------
# Presentación
# ---------------------------------------------------------------------------

def print_confusion_matrix(matrix: list[list[int]], levels: list[str]) -> None:
    col_width = 12
    header = f"{'Humano \\ Motor':<18}" + "".join(f"{l:>{col_width}}" for l in levels) + f"{'Total':>{col_width}}"
    print(header)
    print("-" * len(header))

    row_totals = []
    for i, level in enumerate(levels):
        row = matrix[i]
        total = sum(row)
        row_totals.append(total)
        cells = "".join(f"{v:>{col_width}}" for v in row)
        print(f"{level:<18}{cells}{total:>{col_width}}")

    col_totals = [sum(matrix[j][i] for j in range(len(levels))) for i in range(len(levels))]
    grand_total = sum(col_totals)
    print("-" * len(header))
    totals_row = "".join(f"{t:>{col_width}}" for t in col_totals) + f"{grand_total:>{col_width}}"
    print(f"{'Total':<18}{totals_row}")


def print_metrics(metrics: dict[str, dict[str, float]], levels: list[str]) -> None:
    print(f"\n{'Nivel':<14} {'Sensibilidad':>12} {'Especificidad':>14} {'Precisión':>10} {'F1':>8} {'VP':>4} {'FN':>4} {'FP':>4}")
    print("-" * 85)
    for level in levels:
        m = metrics[level]
        print(
            f"{level:<14} {m['Sensibilidad']:>12.1%} {m['Especificidad']:>14.1%} "
            f"{m['Precisión']:>10.1%} {m['F1']:>8.1%} {m['VP']:>4} {m['FN']:>4} {m['FP']:>4}"
        )


def save_analysis_summary(gold, engine, confusion, metrics, kappa, fn_critical, levels, output_dir):
    """Guarda un resumen del análisis en un archivo de texto."""
    path = os.path.join(output_dir, "analysis_summary.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("=== ANÁLISIS DE EVALUACIÓN DEL MOTOR DE TRIAJE ===\n\n")

        f.write("--- Concordancia entre evaluadores ---\n")
        f.write(f"Kappa de Fleiss: {kappa:.4f} ({kappa_interpretation(kappa)})\n\n")

        f.write("--- Distribución Gold Standard (mayoría) ---\n")
        gs_counts = Counter(gold.values())
        for level in levels:
            f.write(f"  {level}: {gs_counts.get(level, 0)}\n")
        f.write(f"  Total: {len(gold)}\n\n")

        f.write("--- Distribución Motor ---\n")
        eng_counts = Counter(engine.values())
        for level in levels:
            f.write(f"  {level}: {eng_counts.get(level, 0)}\n")
        f.write(f"  Total: {len(engine)}\n\n")

        f.write("--- Matriz de Confusión ---\n")
        header = f"{'Humano \\ Motor':<18}" + "".join(f"{l:>14}" for l in levels) + "\n"
        f.write(header)
        for i, level in enumerate(levels):
            cells = "".join(f"{confusion[i][j]:>14}" for j in range(len(levels)))
            f.write(f"{level:<18}{cells}\n")
        f.write("\n")

        f.write("--- Métricas por nivel ---\n")
        f.write(f"{'Nivel':<14} {'Sensibilidad':>12} {'Especificidad':>14} {'Precisión':>10} {'F1':>8}\n")
        for level in levels:
            m = metrics[level]
            f.write(
                f"{level:<14} {m['Sensibilidad']:>12.1%} {m['Especificidad']:>14.1%} "
                f"{m['Precisión']:>10.1%} {m['F1']:>8.1%}\n"
            )
        f.write("\n")

        if fn_critical:
            f.write("--- FALSOS NEGATIVOS CRÍTICOS ---\n")
            f.write("Órdenes que humanos clasificaron como Crítico pero el motor NO:\n")
            for fn in fn_critical:
                f.write(f"  {fn['order_id']}: motor={fn['engine']}\n")
        else:
            f.write("--- FALSOS NEGATIVOS CRÍTICOS ---\n")
            f.write("Ninguno detectado.\n")

    print(f"\nResumen guardado en: {path}")


def save_detailed_csv(gold, engine, evaluations, output_dir):
    """Guarda un CSV detallado con la comparación orden por orden."""
    path = os.path.join(output_dir, "detailed_comparison.csv")
    eval_names = sorted(list(next(iter(evaluations.values())).keys())) if evaluations else []

    fieldnames = ["order_id", "gold_standard", "engine_priority", "match"]
    for i, name in enumerate(eval_names, 1):
        fieldnames.append(f"evaluator_{i}")

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()

        for oid in sorted(gold.keys()):
            row = {
                "order_id": oid,
                "gold_standard": gold[oid],
                "engine_priority": engine.get(oid, "N/A"),
                "match": "SI" if gold[oid] == engine.get(oid) else "NO",
            }
            for i, name in enumerate(eval_names, 1):
                row[f"evaluator_{i}"] = evaluations.get(oid, {}).get(name, "")
            writer.writerow(row)

    print(f"Detalle guardado en: {path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def discover_evaluator_csvs() -> list[str]:
    """Auto-descubre CSVs de evaluadores en la subcarpeta evaluadores/."""
    evaluadores_dir = os.path.join(BASE_DIR, "evaluadores")
    if not os.path.isdir(evaluadores_dir):
        return []
    csvs = sorted(
        os.path.join(evaluadores_dir, f)
        for f in os.listdir(evaluadores_dir)
        if f.endswith(".csv")
    )
    return csvs


def main():
    if len(sys.argv) >= 2:
        evaluator_paths = sys.argv[1:]
    else:
        evaluator_paths = discover_evaluator_csvs()
        if not evaluator_paths:
            print("Uso: python3 analyze.py [eval_1.csv eval_2.csv ...]")
            print("O colocá los CSVs en la subcarpeta evaluadores/ y ejecutá sin argumentos.")
            sys.exit(1)
        print(f"Auto-descubiertos {len(evaluator_paths)} CSVs en evaluadores/")

    # Buscar resultados del motor
    engine_path = None
    for candidate in ["engine_results_final.csv", "engine_results_preliminary.csv"]:
        p = os.path.join(BASE_DIR, candidate)
        if os.path.exists(p):
            engine_path = p
            break

    if not engine_path:
        print("Error: No se encontró engine_results_preliminary.csv o engine_results_final.csv")
        sys.exit(1)

    print(f"Cargando resultados de {len(evaluator_paths)} evaluadores...")
    evaluations = load_evaluator_results(evaluator_paths)
    print(f"  {len(evaluations)} órdenes evaluadas")

    print(f"Cargando resultados del motor desde {engine_path}...")
    engine = load_engine_results(engine_path)
    print(f"  {len(engine)} órdenes procesadas por el motor")

    # Concordancia
    print("\n=== CONCORDANCIA ENTRE EVALUADORES ===")
    kappa = compute_fleiss_kappa(evaluations, LEVELS)
    print(f"Kappa de Fleiss: {kappa:.4f} ({kappa_interpretation(kappa)})")

    # Gold standard
    gold = compute_gold_standard(evaluations, LEVELS)
    gs_counts = Counter(gold.values())
    print("\n=== DISTRIBUCIÓN GOLD STANDARD (mayoría) ===")
    for level in LEVELS:
        print(f"  {level:<14} {gs_counts.get(level, 0):>3}")

    # Matriz de confusión
    confusion = build_confusion_matrix(gold, engine, LEVELS)
    print("\n=== MATRIZ DE CONFUSIÓN (Humano vs. Motor) ===")
    print_confusion_matrix(confusion, LEVELS)

    # Métricas
    metrics = compute_metrics(confusion, LEVELS)
    print("\n=== MÉTRICAS POR NIVEL ===")
    print_metrics(metrics, LEVELS)

    # Falsos negativos críticos
    fn_critical = find_critical_false_negatives(gold, engine)
    print(f"\n=== FALSOS NEGATIVOS CRÍTICOS ({len(fn_critical)} casos) ===")
    if fn_critical:
        for fn in fn_critical:
            print(f"  {fn['order_id']}: humano={fn['human']}, motor={fn['engine']}")
    else:
        print("  Ninguno detectado.")

    # Guardar resultados
    save_analysis_summary(gold, engine, confusion, metrics, kappa, fn_critical, LEVELS, BASE_DIR)
    save_detailed_csv(gold, engine, evaluations, BASE_DIR)


if __name__ == "__main__":
    main()
