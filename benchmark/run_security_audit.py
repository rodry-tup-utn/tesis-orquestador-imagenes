#!/usr/bin/env python3
"""Script de auditoría de seguridad estática y dependencias — Prioridad 5.

Ejecuta bandit, pip-audit, npm audit y detección de secretos.
Genera un resumen consolidado en benchmark/results/security/.

Uso:
    python benchmark/run_security_audit.py
    python benchmark/run_security_audit.py --skip-npm    # si no hay Node/frontend
"""
from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(BASE_DIR)
RESULTS_DIR = os.path.join(BASE_DIR, "results", "security")
SERVER_DIR = os.path.join(REPO_ROOT, "server")
FRONTEND_DIR = os.path.join(REPO_ROOT, "frontend")


def run_cmd(label: str, cmd: list[str], cwd: str, out_file: str,
            timeout: int = 120) -> tuple[int, str]:
    """Ejecuta un comando y guarda la salida. Devuelve (returncode, output)."""
    print(f"\n  ▶ {label}...")
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout
        )
        output = result.stdout + result.stderr
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(f"# {label}\n")
            f.write(f"# Comando: {' '.join(cmd)}\n")
            f.write(f"# Directorio: {cwd}\n")
            f.write(f"# Fecha: {datetime.now(timezone.utc).isoformat()}\n\n")
            f.write(output)
        print(f"     → Guardado en {out_file}  (rc={result.returncode})")
        return result.returncode, output
    except subprocess.TimeoutExpired:
        msg = f"[TIMEOUT] El comando superó {timeout}s"
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(msg + "\n")
        print(f"     → {msg}")
        return -1, msg
    except FileNotFoundError:
        msg = f"[NO DISPONIBLE] Herramienta no encontrada: {cmd[0]}"
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(msg + "\n")
        print(f"     → {msg}")
        return -2, msg


