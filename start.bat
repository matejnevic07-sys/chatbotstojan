@echo off
echo Installing dependencies...
python -m pip install -r requirements.txt -q

echo.
echo Starting Vendor Analytics Chatbot...
echo Open browser at: http://localhost:8000
echo.

cd backend
python -m uvicorn main:app --reload --port 8000
