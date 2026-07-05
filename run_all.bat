@echo off
chcp 65001 > nul
title 539 AI Ultimate v1.3

echo ======================================
echo 539 AI Ultimate Professional
echo ======================================

echo.
echo [1/5] 更新官方API...
python app\api_update.py

echo.
echo [2/5] 更新AI權重...
python core\engine.py

echo.
echo [3/5] 產生最佳組合...
python core\scorer.py

echo.
echo [4/5] 回測模型...
python core\backtest.py

echo.
echo [5/5] 更新Dashboard...
python dashboard\dashboard.py

echo.
echo ======================================
echo 全部完成！
echo ======================================

pause