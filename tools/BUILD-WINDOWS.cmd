@echo off
setlocal
set PYTHONUTF8=1
cd /d "%~dp0.."
echo VietSpell - build Windows x64 with the trained model
py -3.11 -c "import sys; assert sys.maxsize > 2**32" >nul 2>&1
if errorlevel 1 goto missing_python
if not exist "data\ngram.sqlite" goto missing_data
py -3.11 -m venv .venv-windows
if errorlevel 1 goto failed
.venv-windows\Scripts\python.exe -m pip install --require-hashes -r requirements-dev.lock
if errorlevel 1 goto failed
.venv-windows\Scripts\python.exe -m pip install --no-deps --no-build-isolation -e .
if errorlevel 1 goto failed
.venv-windows\Scripts\python.exe -m pytest -q -p no:cacheprovider
if errorlevel 1 goto failed
.venv-windows\Scripts\python.exe tools\package_windows.py
if errorlevel 1 goto failed
echo.
echo Build and automatic checks passed. Open dist\VietSpell\VietSpell.exe
echo Please review the Word exports in dist\VietSpell\samples with Microsoft Word.
explorer "dist"
pause
exit /b 0
:missing_python
echo Install Python 3.11 x64 from python.org including the Python launcher, then try again.
pause
exit /b 2
:missing_data
echo Missing trained data. Extract the whole source-trained ZIP, including data.
pause
exit /b 2
:failed
echo.
echo Build failed. Read the error above. No verified release ZIP was produced by this run.
pause
exit /b 1
