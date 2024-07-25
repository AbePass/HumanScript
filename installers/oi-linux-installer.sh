#!/bin/bash

echo "Starting Open Interpreter installation..."
sleep 2
echo "This will take approximately 5 minutes..."
sleep 2

# Set up a virtual environment
python3 -m venv opai

# Activate the virtual environment
source opai/bin/activate

# Install the necessary packages
pip install open-interpreter
pip install tk pillow pyttsx3 speechrecognition pyautogui keyboard langchain_community langchain_openai chromadb


# Install portaudio
sudo apt-get install portaudio19-dev

# Install pyaudio
pip install pyaudio

echo ""
echo "Open Interpreter has been installed. Run the following command to use it: "
echo ""
echo "source opai/bin/activate && python chat.py"
