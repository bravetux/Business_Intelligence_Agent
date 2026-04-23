:: =============================================================================
:: Author : B.Vignesh Kumar aka Bravetux <ic19939@gmail.com>
:: Date   : 23 April 2026
:: =============================================================================
@echo off
setlocal enabledelayedexpansion
title P04 — Meeting ^& Document Intelligence Platform — Startup

cd /d "%~dp0"

echo ============================================================
echo   P04 — Meeting ^& Document Intelligence Platform
echo   Startup Check
echo ============================================================
echo.

:: ── 1. Check Python ──────────────────────────────────────────
echo [1/8] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo   [FAIL] Python not found. Please install Python 3.11+ and add it to PATH.
    echo          Download from: https://www.python.org/downloads/
    goto :error
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo   [OK]   Python %PY_VER% found.

:: ── 2. Check uv ──────────────────────────────────────────────
echo [2/8] Checking uv package manager...
uv --version >nul 2>&1
if errorlevel 1 (
    echo   [WARN] uv not found. Installing uv now...
    pip install uv >nul 2>&1
    if errorlevel 1 (
        echo   [FAIL] Could not install uv. Install manually:
        echo          pip install uv
        echo          OR: https://docs.astral.sh/uv/getting-started/installation/
        goto :error
    )
    echo   [OK]   uv installed.
) else (
    for /f "tokens=1,2" %%a in ('uv --version 2^>^&1') do set UV_VER=%%b
    echo   [OK]   uv !UV_VER! found.
)

:: ── 3. Check .env ────────────────────────────────────────────
echo [3/8] Checking .env configuration...
if not exist ".env" (
    echo   [WARN] .env file not found.
    if exist ".env.example" (
        echo          Copying .env.example to .env...
        copy ".env.example" ".env" >nul
        echo   [WARN] .env created from template.
        echo          Default provider is Ollama (zero cost).
        echo          Edit .env to add Bedrock/OpenAI/other API keys if needed.
        echo.
        set /p OPEN_ENV="   Open .env in Notepad now? [Y/N]: "
        if /i "!OPEN_ENV!"=="Y" (
            notepad .env
            echo   Waiting for you to save .env...
            pause
        )
    ) else (
        echo   [FAIL] Neither .env nor .env.example found. Cannot proceed.
        goto :error
    )
) else (
    echo   [OK]   .env found.
)

:: ── 4. Sync dependencies ─────────────────────────────────────
echo [4/8] Syncing Python dependencies with uv...
uv sync --quiet
if errorlevel 1 (
    echo   [FAIL] Dependency sync failed. Check pyproject.toml and internet connectivity.
    echo          Try manually: uv sync
    goto :error
)
echo   [OK]   All dependencies installed.

:: ── 5. Check Ollama + required models ────────────────────────
echo [5/8] Checking Ollama...
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo   [WARN] Ollama is not running or not reachable at http://localhost:11434
    echo          Start Ollama first:  https://ollama.com
    echo          Then pull models:
    echo            ollama pull llama3.3:70b
    echo            ollama pull nomic-embed-text
    echo.
    set /p CONTINUE="   Continue anyway (you can use a different provider)? [Y/N]: "
    if /i "!CONTINUE!" NEQ "Y" goto :error
    echo   [SKIP] Ollama check skipped — ensure your configured provider is reachable.
) else (
    echo   [OK]   Ollama is running.

    :: Check for llama3.3:70b
    curl -s http://localhost:11434/api/tags 2>nul | findstr /i "llama3.3" >nul 2>&1
    if errorlevel 1 (
        echo   [WARN] llama3.3:70b not found locally.
        echo          Run:  ollama pull llama3.3:70b
        echo          (or set DEFAULT_MODEL= in .env to another installed model)
    ) else (
        echo   [OK]   llama3.3:70b found.
    )

    :: Check for nomic-embed-text
    curl -s http://localhost:11434/api/tags 2>nul | findstr /i "nomic-embed-text" >nul 2>&1
    if errorlevel 1 (
        echo   [WARN] nomic-embed-text not found locally.
        echo          Run:  ollama pull nomic-embed-text
    ) else (
        echo   [OK]   nomic-embed-text found.
    )
)

:: ── 6. Check auth.yaml / init DB ─────────────────────────────
echo [6/8] Checking database and authentication...
if not exist "auth.yaml" (
    echo   [INFO] auth.yaml not found — initialising database and creating admin user...
    echo.
    set /p ADMIN_USER="   Admin username (default: admin): "
    if "!ADMIN_USER!"=="" set ADMIN_USER=admin
    set /p ADMIN_PASS="   Admin password (default: changeme): "
    if "!ADMIN_PASS!"=="" set ADMIN_PASS=changeme

    uv run python -m src.tools.init_db --admin-user !ADMIN_USER! --admin-pass !ADMIN_PASS!
    if errorlevel 1 (
        echo   [FAIL] Database initialisation failed.
        goto :error
    )
    echo.
    echo   [OK]   Database and auth.yaml created.
    echo   [WARN] Login credentials: !ADMIN_USER! / !ADMIN_PASS!
    echo          Change the password after first login via Settings.
) else (
    if not exist "data\jobs.db" (
        echo   [INFO] jobs.db missing — re-running schema init...
        uv run python -c "from src.tools.job_store import init_schema; init_schema()" >nul 2>&1
    )
    echo   [OK]   auth.yaml and database found.
)

:: ── 7. Free port 8503 ────────────────────────────────────────
echo [7/8] Checking port 8503...
set PORT_FREE=1
for /f "tokens=5" %%P in ('netstat -ano ^| findstr "LISTENING" ^| findstr ":8503 "') do (
    if not "%%P"=="0" (
        echo   [KILL] Port 8503 held by PID %%P — terminating.
        taskkill /PID %%P /F >nul 2>&1
        set PORT_FREE=0
    )
)
if !PORT_FREE! == 0 (
    timeout /t 2 /nobreak >nul
)
echo   [OK]   Port 8503 is free.

:: ── 8. Launch ────────────────────────────────────────────────
echo [8/8] Launching P04 Meeting ^& Document Intelligence Platform...
echo.
echo ============================================================
echo   App starting at: http://localhost:8503
echo   Press Ctrl+C in this window to stop the server.
echo ============================================================
echo.

:: Open browser after a short delay
start "" /b cmd /c "timeout /t 3 >nul && start http://localhost:8503"

:: Start Streamlit
uv run streamlit run app.py --server.port 8503 --server.headless false
goto :eof

:error
echo.
echo ============================================================
echo   Startup failed. Fix the issues above and re-run startup.bat
echo ============================================================
pause
exit /b 1
