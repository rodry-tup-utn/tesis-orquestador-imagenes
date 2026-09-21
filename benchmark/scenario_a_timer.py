#!/usr/bin/env python3
"""Cronometro para medir el Escenario A (carga manual, TCM) con varios operadores.

Cada operador carga N ordenes en el equipo de modalidad, una por vez. Para cada
orden: Enter = iniciar, Enter = detener. Se guarda UN REGISTRO POR ORDEN
(la limitacion declarada del TCM actual es que no se conservo el registro por ciclo).
Uso: python benchmark/scenario_a_timer.py --operator OP1 --orders 10
     python benchmark/scenario_a_timer.py --summary
"""
import argparse, csv, glob, math, os, statistics, time

DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
T95 = {2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228, 14: 2.145, 19: 2.093, 29: 2.045}


def summary():
    rows = []
    for p in sorted(glob.glob(os.path.join(DIR, "results_tcm_*.csv"))):
        rows += list(csv.DictReader(open(p, encoding="utf-8")))
    if not rows: print("Sin registros en results/results_tcm_*.csv"); return
    ops = sorted({r["operator"] for r in rows}); allv = [float(r["seconds"]) for r in rows]
    for o in ops:
        v = [float(r["seconds"]) for r in rows if r["operator"] == o]
        print(f"  {o}: n={len(v)} media={statistics.mean(v):.1f} s sd={statistics.stdev(v) if len(v)>1 else 0:.1f}")
    n = len(allv); m = statistics.mean(allv); sd = statistics.stdev(allv)
    df = n - 1; t = T95.get(df) or (2.0 if df > 29 else 2.045)
    print(f"TOTAL: operadores={len(ops)} n={n} media={m:.1f} s mediana={statistics.median(allv):.1f} sd={sd:.1f} IC95%(t, ordenes)=[{m - t*sd/math.sqrt(n):.1f}; {m + t*sd/math.sqrt(n):.1f}]")
    print("Nota: el IC trata cada orden como independiente; con pocos operadores conviene reportar tambien la media por operador.")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--operator"); ap.add_argument("--orders", type=int, default=10); ap.add_argument("--summary", action="store_true")
    a = ap.parse_args()
    if a.summary: return summary()
    if not a.operator: ap.error("--operator es obligatorio")
    os.makedirs(DIR, exist_ok=True)
    path = os.path.join(DIR, f"results_tcm_{a.operator}_{time.strftime('%Y-%m-%d')}.csv"); new = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new: w.writerow(["operator", "order_no", "seconds", "timestamp"])
        for i in range(1, a.orders + 1):
            input(f"[{a.operator}] Orden {i}/{a.orders}: Enter para INICIAR...")
            t0 = time.perf_counter(); input("   Enter para DETENER...")
            s = time.perf_counter() - t0; w.writerow([a.operator, i, f"{s:.2f}", time.strftime("%H:%M:%S")]); f.flush()
            print(f"   {s:.1f} s")
    print("Listo. Resumen: python benchmark/scenario_a_timer.py --summary")


if __name__ == "__main__":
    main()
