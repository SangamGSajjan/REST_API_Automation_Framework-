@echo off
REM ============================================================================
REM REST API Automation Test Runner (Python + Requests + Pytest)
REM Designed for fast execution of API Smoke, Regression, Negative & DB validation suites.
REM ============================================================================

:menu
cls
echo ============================================================================
echo      REST API AUTOMATION TEST RUNNER (Python + Requests + Pytest)
echo ============================================================================
echo.
echo Select test suite to execute:
echo   [1] Run All API Tests (Full Suite + HTML Report)
echo   [2] Run Smoke / Sanity Tests (-m smoke)
echo   [3] Run CRUD Lifecycle Tests (-m crud)
echo   [4] Run Negative & Boundary Tests (-m negative)
echo   [5] Run Backend Database Validation Tests (-m db)
echo   [6] Run Query Parameter & Filter Tests (-m filter)
echo   [7] Install Dependencies (pip install -r requirements.txt)
echo   [8] Open Latest HTML Report
echo   [9] Exit
echo.

set /p choice="Enter your choice (1-9): "

if "%choice%"=="1" (
    echo.
    echo Running All API Tests...
    pytest -v --html=reports/report.html --self-contained-html
    goto open_report
)
if "%choice%"=="2" (
    echo.
    echo Running Smoke Tests...
    pytest -v -m smoke --html=reports/smoke_report.html --self-contained-html
    set REPORT_NAME=smoke_report.html
    goto open_custom_report
)
if "%choice%"=="3" (
    echo.
    echo Running CRUD Tests...
    pytest -v -m crud --html=reports/crud_report.html --self-contained-html
    set REPORT_NAME=crud_report.html
    goto open_custom_report
)
if "%choice%"=="4" (
    echo.
    echo Running Negative & Boundary Tests...
    pytest -v -m negative --html=reports/negative_report.html --self-contained-html
    set REPORT_NAME=negative_report.html
    goto open_custom_report
)
if "%choice%"=="5" (
    echo.
    echo Running Backend Database Validation Tests...
    pytest -v -m db --html=reports/db_report.html --self-contained-html
    set REPORT_NAME=db_report.html
    goto open_custom_report
)
if "%choice%"=="6" (
    echo.
    echo Running Filter & Data-Driven Tests...
    pytest -v -m filter --html=reports/filter_report.html --self-contained-html
    set REPORT_NAME=filter_report.html
    goto open_custom_report
)
if "%choice%"=="7" (
    echo.
    echo Installing project dependencies...
    pip install -r requirements.txt
    echo.
    echo Dependencies installed successfully.
    pause
    goto menu
)
if "%choice%"=="8" (
    goto open_report
)
if "%choice%"=="9" (
    exit /b
)

echo Invalid choice. Please select 1-9.
pause
goto menu

:open_report
echo.
echo Test Execution Finished!
if exist reports\report.html (
    echo Opening HTML Report in default browser...
    start reports\report.html
) else (
    echo No report.html found in reports directory.
)
pause
goto menu

:open_custom_report
echo.
echo Test Execution Finished!
if exist reports\%REPORT_NAME% (
    echo Opening %REPORT_NAME% in default browser...
    start reports\%REPORT_NAME%
) else if exist reports\report.html (
    start reports\report.html
)
pause
goto menu
