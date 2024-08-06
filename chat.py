import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox
from interpreter import interpreter
import os
import speech_recognition as sr
from openai import OpenAI
import threading
from query_vector_database import query_vector_database
import tempfile
import re
import pygame
import time
from tkinter import ttk 

use_knowledge = True

def configure_interpreter():
    interpreter.custom_instructions = '''
    You have full permission to run Python code and shell commands on the user's computer. 
    Use Desktop as the working directory. Save all files in Desktop unless otherwise specified.
    If the query involves running a command or code, execute it and provide the output. 
    If additional context is provided, use it to inform your decision-making.
    You will recieve prompts in the format "Context: {context}\n\nQuery: {query}"
    Only respond with the answer to the query. Use the context to help you answer the query.
    If you need to refer to previous messages, use the conversation_history folder
    '''

    providers = ["azure", "openai", "anthropic"]
    
    # Create a new top-level window for provider selection
    provider_window = tk.Toplevel(root)
    provider_window.title("Select Provider")
    provider_window.geometry("300x100")
    
    provider_var = tk.StringVar()
    provider_dropdown = ttk.Combobox(provider_window, textvariable=provider_var, values=providers, state="readonly")
    provider_dropdown.set("Select provider")
    provider_dropdown.pack(pady=10)
    
    def on_provider_select():
        provider = provider_var.get()
        provider_window.destroy()
        configure_provider(provider)
    
    select_button = tk.Button(provider_window, text="Select", command=on_provider_select)
    select_button.pack(pady=10)
    
    provider_window.transient(root)
    provider_window.grab_set()
    root.wait_window(provider_window)

def configure_provider(provider):
    os.environ["OPENAI_API_KEY"] = simpledialog.askstring("Input", "Enter OpenAI API Key: (needed for lanchain rag)")

    interpreter.llm.supports_vision = True
    interpreter.llm.supports_functions = True
    interpreter.auto_run = True
    interpreter.llm.temperature = 0.3
    interpreter.llm.max_tokens = 4096

    if provider.lower() == "azure":
        os.environ["AZURE_API_KEY"] = simpledialog.askstring("Input", "Enter Azure API Key:")
        os.environ["AZURE_API_BASE"] = simpledialog.askstring("Input", "Enter Azure API Base:")
        os.environ["AZURE_API_VERSION"] = simpledialog.askstring("Input", "Enter Azure API Version:")
        model = simpledialog.askstring("Input", "Enter Azure Model:")
        interpreter.llm.provider = "azure"  # Set the provider
        interpreter.llm.api_key = os.environ["AZURE_API_KEY"]
        interpreter.llm.api_base = os.environ["AZURE_API_BASE"]
        interpreter.llm.api_version = os.environ["AZURE_API_VERSION"]
        interpreter.llm.model = f"azure/{model}"  # Ensure the model is prefixed with 'azure/'
    elif provider.lower() == "openai":
        model = simpledialog.askstring("Input", "Enter OpenAI Model:")
        interpreter.llm.api_key = os.environ["OPENAI_API_KEY"]
        interpreter.llm.model = model
    elif provider.lower() == "anthropic":
        os.environ["ANTHROPIC_API_KEY"] = simpledialog.askstring("Input", "Enter Anthropic API Key:")
        model = simpledialog.askstring("Input", "Enter Anthropic Model:")
        interpreter.llm.api_key = os.environ["ANTHROPIC_API_KEY"]
        interpreter.llm.model = model

def send_message(event=None):
    user_input = input_box.get("1.0", tk.END).strip()
    if user_input:
        chat_window.config(state=tk.NORMAL)
        chat_window.insert(tk.END, "You: " + user_input + "\n")
        chat_window.config(state=tk.DISABLED)
        input_box.delete("1.0", tk.END)
        # Query the skills database
        if use_knowledge:
            context_text, sources = query_vector_database(user_input)
        else:
            context_text = None
        
        try:
            response = get_interpreter_response(context_text, user_input)
        except Exception as e:
            response = f"There was an error processing your request: {e}"
            print(f"Error: {e}")  # Print the exception details
        
        chat_window.config(state=tk.NORMAL)
        chat_window.insert(tk.END, "Bot: " + response + "\n")
        if use_knowledge:
            if sources:
                chat_window.insert(tk.END, "Sources:\n" + "\n".join(sources) + "\n")
        chat_window.config(state=tk.DISABLED)
        chat_window.yview(tk.END)
        
        if tts_var.get():
            text_to_speech(response)

def sanitize_filename(filename):
    """Sanitize the filename to remove invalid characters."""
    return re.sub(r'[<>:"/\\|?*\n]', '_', filename)

def get_interpreter_response(context, query):
    # If context is None or empty, just use the query
    if not context:
        prompt = query
    else:
        # Combine context and query in a more clear way
        prompt = f"Context: {context}\n\nQuery: {query}"
    
    sanitized_prompt = sanitize_filename(prompt)
    messages = interpreter.chat(sanitized_prompt, display=False, stream=False)
    response = messages[-1]['content'] if messages else "No response"
    return response

def reset_chat():
    # reset the interpreter
    interpreter.reset()

    #reset the chat window
    
    chat_window.config(state=tk.NORMAL)
    chat_window.delete("1.0", tk.END)
    chat_window.config(state=tk.DISABLED)

def interrupt(event=None):

    
    # Stop the text-to-speech playback if pygame mixer is initialized
    if pygame.mixer.get_init():
        pygame.mixer.music.stop()
    
    chat_window.config(state=tk.NORMAL)
    chat_window.config(state=tk.DISABLED)
    chat_window.yview(tk.END)

