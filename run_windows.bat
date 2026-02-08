@echo off
echo Installing dependencies...
py -m pip install -r requirements.txt
echo Starting LoveTask Server...
echo Open http://localho st:8000 in your browser.
py -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
pause
