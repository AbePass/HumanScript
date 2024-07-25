import tkinter as tk
from tkinter import scrolledtext, filedialog, simpledialog, messagebox
from interpreter import interpreter
import os
import speech_recognition as sr
import threading
import pyttsx3
import argparse
import keyboard
from image_interpreter import encode_image_to_base64, create_image_message
import pyautogui
from query_vector_database import query_vector_database
import config  # Import the new config module

# Argument parsing
parser = argparse.ArgumentParser(description="Open Interpreter Chat UI")
parser.add_argument('--os', type=str, help='Specify the operating system')
args = parser.parse_args()

# Initialize text-to-speech engine
tts_engine = pyttsx3.init()

selected_image_path = None

def configure_interpreter():
    provider = simpledialog.askstring("Input", "Select provider (azure/openai):")
    config.openai_key = simpledialog.askstring("Input", "Enter OpenAI API Key:")  # Update to use config
    
    if provider.lower() == "azure":
        api_key = simpledialog.askstring("Input", "Enter Azure API Key:")
        api_base = simpledialog.askstring("Input", "Enter Azure API Base:")
        api_version = simpledialog.askstring("Input", "Enter Azure API Version:")
        model = simpledialog.askstring("Input", "Enter Azure Model:")
        interpreter.llm.api_key = api_key
        interpreter.llm.api_base = api_base
        interpreter.llm.api_version = api_version
        interpreter.llm.model = model
        interpreter.llm.supports_vision = True
    elif provider.lower() == "openai":
        model = simpledialog.askstring("Input", "Enter OpenAI Model:")
        interpreter.llm.api_key = config.openai_key  # Update to use config
        interpreter.llm.model = model
        interpreter.llm.supports_vision = False
    else:
        messagebox.showerror("Error", "Invalid provider selected")
        root.quit()

# Set the operating system if provided
if args.os:
    interpreter.os = args.os

def is_relevant_context(context_text):
    """Check if the context is relevant by ensuring it contains meaningful content."""
    return context_text and len(context_text.strip()) > 0

def sanitize_context(context_text):
    """Sanitize context to ensure it is safe to use."""
    sanitized_text = context_text.replace("\n", " ").replace("\r", " ").strip()
    return sanitized_text[:500]  # Limit context text length for testing

def send_message(event=None):
    user_input = input_box.get("1.0", tk.END).strip()
    if user_input:
        chat_window.config(state=tk.NORMAL)
        chat_window.insert(tk.END, "You: " + user_input + "\n")
        chat_window.config(state=tk.DISABLED)
        input_box.delete("1.0", tk.END)
        
        if selected_image_path:
            encoded_image = encode_image_to_base64(selected_image_path)
            message = create_image_message(encoded_image)
            message[0]['content'] = user_input
        else:
            message = user_input
        
        # Query the skills database
        query_text = user_input
        context_text, sources = query_vector_database(query_text)
        
        # Determine the response based on the relevance of the context
        if is_relevant_context(context_text):
            sanitized_context = sanitize_context(context_text)
            try:
                response = get_interpreter_response(sanitized_context)
            except Exception as e:
                response = "There was an error processing your request. Please try again."
        else:
            try:
                response = get_interpreter_response(query_text)
            except Exception as e:
                response = "There was an error processing your request. Please try again."
        
        chat_window.config(state=tk.NORMAL)
        chat_window.insert(tk.END, "Bot: " + response + "\n")
        chat_window.config(state=tk.DISABLED)
        chat_window.yview(tk.END)
        
        if tts_var.get():
            tts_engine.say(response)
            tts_engine.runAndWait()

def get_interpreter_response(prompt):
    # Call the interpreter's chat method with the user's prompt
    messages = interpreter.chat(prompt, display=False, stream=False)
    # Extract the response from the messages
    response = messages[-1]['content'] if messages else "No response"
    return response

def interrupt(event=None):
    # Reset the interpreter to stop any ongoing processing
    interpreter.reset()
    chat_window.config(state=tk.NORMAL)
    chat_window.insert(tk.END, "System: The operation has been interrupted.\n")
    chat_window.config(state=tk.DISABLED)
    chat_window.yview(tk.END)

def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        chat_window.config(state=tk.NORMAL)
        chat_window.insert(tk.END, "System: Listening...\n")
        chat_window.config(state=tk.DISABLED)
        chat_window.yview(tk.END)
        audio = recognizer.listen(source)
    try:
        user_input = recognizer.recognize_google(audio)
        input_box.insert(tk.END, user_input)
        send_message()
    except sr.UnknownValueError:
        chat_window.config(state=tk.NORMAL)
        chat_window.insert(tk.END, "System: Could not understand audio\n")
        chat_window.config(state=tk.DISABLED)
        chat_window.yview(tk.END)
    except sr.RequestError as e:
        chat_window.config(state=tk.NORMAL)
        chat_window.insert(tk.END, f"System: Could not request results; {e}\n")
        chat_window.config(state=tk.DISABLED)
        chat_window.yview(tk.END)

def start_recognition_thread():
    threading.Thread(target=recognize_speech).start()

def select_image():
    global selected_image_path
    selected_image_path = filedialog.askopenfilename()
    if selected_image_path:
        chat_window.config(state=tk.NORMAL)
        chat_window.insert(tk.END, "System: Image selected\n")
        chat_window.config(state=tk.DISABLED)
        chat_window.yview(tk.END)

# Set up the main application window
root = tk.Tk()
root.title("Chat UI")

# Configure the interpreter
configure_interpreter()

# Bind Ctrl+C to the interrupt function
root.bind('<Control-c>', interrupt)
root.bind('<Return>', send_message)
root.bind('<Alt_L>', start_recognition_thread)

# Create a scrolled text widget for the chat window
chat_window = scrolledtext.ScrolledText(root, wrap=tk.WORD, state=tk.DISABLED)
chat_window.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

# Create a text widget for user input
input_box = tk.Text(root, height=3)
input_box.pack(padx=10, pady=10, fill=tk.X, expand=False)

# Create a send button
send_button = tk.Button(root, text="Send", command=send_message)
send_button.pack(padx=10, pady=10, side=tk.LEFT)

# Create a speech-to-text button
speech_button = tk.Button(root, text="Speak", command=start_recognition_thread)
speech_button.pack(padx=10, pady=10, side=tk.RIGHT)

# Create a button to select an image
image_button = tk.Button(root, text="Attach Image", command=select_image)
image_button.pack(padx=10, pady=10, side=tk.RIGHT)

# Create a checkbox to toggle text-to-speech
tts_var = tk.BooleanVar()
tts_checkbox = tk.Checkbutton(root, text="Enable Text-to-Speech", variable=tts_var)
tts_checkbox.pack(padx=10, pady=10)

# Run the application
root.mainloop()