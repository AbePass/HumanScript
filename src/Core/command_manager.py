import base64
import pyautogui
from PIL import Image
import io
import re
from interpreter.terminal_interface.utils.find_image_path import find_image_path

class CommandExecutor:
    def __init__(self):
        self.commands = [
            # if you say what's on my screen, show my screen, capture my screen, or screenshot, it will take a screenshot
            (r'\b(?:what(?:\'s|\s+is)?|show)[\s\.,!?]*(?:on|in)[\s\.,!?]*my[\s\.,!?]*screen\b', self.take_screenshot_command), 
            # if you say a phrase that includes a file path, it will detect the file path
            (r'\b(?:[a-zA-Z]:\\|/)?(?:[\w-]+\\|/)*[\w-]+\.\w+\b', self.detect_filepath_command),
        ]

    def execute_command(self, query):
        # Normalize the query: convert to lowercase
        normalized_query = query.lower()
        
        for pattern, func in self.commands:
            if re.search(pattern, normalized_query, re.IGNORECASE):
                print(f"Command matched: {pattern}")
                return func(query)

        return None

    def take_screenshot_command(self, query):
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

    def detect_filepath_command(self, query):
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
                return query

# Add more command functions as needed