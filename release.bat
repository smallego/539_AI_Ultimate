@echo off
setlocal enabledelayedexpansion

set "PY_CMD="

where py >nul 2>nul
if %ERRORLEVEL%==0 set "PY_CMD=py"

if not defined PY_CMD (
    where python >nul 2>nul
    if %ERRORLEVEL%==0 set "PY_CMD=python"
)

if not defined PY_CMD (
    where python3 >nul 2>nul
    if %ERRORLEVEL%==0 set "PY_CMD=python3"
)

if not defined PY_CMD (
    echo No Python executable found.
    exit /b 1
)

if "%1"=="" goto help
if "%1"=="compile" goto compile
if "%1"=="pytest" goto pytest
if "%1"=="test" goto pytest
if "%1"=="build" goto build
if "%1"=="run" goto run
if "%1"=="all" goto all
goto help

:compile
%PY_CMD% -m compileall core web tests
exit /b %ERRORLEVEL%

:pytest
%PY_CMD% -m pytest tests
exit /b %ERRORLEVEL%

:build
docker build -t 539-ai-ultimate:rc .
exit /b %ERRORLEVEL%

:run
%PY_CMD% -m uvicorn web.app:app --host 127.0.0.1 --port 8000
exit /b %ERRORLEVEL%

:all
%PY_CMD% -m compileall core web tests
if not %ERRORLEVEL%==0 exit /b %ERRORLEVEL%
%PY_CMD% -m pytest tests
if not %ERRORLEVEL%==0 exit /b %ERRORLEVEL%
docker build -t 539-ai-ultimate:rc .
exit /b %ERRORLEVEL%

:help
echo Usage:
echo   release.bat compile
echo   release.bat pytest
echo   release.bat build
echo   release.bat run
echo   release.bat all
exit /b 0
