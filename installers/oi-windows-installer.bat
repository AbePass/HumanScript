@echo off

echo Starting Open Interpreter installation...

echo This will take approximately 5 minutes...

REM Check if Python is installed
echo Checking if Python is installed...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed. Please install Python and try again.
    exit /b 1
)
echo Python is installed.

REM Check if venv is installed
echo Checking if Python venv is installed...
python -m venv --help >nul 2>&1
if %errorlevel% neq 0 (
    echo Python venv is not installed. Installing venv...
    python -m pip install --user virtualenv
)
echo Python venv is installed.

REM Set up a virtual environment
echo Setting up a virtual environment...
python -m venv opai
echo Virtual environment setup complete.

REM Activate the virtual environment
echo Activating the virtual environment...
call opai\Scripts\activate.bat
echo Virtual environment activated.

REM Install the necessary packages
echo Installing necessary packages...
pip install open-interpreter tk pillow pyttsx3 speechrecognition pyautogui keyboard langchain_community langchain_openai chromadb shortuuid
pip install openai pydub pygame
echo Necessary packages installed.

REM Install pyaudio
echo Installing pyaudio...
pip install pyaudio
echo pyaudio installed.

echo.
echo Open Interpreter has been installed. Run the following command to use it:
echo.
echo opai\Scripts\activate.bat && python chat.py
