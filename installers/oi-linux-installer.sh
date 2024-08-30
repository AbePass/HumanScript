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
pip install open-interpreter tk pillow speechrecognition pyautogui keyboard langchain_community langchain_openai chromadb openai pygame python-dotenv unstructured unstructured[md] unstructured[pdf] customtkinter

# Install system dependencies
sudo apt-get update
sudo apt-get install -y portaudio19-dev ffmpeg libsdl2-mixer-2.0-0 flac

# Install pyaudio
pip install pyaudio

echo ""
echo "Open Interpreter has been installed. Run the following command to use it: "
echo ""
