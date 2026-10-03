"""Verificación estructural de la entrega V10.6 reparada.

Comprueba la presencia y coherencia de los artefactos de evidencia incluidos en el ZIP.
No sustituye una ejecución funcional completa del stack Docker. Los resultados negativos
de carga son evidencia de límite observado y los escenarios no ejecutados se mantienen
como NO EJECUTADOS.
"""
from __future__ import annotations
import ast, builtins, csv, json, re, statistics, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def test_count(path:Path)->int:
    tree=ast.parse(path.read_text(encoding='utf-8'))
    return sum(isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name.startswith('test_') for n in ast.walk(tree))

def undefined_names(path:Path)->list[str]:
    tree=ast.parse(path.read_text(encoding='utf-8'))
    defined=set(dir(builtins))|{'__file__'}
    for n in ast.walk(tree):
        if isinstance(n,(ast.Import,ast.ImportFrom)):
            defined.update((a.asname or a.name).split('.')[0] for a in n.names)
        elif isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
            defined.add(n.name)
        elif isinstance(n,ast.arg): defined.add(n.arg)
        elif isinstance(n,ast.Name) and isinstance(n.ctx,(ast.Store,ast.Del)): defined.add(n.id)
        elif isinstance(n,ast.ExceptHandler) and n.name: defined.add(n.name)
    return sorted({n.id for n in ast.walk(tree) if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Load) and n.id not in defined})

def p95(v): return statistics.quantiles(v,n=100,method='inclusive')[94]
def rows(p):
    with p.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))