def recognize_speech():
        # Stop the text-to-speech playback if pygame mixer is initialized
    if pygame.mixer.get_init():
        pygame.mixer.music.stop()
        
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        chat_window.config(state=tk.NORMAL)
        chat_window.insert(tk.END, "System: Listening...\n")
        chat_window.config(state=tk.DISABLED)
        chat_window.yview(tk.END)
        audio = recognizer.listen(source)
    
    try:
        # Save the audio to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            temp_audio.write(audio.get_wav_data())
            temp_audio_path = temp_audio.name
        
        # Transcribe using Whisper
        with open(temp_audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
            )
        
        user_input = transcript.text
        input_box.insert(tk.END, user_input)
        send_message()
    except Exception as e:
        chat_window.config(state=tk.NORMAL)
        chat_window.insert(tk.END, f"System: Error in speech recognition: {str(e)}\n")
        chat_window.config(state=tk.DISABLED)
        chat_window.yview(tk.END)
    finally:
        # Clean up the temporary file
        if 'temp_audio_path' in locals():
            os.unlink(temp_audio_path)

def start_recognition_thread():
    threading.Thread(target=recognize_speech).start()

def text_to_speech(text):
    pygame.mixer.init()
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text
    )
    
    # Save the audio content to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
        temp_audio.write(response.content)
        temp_audio_path = temp_audio.name
    
    # Play the audio file
    pygame.mixer.music.load(temp_audio_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    
    # Wait a bit before trying to delete the file
    pygame.mixer.music.unload()
    time.sleep(0.1)
    
    # Try to remove the temporary file, but don't raise an error if it fails
    try:
        os.unlink(temp_audio_path)
    except PermissionError:
        print(f"Could not delete temporary file: {temp_audio_path}")

def open_settings():
    settings_window = tk.Toplevel(root)
    settings_window.title("Settings")
    settings_window.geometry("400x300")

    ttk.Label(settings_window, text="Use Knowledge Base:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
    use_knowledge_var = tk.BooleanVar(value=use_knowledge)
    ttk.Checkbutton(settings_window, variable=use_knowledge_var).grid(row=0, column=1, padx=10, pady=5)

    ttk.Label(settings_window, text="Supports Vision:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
    supports_vision_var = tk.BooleanVar(value=interpreter.llm.supports_vision)
    ttk.Checkbutton(settings_window, variable=supports_vision_var).grid(row=1, column=1, padx=10, pady=5)

    ttk.Label(settings_window, text="Supports Functions:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
    supports_functions_var = tk.BooleanVar(value=interpreter.llm.supports_functions)
    ttk.Checkbutton(settings_window, variable=supports_functions_var).grid(row=2, column=1, padx=10, pady=5)

    ttk.Label(settings_window, text="Auto Run:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
    auto_run_var = tk.BooleanVar(value=interpreter.auto_run)
    ttk.Checkbutton(settings_window, variable=auto_run_var).grid(row=3, column=1, padx=10, pady=5)

    ttk.Label(settings_window, text="Temperature:").grid(row=4, column=0, padx=10, pady=5, sticky="w")
    temperature_var = tk.DoubleVar(value=interpreter.llm.temperature)
    ttk.Entry(settings_window, textvariable=temperature_var).grid(row=4, column=1, padx=10, pady=5)

    ttk.Label(settings_window, text="Max Tokens:").grid(row=5, column=0, padx=10, pady=5, sticky="w")
    max_tokens_var = tk.IntVar(value=interpreter.llm.max_tokens)
    ttk.Entry(settings_window, textvariable=max_tokens_var).grid(row=5, column=1, padx=10, pady=5)

    def save_settings():
        global use_knowledge
        use_knowledge = use_knowledge_var.get()
        interpreter.llm.supports_vision = supports_vision_var.get()
        interpreter.llm.supports_functions = supports_functions_var.get()
        interpreter.auto_run = auto_run_var.get()
        interpreter.llm.temperature = temperature_var.get()
        interpreter.llm.max_tokens = max_tokens_var.get()
        settings_window.destroy()

    ttk.Button(settings_window, text="Save", command=save_settings).grid(row=6, column=0, columnspan=2, pady=20)

# Set up the main application window
root = tk.Tk()
root.title("Chat UI")

# Configure the interpreter
configure_interpreter()

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

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

# Create a frame for buttons
button_frame = tk.Frame(root)
button_frame.pack(padx=10, pady=10, fill=tk.X)

# Create a send button
send_button = tk.Button(button_frame, text="Send", command=send_message)
send_button.pack(side=tk.LEFT, padx=5)

# Create a speech-to-text button
speech_button = tk.Button(button_frame, text="Speak", command=start_recognition_thread)
speech_button.pack(side=tk.LEFT, padx=5)

# Create a settings button
settings_button = tk.Button(button_frame, text="Settings", command=open_settings)
settings_button.pack(side=tk.LEFT, padx=5)

# Create a reset button
reset_button = tk.Button(button_frame, text="Reset", command=reset_chat)
reset_button.pack(side=tk.LEFT, padx=5)

# Create an interrupt button
interrupt_button = tk.Button(button_frame, text="Interrupt", command=interrupt)
interrupt_button.pack(side=tk.LEFT, padx=5)

# Create a checkbox to toggle text-to-speech
tts_var = tk.BooleanVar()
tts_checkbox = tk.Checkbutton(root, text="Enable Text-to-Speech", variable=tts_var)
tts_checkbox.pack(padx=10, pady=10)

# Run the application
root.mainloop()