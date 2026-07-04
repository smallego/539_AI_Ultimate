@echo off
chcp 65001 >nul
title 539 AI Ultimate Professional
color 0A

echo ==========================================
echo        539 AI Ultimate Professional
echo ==========================================

python -c "from core.logger import log; log('Run all started')"

call :RunStep "Database Backup" "python core\backup.py"
call :RunStep "Open official download page" "python app\downloader.py"
call :RunStep "Update history data" "python app\update.py"
call :RunStep "Analysis" "python app\analysis.py"
call :RunStep "Prediction" "python app\predict.py"
call :RunStep "Backtest" "python core\backtest.py"
call :RunStep "Dashboard" "python dashboard\dashboard.py"
python -c "from core.logger import log; log('Run all finished')"

echo.
echo ==========================================
echo ALL TASKS COMPLETED SUCCESSFULLY
echo ==========================================

pause
exit /b

:RunStep
echo.
echo [%~1]

python -c "from core.logger import log; log('%~1 started')"

cmd /c %~2

if errorlevel 1 (
    python -c "from core.logger import log; log('%~1 FAILED', 'ERROR')"

    echo.
    echo ==========================================
    echo ERROR:
    echo %~1 FAILED
    echo Program stopped.
    echo ==========================================

    pause
    exit /b 1
)

python -c "from core.logger import log; log('%~1 completed')"

exit /b