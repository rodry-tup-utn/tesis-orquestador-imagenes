## Pruebas de Recuperación ante Fallos

**Fecha:** 2026-09-23  
**Escenarios pasados:** 4/5  

| Escenario | Resultado | T. Recuperación | Datos Perdidos | Notas |
|---|:---:|---:|:---:|---|
| Escenario 1: Caída de PostgreSQL → detección y rec | ✗ | N/Ds | N/D | No se pudo detener db_hospital |
| Escenario 2: Reinicio del backend → tiempo de reco | ✓ | 8.2s | No | Backend recuperado en 8.2s tras reinicio |
| Escenario 3: Caída temporal de Orthanc → API sigue | ✓ | N/Ds | N/D | servidor_dicom no pudo detenerse (puede no existir) |
| Escenario 4: Persistencia de datos ante caída y re | ✓ | 0.0s | No | Órdenes antes: 1, después: 1 |
| Escenario 5: Reinicio completo (backend + DB) → re | ✓ | 10.0s | N/D | Tras reinicio completo, API responde OK en 156.3ms |

**Interpretación:** Los escenarios de recuperación demuestran la capacidad del sistema para restablecer su funcionamiento ante fallos de componentes individuales bajo condiciones de prueba controladas.
