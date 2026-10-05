#!/usr/bin/env python3
"""Puntaje SUS (System Usability Scale) y desempeno de tareas.

Entrada: CSV con una fila por participante y columnas:
    participant, q1..q10 (1-5), [t1_ok, t1_seg, t2_ok, t2_seg, ...]  (ok = 1/0)
Formulas SUS: items impares (q1,q3,...) aportan (r-1); pares (q2,q4,...) aportan (5-r);
suma * 2,5 -> 0-100. Referencia de la literatura: media 68 (Sauro y Lewis).
Uso: python benchmark/sus_score.py --csv benchmark/templates/sus_PLANTILLA.csv
"""
import argparse, csv, math, statistics

T95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228, 14: 2.145, 19: 2.093, 29: 2.045}


def tcrit(df):
    return T95.get(df) or (2.0 if df > 29 else T95[min(T95, key=lambda k: abs(k - df))])


def sus(r):
    return 2.5 * sum((r[i] - 1) if i % 2 == 0 else (5 - r[i]) for i in range(10))


def grade(s):
    return "excelente" if s >= 80.3 else "bueno" if s >= 68 else "marginal" if s >= 51 else "deficiente"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--csv", required=True); a = ap.parse_args()
    rows = list(csv.DictReader(open(a.csv, newline="", encoding="utf-8-sig")))
    scores = []
    for r in rows:
        q = [int(r[f"q{i}"]) for i in range(1, 11)]
        assert all(1 <= x <= 5 for x in q), f"Respuesta fuera de 1-5 en {r['participant']}"
        scores.append(sus(q))
    n = len(scores); m = statistics.mean(scores); sd = statistics.stdev(scores) if n > 1 else 0.0
    h = tcrit(n - 1) * sd / math.sqrt(n) if n > 1 else 0.0
    print(f"Participantes: {n}\nSUS: media={m:.1f}  mediana={statistics.median(scores):.1f}  sd={sd:.1f}  IC95%=[{m-h:.1f}; {m+h:.1f}]  -> {grade(m)}")
    tasks = sorted({k[:-3] for k in rows[0] if k.endswith("_ok")})
    for t in tasks:
        ok = [int(r[f"{t}_ok"]) for r in rows]; secs = [float(r[f"{t}_seg"]) for r in rows if r.get(f"{t}_seg")]
        print(f"  {t}: exito {sum(ok)}/{len(ok)} = {100*sum(ok)/len(ok):.0f} %" + (f" · tiempo medio {statistics.mean(secs):.1f} s (mediana {statistics.median(secs):.1f})" if secs else ""))


if __name__ == "__main__":
    main()
