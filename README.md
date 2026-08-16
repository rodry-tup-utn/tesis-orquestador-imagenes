# Middleware de Orquestación y Triaje para Diagnóstico por Imágenes 🏥🚀

![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/postgresql-4169e1?style=for-the-badge&logo=postgresql&logoColor=white)
![React](https://img.shields.io/badge/react-%2320232a.svg?style=for-the-badge&logo=react&logoColor=%2361DAFB)
![n8n](https://img.shields.io/badge/n8n-FF6600?style=for-the-badge&logo=n8n&logoColor=white)

Este proyecto es el Trabajo Integrador Final para la **Tecnicatura Universitaria en Programación (UTN FRM)**. Se trata de un middleware no invasivo basado en microservicios, diseñado para centralizar, normalizar y priorizar automáticamente órdenes médicas provenientes de distintos sistemas hospitalarios (HIS) heterogéneos, integrándolos hacia un servidor PACS/DICOM y emitiendo alertas críticas en tiempo real.

---

## 🏗️ Arquitectura y Stack Tecnológico

El sistema utiliza una arquitectura orientada a microservicios orquestada íntegramente mediante contenedores Docker:

*   **n8n (Orquestador ETL):** Realiza la ingesta automatizada de datos (mediante polling HTTP GET no invasivo), normalización semántica y empuje de lotes hacia el backend.
*   **FastAPI + PostgreSQL (Motor de Triaje):** API REST asíncrona que valida datos con Pydantic, aplica reglas configurables de triaje (Niveles: Crítico, Urgente, Prioritario, Rutinario) y persiste el estado.
*   **Orthanc (VNA/PACS):** Servidor DICOM que expone el servicio de *Modality Worklist* (MWL) para que los resonadores/tomógrafos consuman la lista de pacientes.
*   **React + Vite (Tablero SPA):** Frontend (Feature-Sliced Design) servido vía Nginx, con actualizaciones en tiempo real (WebSockets) para monitoreo de la cola de trabajo clínica.
*   **Telegram Bot API:** Subsistema asíncrono para notificaciones proactivas al equipo médico con datos de pacientes seudonimizados (SHA-256).
*   **Python Mock Server:** Simulador que emula APIs de sistemas HIS (Guardia, Internación, Ambulatorio) generando escenarios de prueba sintéticos.

---

## 🛠️ Requisitos Previos

Para ejecutar el proyecto, tu entorno debe contar con:
*   [Docker Engine](https://docs.docker.com/get-docker/) y Docker Compose (versión >= 2.24).
*   Git.

---

## 🚀 Guía Rápida de Instalación y Despliegue

Sigue estos pasos cuidadosamente para levantar el entorno completo desde cero (ideal para pruebas o demostraciones).

### 1. Variables de Entorno
Asegúrate de que el archivo `.env` exista en la raíz del proyecto `tesis-orquestador-imagenes` (puedes usar `.env.example` como plantilla) con tus credenciales de base de datos y Orthanc.

### 2. Levantar la Infraestructura
Abre tu terminal en la carpeta raíz del proyecto y ejecuta:

```bash
docker compose up -d --build
```
> Esto construirá la imagen de desarrollo del Frontend (Vite), el Backend (FastAPI), y descargará las imágenes de Postgres, n8n, Mock Server y Orthanc. Las migraciones de la base de datos se aplicarán automáticamente.
>
> El Frontend corre en modo desarrollo con **Hot Module Replacement (HMR)**: los cambios en `frontend/src` se ven al instante sin rebuild. Ingresa a [http://localhost:5173](http://localhost:5173).

### 3. Configurar el Orquestador (n8n)
La primera vez que n8n inicie, estará "en blanco".
1. Ingresa a [http://localhost:5678](http://localhost:5678) y crea una cuenta de administrador local.
2. Ve a **Workflows** > **Add Workflow**.
3. En el menú superior derecho (`...`), selecciona **Import from File**.
4. Importa el archivo `n8n-workflow/Orquestador Imagenes.json`, guárdalo y **actívalo** (Toggle "Active").
5. Repite el paso para el archivo `n8n-workflow/Alertas Criticas.json`.

### 4. Configurar el Bot de Alertas (Telegram)
Para recibir alertas sobre pacientes en estado "Crítico":
1. En Telegram, busca a `@BotFather`, envía `/newbot` y sigue los pasos para obtener un **Token de Acceso**.
2. En n8n, abre el flujo **Alertas Criticas** y haz doble clic en el nodo de Telegram.
3. En `Credential to connect with`, selecciona **Create New Credential** y pega tu Token.
4. Para obtener tu `Chat ID` personal, háblale al bot `@userinfobot` en Telegram. Coloca ese ID numérico en el nodo de n8n y guarda.

### 5. Enlazar el Backend con n8n (Webhook)
Cuando el motor de triaje de FastAPI detecta un caso crítico, avisa a n8n mediante un webhook.
1. En el flujo **Alertas Criticas** de n8n, haz doble clic en el nodo **Webhook** y copia la **Test URL** o **Production URL**.
2. Debería ser algo como `http://n8n:5678/webhook/<ID>`. *(Se usa `n8n` como host porque ocurre dentro de la red interna de Docker).*
3. Pega esa URL en tu archivo `.env`:
   ```env
   URL_WEBHOOK_N8N=http://n8n:5678/webhook/<ID-DEL-WEBHOOK>
   ```
4. Reinicia el backend para aplicar el cambio:
   ```bash
   docker compose restart backend
   ```

---

## 🖥️ Uso del Sistema (Demostración)

Con el sistema en marcha:
1.  **Dashboard:** Ingresa a [http://localhost:5173](http://localhost:5173) para ver el tablero de control principal, donde las órdenes irán apareciendo coloreadas por su nivel de triaje.
2.  **Alertas:** Mantén abierto tu Telegram; las órdenes marcadas como críticas te notificarán en menos de 5 segundos con el código del paciente seudonimizado.
3.  **DICOM/PACS:** El servidor Orthanc estará escuchando conexiones de modalidades en el puerto `4242` y exponiendo su interfaz web en [http://localhost:8042](http://localhost:8042).

---

## 👥 Autores

*   Nahuel Aciar
*   Rodrigo Ramírez
*   Leandro Mercado

