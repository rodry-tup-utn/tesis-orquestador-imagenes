## Pruebas de Recuperación ante Fallos

**Fecha:** 2026-09-23
**Escenarios pasados:** 3/5
**Fallidos:** 0
**No ejecutados:** 2

| Escenario | Resultado | T. Recuperación | Datos Perdidos | Notas |
|---|:---:|---:|:---:|---|
| Caída de PostgreSQL → detección y recuperación | ○ | N/D | N/D | No se pudo detener db_hospital en el entorno de prueba. |
| Reinicio del backend → tiempo de reconexión | ✓ | 8,2 s | No | Backend recuperado tras reinicio. |
| Caída temporal de Orthanc → API sigue funcionando | ○ | N/D | N/D | No se pudo detener servidor_dicom en el entorno de prueba. |
| Persistencia de datos ante caída y recuperación de DB | ✓ | 0,0 s | No | Órdenes antes: 1; después: 1. |
| Reinicio completo (backend + DB) → recuperación total | ✓ | 10,0 s | N/D | API respondió HTTP 200 tras el reinicio. |

**Interpretación:** los escenarios marcados como ✓ fueron ejecutados y superados. Los escenarios marcados como ○ no pudieron ejecutarse por una limitación del entorno de prueba y no se computan como fallos ni como éxitos. La campaña caracteriza la recuperación observada bajo las condiciones efectivamente ejecutadas y no constituye una garantía de resiliencia en producción.
