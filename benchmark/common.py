"""Utilidades compartidas para los scripts de medicion del Escenario B."""
import os
import re
import subprocess
import time
from datetime import datetime, timezone

METRIC_RE = re.compile(r"METRIC\s+(\S+)\s*(.*)")


def now_ms() -> int:
    return int(time.time() * 1000)


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def repo_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_env() -> dict:
    env = {}
    env_file = os.path.join(repo_root(), ".env")
    if os.path.exists(env_file):
        with open(env_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def parse_metric_line(line: str):
    """Devuelve (nombre, {campos}) o None si la linea no es METRIC."""
    m = METRIC_RE.search(line)
    if not m:
        return None
    name = m.group(1)
    fields = {}
    for k, v in re.findall(r"(\w+)=([\w.\-]+)", m.group(2)):
        fields[k] = v
    return name, fields


def fetch_metric_lines(service: str, since_iso: str, needle: str = "") -> list:
    """Extrae las lineas METRIC del log de un servicio docker desde since_iso."""
    cmd = ["docker", "compose", "logs", "--timestamps", f"--since={since_iso}", service]
    proc = subprocess.run(cmd, cwd=repo_root(), capture_output=True, text=True)
    out = proc.stdout + proc.stderr
    parsed = []
    for raw in out.splitlines():
        if needle and needle not in raw:
            continue
        hit = parse_metric_line(raw)
        if hit:
            parsed.append(hit)
    return parsed


def truncate_orders(env: dict) -> None:
    """Limpia las tablas de ordenes para que cada ciclo procese datos frescos."""
    user = env.get("DB_USER") or "admin"
    db = env.get("DB_NAME") or "orquestador_db"
    cmd = [
        "docker", "compose", "exec", "-T", "postgres", "psql",
        "-U", user, "-d", db,
        "-c", "TRUNCATE TABLE medicalorder, notificacionemitida RESTART IDENTITY CASCADE;",
    ]
    subprocess.run(cmd, cwd=repo_root(), check=True, capture_output=True, text=True)
