@echo off
setlocal enabledelayedexpansion

rem upload.bat - Interactive tool to upload existing summaries to Sanity
rem Lists files in output/ directory and asks user to pick one.

if exist venv\Scripts\activate.bat call venv\Scripts\activate.bat
if exist .venv\Scripts\activate.bat call .venv\Scripts\activate.bat

echo ---------------------------------------------------
echo Select a Summary to Upload to Sanity
echo ---------------------------------------------------

set "output_dir=output"
if not exist "%output_dir%" (
    echo Error: "%output_dir%" directory not found.
    goto end
)

set count=0
for %%f in ("%output_dir%\*.json") do (
    set /a count+=1
    set "file[!count!]=%%f"
    echo [!count!] %%~nxf
)

if %count%==0 (
    echo No JSON files found in "%output_dir%".
    goto end
)

echo.
set /p "choice=Enter number to upload (1-%count%): "

if "%choice%"=="" goto end
if %choice% lss 1 goto end
if %choice% gtr %count% goto end

set "selected_file=!file[%choice%]!"
echo.
echo Selected: "%selected_file%"
echo Running upload script...
echo.

python "scripts\manual_upload.py" "%selected_file%"

:end
echo.
pause
endlocal
