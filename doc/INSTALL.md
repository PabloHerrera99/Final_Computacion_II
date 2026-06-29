# Instalación y despliegue
 
Guía para clonar, instalar y levantar **Cuatro en Línea**.
 
## Requisitos
 
- **Python 3.10+** (el servidor usa `asyncio`, f-strings y tipado moderno).
- **pip** para instalar las dependencias.
- Las dependencias del proyecto son mínimas (ver `requirements.txt`):
  - `Flask==3.0.0` — API REST.
  - `requests==2.31.0` — cliente HTTP del proceso puente.

## 1. Clonar el repositorio
 
```bash
git clone https://github.com/PabloHerrera99/Final_Computacion_II.git
cd Final_Computacion_II
```

Todos los comandos de esta guía asumen que estás parado en la raíz del proyecto (la carpeta `Final_Computacion_II`).
 
## 2. Crear el entorno virtual e instalar dependencias
 
**Linux / macOS:**
 
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
 
**Windows (PowerShell):**
 
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
 
> El repositorio puede traer una carpeta `venv/` ya commiteada. Conviene **recrearla** con los pasos de arriba, porque un entorno virtual generado en otra máquina o sistema operativo no suele funcionar.
 
## 3. Lanzar el sistema
 
El sistema son **dos programas independientes** que se levantan por separado, cada uno en su terminal (con el entorno virtual activado y parados en la raíz). **El orden importa:** primero la API, después el servidor de juego.
 
**Terminal 1 — API REST (inicializa la base de datos y escucha en el puerto 5000):**
 
```bash
python3 app/api/app.py
```
 
Al arrancar crea/inicializa la base SQLite (`app/api/cuatro_en_linea.db`) a partir de `app/api/database/schema.sql` y deja la API escuchando en `http://0.0.0.0:5000`.
 
**Terminal 2 — Servidor de juego (lanza el Proceso 1 y el Proceso 2, escucha en el puerto 8888):**
 
```bash
python3 app/server/main.py
```
 
 
## 4. Conectar un cliente (smoke test)
 
Con la API y el servidor corriendo, en otra terminal:
 
```bash
python3 app/client/client.py -u test -p 1234 -a ranking -i 127.0.0.1
```