# Middleware de Orquestación y Triaje para Diagnóstico por Imágenes 🏥🚀

Este proyecto es el Trabajo Final para la **Tecnicatura en Programación (UTN FRM)**. Se trata de un middleware diseñado para centralizar, normalizar y priorizar órdenes médicas provenientes de distintos sistemas hospitalarios hacia un servidor DICOM.

## 🏗️ Arquitectura del Sistema

El sistema utiliza una arquitectura de microservicios orquestada por contenedores:

- **n8n (Orquestador):** Realiza la ingesta de datos (ETL), normalización y lógica de triaje.
- **FastAPI (Backend):** API robusta en Python para la gestión de reglas de negocio y persistencia.
- **PostgreSQL (Base de Datos):** Almacenamiento relacional de pacientes y estados de órdenes.
- **Orthanc (VNA/PACS):** Servidor DICOM para la gestión de la Modality Worklist (MWL).
- **Python Mock Server:** Simulador de APIs hospitalarias (Guardia, Internación, Ambulatorio).
- **React + Vite (Frontend):** Tablero de control para la visualización técnica.

## 🛠️ Requisitos Previos

- [Docker](https://www.docker.com/) y Docker Compose instalados.
- Python 3.10+ (para desarrollo local del backend).
