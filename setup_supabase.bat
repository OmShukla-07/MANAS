@echo off
REM MANAS Supabase Setup Script
REM This script sets environment variables and runs Supabase operations

echo.
echo ==========================================
echo   MANAS Supabase Integration Setup
echo ==========================================
echo.

REM Set Supabase environment variables
set SUPABASE_URL=https://llkdmzdhnppvnlclcapv.supabase.co
set SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imxsa2RtemRobnBwdm5sY2xjYXB2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTg5OTk4MTIsImV4cCI6MjA3NDU3NTgxMn0.vbx8DmTi5M2Fi7o6YZimzY2nZEVoABiLIFHwe63k6tI=
set SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imxsa2RtemRobnBwdm5sY2xjYXB2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1ODk5OTgxMiwiZXhwIjoyMDc0NTc1ODEyfQ.HnX6EigrszqrWe1t30JaESzvnq5cU1O0wqLHTMZxB6g

echo Environment variables set!
echo.

REM Check what operation to perform
if "%1"=="check" (
    echo Testing Supabase connection...
    python manage.py setup_supabase --check-only
    goto :end
)

if "%1"=="setup" (
    echo Running full Supabase setup...
    python manage.py setup_supabase
    goto :end
)

if "%1"=="server" (
    echo Starting Django server...
    python manage.py runserver 8000
    goto :end
)

if "%1"=="status" (
    echo Testing Supabase API status...
    curl -s http://localhost:8000/api/v1/core/supabase/status/ || echo Please start the server first with: setup_supabase.bat server
    goto :end
)

REM Default: Show usage
echo Usage:
echo   setup_supabase.bat check     - Test Supabase connection
echo   setup_supabase.bat setup     - Run full setup
echo   setup_supabase.bat server    - Start Django server
echo   setup_supabase.bat status    - Test API status
echo.
echo Examples:
echo   setup_supabase.bat check
echo   setup_supabase.bat server
echo.

:end
pause