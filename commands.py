import base64
import pyautogui
from PIL import Image
import io
import re
from interpreter.terminal_interface.utils.find_image_path import find_image_path

def execute_command(query):
    commands = [
        #if you say what's on my screen, show my screen, capture my screen, or screenshot, it will take a screenshot
        (r'\b(?:what(?:\'s|\s+is)?|show)\s+(?:on|in)\s+my\s+screen\b', take_screenshot_command), 
        # if you say a phrase that includes a file path, it will detect the file path
        (r'\b(?:[a-zA-Z]:\\|/)?(?:[\w-]+\\|/)*[\w-]+\.\w+\b', detect_filepath_command),
    ]
    
    # Normalize the query: convert to lowercase
    normalized_query = query.lower()
    
    for pattern, func in commands:
        if re.search(pattern, normalized_query, re.IGNORECASE):
            return func(query)

    return None

def take_screenshot_command(query):
    screenshot = pyautogui.screenshot()
    buffered = io.BytesIO()
    screenshot.save(buffered, format="PNG")
    encoded_screenshot = base64.b64encode(buffered.getvalue()).decode('utf-8')
    return {
        "role": "user",
        "type": "image",
        "format": "base64",
        "content": encoded_screenshot,
    }

def detect_filepath_command(query):
    # Extract the file path from the query
    file_path_match = re.search(r'\b(?:[a-zA-Z]:\\|/)?(?:[\w-]+\\|/)*[\w-]+\.\w+\b', query)
    if file_path_match:
        file_path = file_path_match.group(0)
        if find_image_path(file_path):
            # If the file is an image, return the message in the specified format
            message = {
                "role": "user",
                "type": "image",
                "format": "path",
                "content": file_path,
            }
            return message
        else:
            return f"The file at {file_path} is not an image."
    return "No valid file path found in the query."

# Add more command functions as needed