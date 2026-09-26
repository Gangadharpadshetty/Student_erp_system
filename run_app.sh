#!/bin/bash
echo "Starting Student ERP System..."

# 1. Create Virtual Environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# 2. Activate Virtual Environment
source venv/bin/activate

# 3. Install Dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# 4. Initialize Database on Render
echo "Initializing Render PostgreSQL Database..."
python3 seed_db.py

# 5. Start the Server
echo -e "\n🚀 Server is starting!"
echo "Please open your browser and go to: http://127.0.0.1:8000"
echo -e "\n"
uvicorn app.main:app --reload
