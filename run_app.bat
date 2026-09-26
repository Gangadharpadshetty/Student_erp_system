@echo off
echo Starting Student ERP System...

:: 1. Create Virtual Environment if it doesn't exist
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

:: 2. Activate Virtual Environment
call venv\Scripts\activate

:: 3. Install Dependencies
echo Installing dependencies...
pip install -r requirements.txt

:: 4. Initialize Database on Render
echo Initializing Render PostgreSQL Database...
python seed_db.py

:: 5. Start the Server
echo.
echo 🚀 Server is starting!
echo Please open your browser and go to: http://127.0.0.1:8000
echo.
uvicorn app.main:app --reload
pause
