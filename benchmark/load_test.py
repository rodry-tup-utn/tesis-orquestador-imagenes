#!/usr/bin/env python3
"""Prueba de carga concurrente y de disponibilidad sostenida sobre la API.

Complementa a api_latency.py (un cliente, secuencial) con N clientes en paralelo
durante un tiempo dado. Sirve para dos evidencias:
  - RNF-01 bajo concurrencia: P50/P95/P99 por endpoint con N clientes.
  - RNF-02 (disponibilidad): proporcion de respuestas HTTP 200 sobre el total,
    reportada por ventana de un minuto durante una corrida larga (--minutes 240).

Precondiciones: stack levantado, AUTH_USERNAME/AUTH_PASSWORD en .env o entorno.
Uso:
    python benchmark/load_test.py --clients 20 --minutes 5
    python benchmark/load_test.py --clients 10 --minutes 240 --think-ms 500   # soak
No genera ordenes: solo lee. (Cada cliente espera --think-ms entre peticiones.)
"""
import argparse, csv, json, os, statistics, sys, threading, time, urllib.error, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

ENDPOINTS = ["/orders?limit=10&offset=0", "/orders/stats", "/orders/notifications"]


def login(base, user, pwd):
    req = urllib.request.Request(f"{base}/auth/login", data=json.dumps({"username": user, "password": pwd}).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())["access_token"]


def worker(base, token, stop_at, think, out, lock, idx):
    i = idx
    while time.time() < stop_at:
        path = ENDPOINTS[i % len(ENDPOINTS)]; i += 1
        t0 = time.perf_counter(); status = 0
        try:
            req = urllib.request.Request(base + path, headers={"Authorization": f"Bearer {token}"})
            with urllib.request.urlopen(req, timeout=15) as r:
                r.read(); status = r.status
        except urllib.error.HTTPError as e:
            status = e.code
        except Exception:
            status = 0  # timeout / conexion rechazada
        ms = (time.perf_counter() - t0) * 1000
        with lock:
            out.append((time.time(), path, status, ms))
        if think: time.sleep(think)


def pct(v, q):
    return statistics.quantiles(v, n=100, method="inclusive")[q - 1] if len(v) >= 2 else (v[0] if v else float("nan"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--backend", default=os.environ.get("BACKEND_URL", "http://localhost:8000"))
    ap.add_argument("--clients", type=int, default=20)
    ap.add_argument("--minutes", type=float, default=5)
    ap.add_argument("--think-ms", type=int, default=0)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    env = common.load_env()
    user = os.environ.get("AUTH_USERNAME") or env.get("AUTH_USERNAME", "admin")
    pwd = os.environ.get("AUTH_PASSWORD") or env.get("AUTH_PASSWORD", "")
    if not pwd: sys.exit("Falta AUTH_PASSWORD (entorno o .env).")
    token = login(a.backend, user, pwd)

    out, lock = [], threading.Lock()
    t_start = time.time(); stop_at = t_start + a.minutes * 60
    th = [threading.Thread(target=worker, args=(a.backend, token, stop_at, a.think_ms / 1000, out, lock, i)) for i in range(a.clients)]
    [t.start() for t in th]; [t.join() for t in th]
    elapsed = time.time() - t_start

    stamp = time.strftime("%Y-%m-%d")
    path = a.out or os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", f"results_load_{a.clients}c_{stamp}.csv")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["ts", "endpoint", "status", "latency_ms"]); w.writerows(out)

    print(f"\nClientes={a.clients}  duracion={elapsed:.0f}s  peticiones={len(out)}  ({len(out)/elapsed:.1f} req/s)  CSV: {path}")
    total_ok = sum(1 for o in out if o[2] == 200)
    print(f"Disponibilidad global (HTTP 200 / total): {100*total_ok/len(out):.3f} %  errores={len(out)-total_ok}")
    for ep in ENDPOINTS:
        v = [o[3] for o in out if o[1] == ep and o[2] == 200]
        if v:
            q95 = pct(v, 95)
            print(f"  {ep:28s} n={len(v):6d} P50={pct(v,50):7.2f} P95={q95:7.2f} P99={pct(v,99):7.2f} max={max(v):8.2f} ms -> P95<500: {'si' if q95 < 500 else 'NO'}")
    minutes = {}
    for ts, _, st, _ in out:
        m = int((ts - t_start) // 60); minutes.setdefault(m, [0, 0]); minutes[m][1] += 1; minutes[m][0] += (st == 200)
    worst = min((ok / tot, m) for m, (ok, tot) in minutes.items())
    print(f"Peor ventana de 1 min: minuto {worst[1]} con {100*worst[0]:.2f} % de exito ({len(minutes)} ventanas)")
    print("Interpretacion: la disponibilidad aqui es la del API bajo carga sintetica de lectura; no incluye Orthanc ni n8n.")


if __name__ == "__main__":
    main()
