@echo off
rem Usage: 
rem   run.bat highlights <slug> [--limit N]
rem   run.bat description <json_file>
rem   run.bat [args for main.py]

if exist venv\Scripts\activate.bat call venv\Scripts\activate.bat
if exist .venv\Scripts\activate.bat call .venv\Scripts\activate.bat

set CMD=%1

if "%CMD%"=="highlights" goto highlights
if "%CMD%"=="description" goto description
goto main

:highlights
shift
echo Running Highlights Update...
python "scripts\update_highlights.py" %1 %2 %3 %4 %5 %6 %7 %8 %9
goto end

:description
shift
echo Generating Book Description...
python "scripts\generate_description.py" %1 %2 %3 %4 %5 %6 %7 %8 %9
goto end

:main
echo Running Main Pipeline...
python main.py %*
goto end

:end
pause
