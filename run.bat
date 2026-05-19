@echo off
:: Change to your Flask app folder
cd /d "C:\path\to\your\flask-app"

:: Activate virtual environment if you have one
:: call venv\Scripts\activate

:: Run Flask app in a separate window
start cmd /k "python app.py"

:: Wait a few seconds for Flask to start
timeout /t 5

:: Run ngrok to expose port 5000 and save the URL to a file
start cmd /k "ngrok http 5000 --log=stdout > ngrok.log"

:: Wait a few seconds for ngrok to start and get URL
timeout /t 5

:: Extract ngrok URL from log and open it in default browser
for /f "tokens=2 delims=: " %%a in ('findstr /R "https://[0-9a-z]*\.ngrok\.io" ngrok.log') do (
    start "" %%a
)

pause
