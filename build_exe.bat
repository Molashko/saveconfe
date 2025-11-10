@echo off
echo Сборка SaveConfe в EXE...
echo.

REM Проверка установки PyInstaller
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo Установка PyInstaller...
    pip install pyinstaller
)

echo Сборка с правами администратора...
REM Используем --uac-admin для запроса прав администратора при запуске
pyinstaller --onefile --noconsole --name SaveConfe --uac-admin --icon=resources/icons/icon.ico main.py

if errorlevel 1 (
    echo Ошибка сборки!
    pause
    exit /b 1
)

echo.
echo Сборка завершена успешно!
echo EXE файл находится в папке dist\
echo.
echo ВАЖНО: EXE файл будет автоматически запрашивать права администратора при запуске.
pause

