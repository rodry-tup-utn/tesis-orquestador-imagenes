import logging
import sys
import time

metrics_logger = logging.getLogger("metrics")
metrics_logger.setLevel(logging.INFO)
if not metrics_logger.handlers:
    _handler = logging.StreamHandler(sys.stdout)
    _handler.setFormatter(logging.Formatter("%(message)s"))
    metrics_logger.addHandler(_handler)
metrics_logger.propagate = False


def now_ms() -> float:
    """Timestamp de pared actual en milisegundos (epoch).

    Usa el reloj del host (compartido por n8n y el backend dentro de Docker),
    por lo que es comparable con Date.now() en los scripts de n8n.
    """
    return time.time() * 1000


def log_metric(name: str, **fields) -> None:
    """Emite una linea METRIC con formato clave=valor para facilitar su
    extraccion desde los logs del contenedor.

    Ejemplo: METRIC t_proc cycle_id=T-001 t_received=... T_server=...
    """
    parts = " ".join(f"{k}={v}" for k, v in fields.items())
    metrics_logger.info("METRIC %s %s", name, parts)
