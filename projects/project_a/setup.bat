@echo off
chcp 65001 >nul
echo ========================================
echo   Sticker Maker v3.3 - Установка
echo ========================================
echo.

REM Переход в папку скрипта
cd /d "%~dp0"

REM Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден!
    echo Установите Python 3.8+ с сайта python.org
    echo Не забудьте отметить "Add Python to PATH"
    pause
    exit /b 1
)

echo ✓ Python найден
python --version

REM Создание виртуального окружения
echo.
echo Создание виртуального окружения...
if exist venv (
    echo Виртуальное окружение уже существует
) else (
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Не удалось создать виртуальное окружение
        echo Установите модуль venv: python -m pip install virtualenv
        pause
        exit /b 1
    )
    echo ✓ Виртуальное окружение создано
)

REM Создание requirements.txt если его нет
if not exist requirements.txt (
    echo # Основные зависимости> requirements.txt
    echo pillow^>^=10.0.0>> requirements.txt
    echo pandas^>^=2.0.0>> requirements.txt
    echo openpyxl^>^=3.1.0>> requirements.txt
    echo xlrd^>^=2.0.0>> requirements.txt
    echo qrcode^>^=7.4.2>> requirements.txt
    echo python-barcode^>^=0.14.0>> requirements.txt
    echo requests^>^=2.31.0>> requirements.txt
    echo.>> requirements.txt
    echo # Для сборки в exe>> requirements.txt
    echo pyinstaller^>^=5.0.0>> requirements.txt
)

REM Активация и установка зависимостей
echo.
echo Активация окружения и установка зависимостей...
call venv\Scripts\activate.bat

REM Обновление pip без ошибок
python -m pip install --upgrade pip --quiet

REM Установка зависимостей
python -m pip install -r requirements.txt

if errorlevel 1 (
    echo ❌ Ошибка установки зависимостей
    echo Проверьте подключение к интернету
    pause
    exit /b 1
)

echo ✓ Зависимости установлены

REM Создание ярлыков запуска
echo.
echo Создание ярлыков запуска...

echo @echo off > run_gui.bat
echo chcp 65001 ^>nul >> run_gui.bat
echo cd /d "%%~dp0" >> run_gui.bat
echo call venv\Scripts\activate.bat >> run_gui.bat
echo python main.py >> run_gui.bat
echo pause >> run_gui.bat

echo @echo off > run_cli.bat
echo chcp 65001 ^>nul >> run_cli.bat
echo cd /d "%%~dp0" >> run_cli.bat
echo call venv\Scripts\activate.bat >> run_cli.bat
echo python main.py cli >> run_cli.bat
echo pause >> run_cli.bat

REM Создание иконки если ее нет
if not exist icon.ico (
    echo placeholder > icon.ico
)

echo.
echo ========================================
echo   Установка завершена успешно!
echo ========================================
echo.
echo Доступные команды:
echo   run_gui.bat  - Запуск графического интерфейса
echo   run_cli.bat  - Запуск в командном режиме
echo.
echo Для разработки активируйте окружение:
echo   venv\Scripts\activate.bat
echo.
echo Папка настроек:
echo   %%APPDATA%%\StickerMakerV3
echo.
pause