def main()->int:
    res=ROOT/'benchmark'/'results'
    required=[
      ROOT/'docker-compose.yml',ROOT/'README.md',ROOT/'REPRODUCIBILITY.md',ROOT/'VERIFY_DELIVERY.py',
      res/'results_api_latency_2026-09-20.csv',res/'results_ws_latency_extended_n50_2026-09-23.csv',
      res/'results_worklist_equivalence_2026-09-20.csv',res/'results_worklist_equivalence_extended_2026-09-23.csv',
      res/'load_suite'/'results'/'load_consolidated_2026-09-23.json',res/'load_suite'/'results'/'load_consolidated_2026-09-23.md',res/'diagnostico'/'README_A03.md',res/'soak_test_report_extended_2026-09-23.json',res/'soak_test'/'raw'/'soak_2026-09-23_1540.csv',ROOT/'server'/'requirements.lock',
      res/'resilience'/'raw'/'resilience_2026-09-23_1529.json',ROOT/'benchmark'/'test_orders_regression.json']
    miss=[str(x.relative_to(ROOT)) for x in required if not x.exists()]
    if miss: print('FALTAN:\n'+'\n'.join(miss)); return 1
    test_files=sorted((ROOT/'server'/'tests').glob('test_*.py'))
    counts={str(p.relative_to(ROOT)):test_count(p) for p in test_files}; total_tests=sum(counts.values())
    regression=json.loads((ROOT/'benchmark'/'test_orders_regression.json').read_text(encoding='utf-8'))
    regression_n=len(regression.get('orders',[]))
    api=rows(res/'results_api_latency_2026-09-20.csv'); by={}
    for r in api:
        if r['status']=='200': by.setdefault(r['endpoint'],[]).append(float(r['latency_ms']))
    api_p95={k:round(p95(v),2) for k,v in by.items()}
    ws=rows(res/'results_ws_latency_extended_n50_2026-09-23.csv'); wsv=[float(r['latency_ms']) for r in ws]
    wl=rows(res/'results_worklist_equivalence_2026-09-20.csv'); wlf=[k for k in wl[0] if k.endswith('_ok')] if wl else []
    wle=rows(res/'results_worklist_equivalence_extended_2026-09-23.csv'); wlef=[k for k in wle[0] if k.endswith('_ok')] if wle else []
    wl_bad=sum(r[k]!='True' for r in wl for k in wlf); wle_bad=sum(r[k]!='True' for r in wle for k in wlef)
    load=json.loads((res/'load_suite'/'results'/'load_consolidated_2026-09-23.json').read_text(encoding='utf-8')); lv=load.get('results',[])
    load_ok=([x.get('clients') for x in lv]==[1,5,10,25,50] and all(all(k in x for k in ('total_requests','successful','failed','error_rate_pct','attempt_rate_rps')) for x in lv) and lv[3].get('interpretable_for_load_capacity') is False and lv[4].get('interpretable_for_load_capacity') is False and 'overlap' in load.get('interpretation_scope','').lower())
    soak=json.loads((res/'soak_test_report_extended_2026-09-23.json').read_text(encoding='utf-8')); soak_rows=rows(res/'soak_test'/'raw'/'soak_2026-09-23_1540.csv'); soak_lat=[float(r['latency_ms']) for r in soak_rows if r.get('status')=='200']; soak_ok=(len(soak_rows)==1548 and len(soak_lat)==1548 and all(r.get('status')=='200' for r in soak_rows) and abs(p95(soak_lat)-20.0825)<0.05 and 'DICOM' in soak.get('scope_note',''))
    rr=json.loads((res/'resilience'/'raw'/'resilience_2026-09-23_1529.json').read_text(encoding='utf-8')).get('results',[])
    rp=sum(x.get('passed') is True for x in rr); rf=sum(x.get('passed') is False for x in rr); rn=sum(x.get('passed') is None for x in rr)
    notifier=(ROOT/'server'/'app'/'modules'/'medical_order'/'notifier.py').read_text(encoding='utf-8')
    m=re.search(r'def _build_payload\(.*?\n    async def notify',notifier,re.S); block=m.group(0) if m else ''
    privacy_backend=('patient_pseudonym' in block and 'patient_name' not in block and 'patient_dni' not in block)
    wf=json.loads((ROOT/'n8n-workflow'/'Alertas Criticas.json').read_text(encoding='utf-8')); texts=[n.get('parameters',{}).get('text','') for n in wf.get('nodes',[]) if n.get('type')=='n8n-nodes-base.telegram']
    privacy_wf=any('patient_pseudonym' in t and 'patient_name' not in t and 'patient_dni' not in t for t in texts)
    requirements = (ROOT/'server'/'requirements.txt').read_text(encoding='utf-8')
    requirements_lock = (ROOT/'server'/'requirements.lock').read_text(encoding='utf-8')
    pinned_lines=[ln.strip() for ln in requirements.splitlines() if ln.strip() and not ln.strip().startswith('#')]
    lock_lines=[ln.strip() for ln in requirements_lock.splitlines() if ln.strip() and not ln.strip().startswith('#')]
    deps_ok=bool(pinned_lines) and all(re.match(r'^[A-Za-z0-9_.-]+==[^=\s]+$', ln) for ln in pinned_lines) and all(ln in lock_lines for ln in pinned_lines)
    telegram_hardcoded = bool(re.search(r'\"chatId\"\s*:\s*\"(?!=)[^\"]+\"', (ROOT/'n8n-workflow'/'Alertas Criticas.json').read_text(encoding='utf-8')))
    compose=(ROOT/'docker-compose.yml').read_text(encoding='utf-8'); config=(ROOT/'server'/'app'/'core'/'config.py').read_text(encoding='utf-8'); ws_src=(ROOT/'server'/'app'/'core'/'websocket.py').read_text(encoding='utf-8')
    robust=('healthcheck:' in compose and 'condition: service_healthy' in compose and 'postgres_password: str' in config and 'postgres_password: str = "admin"' not in config and 'dead_connections' in ws_src)
    probs={}
    for p in sorted((ROOT/'benchmark').glob('*.py')):
        try:n=undefined_names(p)
        except SyntaxError as e:n=[f'SyntaxError: {e}']
        if n: probs[p.name]=n
    panel=subprocess.run([sys.executable,str(ROOT/'benchmark'/'verify_chapter6_panel.py')],capture_output=True,text=True,cwd=str(ROOT)); panel_ok=panel.returncode==0
    env_ok=not any(p.name=='.env' for p in ROOT.rglob('.env'))
    stale_cov=not (ROOT/'server'/'.coverage').exists()
    deps_files_ok=deps_ok and (ROOT/'server'/'requirements.lock').exists() and not telegram_hardcoded
    a03_note=(res/'diagnostico'/'README_A03.md').read_text(encoding='utf-8').lower()
    a03_ok=('failed' in a03_note and 'no se inventa una causa' in a03_note)

    # The package must not contain the obsolete interpretation that the 25/50 errors are load limits.
    stale_texts=[]
    for p in ROOT.rglob('*'):
        if p.is_file() and p.name != 'VERIFY_DELIVERY.py' and p.suffix.lower() in {'.md','.py','.yml','.txt'}:
            try: t=p.read_text(encoding='utf-8').lower()
            except UnicodeDecodeError: continue
            if 'caracterización sintética de límites' in t or 'caracteriza límites bajo carga' in t:
                stale_texts.append(str(p.relative_to(ROOT)))
    stale_claims_ok=not stale_texts
    print(f'Suite V10.6: {total_tests} tests -> {"OK" if total_tests==101 else "REVISAR"}')
    print('Desglose:',counts)
    print(f'Regresión: {regression_n} -> {"OK" if regression_n==50 else "REVISAR"}')
    print('RNF-01 P95:',api_p95)
    print(f'RF-04 N={len(ws)} P95={p95(wsv):.2f} ms')
    print(f'DICOM: {len(wl)} órdenes/140 checks; extendido {len(wle)}/350 -> {"OK" if wl_bad==0 and wle_bad==0 else "REVISAR"}')
    print(f'Carga: {"OK" if load_ok else "REVISAR"}; los errores observados a 25/50 clientes se conservan como resultado experimental')
    print(f'Soak API: {len(soak_rows)} requests; {sum(r.get("status")=="200" for r in soak_rows)/len(soak_rows)*100 if soak_rows else 0:.1f}% HTTP 200; P95={p95(soak_lat):.2f} ms -> {"OK" if soak_ok else "REVISAR"}')
    print(f'Resiliencia: {rp} PASS / {rf} FAIL / {rn} NO EJECUTADO')
    print(f'Privacidad: {"OK" if privacy_backend and privacy_wf else "REVISAR"}; Robustez: {"OK" if robust else "REVISAR"}')
    print(f'Bench scripts: {"OK" if not probs else probs}; Capítulo 6: {"OK" if panel_ok else "REVISAR"}')
    print(f'Entrega sin .env: {"OK" if env_ok else "REVISAR"}; sin .coverage residual: {"OK" if stale_cov else "REVISAR"}; dependencias/Telegram: {"OK" if deps_files_ok else "REVISAR"}; A-03: {"OK" if a03_ok else "REVISAR"}; claims carga: {"OK" if stale_claims_ok else stale_texts}')
    ok=(total_tests==101 and regression_n==50 and len(api)==600 and len(ws)==50 and len(wl)==20 and len(wle)==50 and wl_bad==0 and wle_bad==0 and load_ok and soak_ok and rf==0 and privacy_backend and privacy_wf and robust and not probs and panel_ok and env_ok and stale_cov and deps_files_ok and a03_ok and stale_claims_ok)
    print('VERIFICACIÓN ESTRUCTURAL:', 'OK' if ok else 'REVISAR')
    return 0 if ok else 1
if __name__=='__main__': raise SystemExit(main())
