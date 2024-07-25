import base64
from PIL import Image
import io
import os
from interpreter import interpreter

def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return encoded_string

def create_image_message(encoded_image):
    message = [
        {"role": "user", "type": "message", "content": "Describe this image"},
        {
            "role": "user",
            "type": "image",
            "format": "base64.png",
            "content": encoded_image,
        },
    ]
    return message

def send_image_to_interpreter(image_path):
    encoded_image = encode_image_to_base64(image_path)
    message = create_image_message(encoded_image)
    
    interpreter.llm.supports_vision = True
    interpreter.llm.model = os.getenv('MODEL')
    
    response = interpreter.chat(message)
    return response