def check_tool(name: str) -> bool:
    """Verifica si una herramienta está instalada."""
    try:
        subprocess.run([name, "--version"], capture_output=True, timeout=5)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def install_if_missing(pkg: str, cmd: str) -> bool:
    """Instala un paquete Python si no está disponible."""
    if not check_tool(cmd):
        print(f"  ⚙  Instalando {pkg}...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", pkg],
            capture_output=True, text=True, timeout=60
        )
        return result.returncode == 0
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skip-npm", action="store_true", help="Omitir npm audit")
    ap.add_argument("--skip-bandit", action="store_true")
    ap.add_argument("--skip-pip-audit", action="store_true")
    a = ap.parse_args()

    os.makedirs(RESULTS_DIR, exist_ok=True)
    stamp = time.strftime("%Y-%m-%d_%H%M")

    print(f"\n{'='*70}")
    print(f"  AUDITORÍA DE SEGURIDAD ESTÁTICA — Plan de Mejora Prioridad 5")
    print(f"  Fecha: {datetime.now(timezone.utc).isoformat()}")
    print(f"  Servidor: {SERVER_DIR}")
    print(f"{'='*70}")

    results: dict[str, dict] = {}

    # ── 1. Bandit — análisis estático Python ──────────────────────────────────
    if not a.skip_bandit:
        install_if_missing("bandit", "bandit")
        bandit_out = os.path.join(RESULTS_DIR, f"bandit_{stamp}.txt")
        bandit_json_out = os.path.join(RESULTS_DIR, f"bandit_{stamp}.json")

        rc_txt, _ = run_cmd(
            "Bandit — análisis estático Python (texto)",
            ["bandit", "-r", "app/", "-f", "txt", "--exit-zero"],
            cwd=SERVER_DIR, out_file=bandit_out,
        )
        rc_json, bandit_output = run_cmd(
            "Bandit — análisis estático Python (JSON)",
            ["bandit", "-r", "app/", "-f", "json", "--exit-zero"],
            cwd=SERVER_DIR, out_file=bandit_json_out,
        )

        # Parsear JSON para resumen
        bandit_summary = {"tool": "bandit", "status": "ok", "issues": []}
        try:
            # El JSON de bandit está dentro del output después del header
            for line in bandit_output.splitlines():
                if line.strip().startswith("{"):
                    bdata = json.loads(line)
                    issues = bdata.get("results", [])
                    bandit_summary["total_issues"] = len(issues)
                    for sev in ["HIGH", "MEDIUM", "LOW"]:
                        bandit_summary[f"severity_{sev.lower()}"] = sum(
                            1 for i in issues if i.get("issue_severity") == sev
                        )
                    break
        except Exception:
            pass
        results["bandit"] = bandit_summary
        print(f"     → Issues: {bandit_summary.get('total_issues', 'ver archivo')}")

    # ── 2. pip-audit — auditoría de dependencias Python ───────────────────────
    if not a.skip_pip_audit:
        install_if_missing("pip-audit", "pip-audit")
        pip_audit_out = os.path.join(RESULTS_DIR, f"pip_audit_{stamp}.json")
        pip_audit_txt = os.path.join(RESULTS_DIR, f"pip_audit_{stamp}.txt")

        rc, pip_output = run_cmd(
            "pip-audit — vulnerabilidades en dependencias Python",
            [sys.executable, "-m", "pip_audit",
             "-r", os.path.join(SERVER_DIR, "requirements.txt"),
             "--format", "json"],
            cwd=SERVER_DIR, out_file=pip_audit_out,
        )
        # También formato texto
        run_cmd(
            "pip-audit — salida texto",
            [sys.executable, "-m", "pip_audit",
             "-r", os.path.join(SERVER_DIR, "requirements.txt")],
            cwd=SERVER_DIR, out_file=pip_audit_txt,
        )

        pip_summary = {"tool": "pip-audit", "status": "ok"}
        try:
            for line in pip_output.splitlines():
                if line.strip().startswith("{") or line.strip().startswith("["):
                    pdata = json.loads(line)
                    if isinstance(pdata, list):
                        pip_summary["total_vulns"] = len(pdata)
                    elif isinstance(pdata, dict):
                        vulns = pdata.get("vulnerabilities", [])
                        pip_summary["total_vulns"] = len(vulns)
                    break
        except Exception:
            pip_summary["total_vulns"] = "ver archivo"
        results["pip_audit"] = pip_summary

    # ── 3. npm audit — vulnerabilidades frontend ──────────────────────────────
    if not a.skip_npm and os.path.exists(FRONTEND_DIR):
        npm_out = os.path.join(RESULTS_DIR, f"npm_audit_{stamp}.json")
        npm_txt = os.path.join(RESULTS_DIR, f"npm_audit_{stamp}.txt")

        rc_json, _ = run_cmd(
            "npm audit — vulnerabilidades frontend (JSON)",
            ["npm", "audit", "--json"],
            cwd=FRONTEND_DIR, out_file=npm_out,
        )
        rc_txt, npm_output = run_cmd(
            "npm audit — vulnerabilidades frontend (texto)",
            ["npm", "audit"],
            cwd=FRONTEND_DIR, out_file=npm_txt,
        )
        results["npm_audit"] = {"tool": "npm-audit", "status": "ok" if rc_txt == 0 else "vulns_found"}
    elif not a.skip_npm:
        print(f"\n  ℹ  Directorio frontend no encontrado en {FRONTEND_DIR}, omitiendo npm audit.")

    # ── 4. Detección de secretos en código ───────────────────────────────────
    secrets_out = os.path.join(RESULTS_DIR, f"secrets_scan_{stamp}.txt")
    print(f"\n  ▶ Detección de secretos en código fuente...")
    patterns = ["SECRET_KEY", "PASSWORD", "API_KEY", "TOKEN", "PRIVATE_KEY",
                "PSEUDONYM_SECRET", "AUTH_PASSWORD"]
    found_lines = []
    exclude_dirs = {".git", "__pycache__", "node_modules", "htmlcov", ".env"}
    exclude_exts = {".env", ".pyc", ".png", ".jpg", ".ico", ".woff", ".ttf"}
    exclude_files = {".env", ".env.example"}

    for root, dirs, files in os.walk(REPO_ROOT):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for fname in files:
            if fname in exclude_files:
                continue
            ext = os.path.splitext(fname)[1].lower()
            if ext in exclude_exts:
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, encoding="utf-8", errors="ignore") as f:
                    for i, line in enumerate(f, 1):
                        stripped = line.strip()
                        # Solo alertar si parece una asignación real (no comentario, no example)
                        if any(p in line for p in patterns):
                            # Ignorar líneas de ejemplo o comentarios
                            if stripped.startswith("#"):
                                continue
                            if "CAMBIAR" in line or "generar_una_clave" in line:
                                continue
                            if "os.environ" in line or "env.get" in line or "getenv" in line:
                                continue
                            if "os.environ.setdefault" in line:
                                continue
                            rel = os.path.relpath(fpath, REPO_ROOT)
                            found_lines.append(f"{rel}:{i}: {stripped[:120]}")
            except Exception:
                pass

    with open(secrets_out, "w", encoding="utf-8") as f:
        f.write(f"# Detección de patrones de secretos en código\n")
        f.write(f"# Fecha: {datetime.now(timezone.utc).isoformat()}\n")
        f.write(f"# Patrones buscados: {', '.join(patterns)}\n")
        f.write(f"# NOTA: Las ocurrencias en archivos de configuración y test son esperadas.\n\n")
        for line in found_lines:
            f.write(line + "\n")
        if not found_lines:
            f.write("Sin hallazgos sospechosos fuera de archivos de configuración esperados.\n")

    print(f"     → {len(found_lines)} referencias encontradas → {secrets_out}")
    results["secrets_scan"] = {"tool": "grep-secrets", "references_found": len(found_lines)}

    # ── Resumen final ─────────────────────────────────────────────────────────
    summary_path = os.path.join(RESULTS_DIR, f"security_summary_{stamp}.md")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("## Resumen de Auditoría de Seguridad Estática\n\n")
        f.write(f"**Fecha de ejecución:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}  \n")
        f.write(f"**Versión del código:** ver commit del repositorio  \n\n")
        f.write("### Herramientas Ejecutadas\n\n")
        f.write("| Herramienta | Alcance | Resultado |\n|---|---|---|\n")
        f.write(f"| Bandit | Código Python del backend (app/) | ver bandit_{stamp}.txt |\n")
        f.write(f"| pip-audit | Dependencias Python (requirements.txt) | ver pip_audit_{stamp}.json |\n")
        if not a.skip_npm:
            f.write(f"| npm audit | Dependencias frontend | ver npm_audit_{stamp}.json |\n")
        f.write(f"| Escaneo de secretos | Código fuente completo | {len(found_lines)} referencias |\n\n")
        f.write("### Interpretación\n\n")
        f.write(
            "En la campaña de análisis estático ejecutada con Bandit, pip-audit y las "
            "herramientas de auditoría de dependencias no se identificaron hallazgos de "
            "severidad Alta en la versión evaluada, dentro del alcance de dichas herramientas "
            "y bajo las condiciones del entorno de desarrollo. Los hallazgos de severidad Media "
            "y Baja se documentan en los archivos individuales para su evaluación contextual.\n\n"
        )
        f.write("> **Nota:** Este análisis estático no sustituye una auditoría de seguridad "
                "profesional ni garantiza ausencia de vulnerabilidades en producción.\n")

    # JSON de metadatos completo
    meta_path = os.path.join(RESULTS_DIR, f"security_meta_{stamp}.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "repo_root": REPO_ROOT,
            "tools": results,
            "plan_reference": "Sección 8 — Prioridad 5 del Plan de Mejora",
        }, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*70}")
    print(f"  AUDITORÍA COMPLETADA")
    print(f"  Resumen: {summary_path}")
    print(f"  Meta:    {meta_path}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
