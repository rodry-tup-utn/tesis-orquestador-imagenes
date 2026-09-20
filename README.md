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
*   **FastAPI + PostgreSQL (Motor de Triaje):** API REST asíncrona que valida datos con Pydantic, aplica reglas configurables de triaje (Niveles: Crítico, Urgente, Prioritario y Rutina) y persiste el estado. Los niveles de prioridad utilizados por el artefacto son Crítico, Urgente, Prioritario y Rutina.
*   **Orthanc (VNA/PACS):** Servidor DICOM que expone el servicio de *Modality Worklist* (MWL) para que los resonadores/tomógrafos consuman la lista de pacientes.
*   **React + Vite (Tablero SPA):** Frontend (Feature-Sliced Design) con Vite. En el entorno de validación se ejecuta mediante el servidor de desarrollo de Vite; un despliegue productivo debe servir el artefacto estático detrás de un proxy inverso (por ejemplo, Nginx). Las actualizaciones se realizan en tiempo real mediante WebSockets.
*   **Telegram Bot API:** Subsistema asíncrono para notificaciones proactivas al equipo médico con datos de pacientes seudonimizados mediante HMAC-SHA256.
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

### 2. Variables obligatorias de seguridad
El MVP exige secretos separados: `SECRET_KEY` para JWT, `PSEUDONYM_SECRET` para HMAC-SHA256, `INTERNAL_API_KEY` para autenticar la ingesta máquina-a-máquina desde n8n y `ALERT_WEBHOOK_KEY` para autenticar el backend frente al webhook interno de alertas. Configure también `AUTH_USERNAME` y `AUTH_PASSWORD` para el usuario del tablero. Ninguno debe quedar versionado.

### 3. Levantar la Infraestructura
Abre tu terminal en la carpeta raíz del proyecto y ejecuta:

```bash
docker compose up -d --build
```
> Esto construirá la imagen de desarrollo del Frontend (Vite), el Backend (FastAPI), y descargará las imágenes de Postgres, n8n, Mock Server y Orthanc. Las migraciones de la base de datos se aplicarán automáticamente.
>
> El Frontend corre en modo desarrollo con **Hot Module Replacement (HMR)**: los cambios en `frontend/src` se ven al instante sin rebuild. Ingresa a [http://localhost:5173](http://localhost:5173).

### 4. Configurar el Orquestador (n8n)
La primera vez que n8n inicie, estará "en blanco".
1. Ingresa a [http://localhost:5678](http://localhost:5678) y crea una cuenta de administrador local.
2. Ve a **Workflows** > **Add Workflow**.
3. En el menú superior derecho (`...`), selecciona **Import from File**.
4. Importa el archivo `n8n-workflow/Orquestador Imagenes.json`, guárdalo y **actívalo** (Toggle "Active").
5. Repite el paso para el archivo `n8n-workflow/Alertas Criticas.json`.

### 5. Configurar el Bot de Alertas (Telegram)
Para recibir alertas sobre pacientes en estado "Crítico":
1. En Telegram, busca a `@BotFather`, envía `/newbot` y sigue los pasos para obtener un **Token de Acceso**.
2. En n8n, abre el flujo **Alertas Criticas** y haz doble clic en el nodo de Telegram.
3. En `Credential to connect with`, selecciona **Create New Credential** y pega tu Token.
4. Para obtener tu `Chat ID` personal, háblale al bot `@userinfobot` en Telegram y coloca ese valor en `TELEGRAM_CHAT_ID` dentro de `.env`. El workflow de n8n toma el destino desde esa variable y no contiene un identificador de canal hardcodeado. **Nota de privacidad:** El sistema está diseñado para enviar únicamente el pseudónimo criptográfico (HMAC-SHA256) del paciente, de modo que el nombre real no se incluya en el payload enviado al canal externo.

### 6. Enlazar el Backend con n8n (Webhook)
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
1.  **Autenticación y Dashboard:** Ingresa a [http://localhost:5173](http://localhost:5173), inicia sesión con `AUTH_USERNAME`/`AUTH_PASSWORD` y luego accede al tablero de control principal. Las órdenes irán apareciendo coloreadas por su nivel de triaje.
2.  **Alertas:** Mantén abierto tu Telegram; las órdenes marcadas como críticas te notificarán dentro del umbral experimental de 10 segundos con el código del paciente seudonimizado.
3.  **DICOM/PACS:** El servidor Orthanc estará escuchando conexiones de modalidades en el puerto `4242` y exponiendo su interfaz web en [http://localhost:8042](http://localhost:8042).

---

## 👥 Autores

*   Nahuel Aciar
*   Rodrigo Ramírez
*   Leandro Mercado


---

## Materiales experimentales complementarios

El ZIP de software contiene la implementación, las pruebas automatizadas y la regresión de consistencia del motor. Los archivos completos del experimento humano del Capítulo 6 (por ejemplo, órdenes de evaluación y planillas individuales de los evaluadores) se conservan como material académico complementario separado y no se incluyen en este paquete de software. La ausencia de esos archivos en el ZIP no debe interpretarse como ausencia de la evaluación descrita en la tesis.
