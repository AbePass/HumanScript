import tkinter as tk
from tkinter import scrolledtext, simpledialog, ttk, filedialog, messagebox
from interpreter import interpreter
import os
import speech_recognition as sr
from openai import OpenAI
import threading
from query_vector_database import query_vector_database
from build_vector_database import build_vector_database
import tempfile
import re
import pygame
import time
import numpy as np
from config import *  # Import all settings from config.py
import json
import shutil
import commands


# Replace the global variables with imports from config
use_knowledge = USE_KNOWLEDGE
selected_kbs = DEFAULT_SELECTED_KBS.copy()
wake_word = WAKE_WORD
is_listening = False
listen_thread = None
is_voice_mode = False

def configure_interpreter():
    interpreter.system_message = SYSTEM_MESSAGE
    interpreter.llm.supports_vision = INTERPRETER_SETTINGS["supports_vision"]
    interpreter.llm.supports_functions = INTERPRETER_SETTINGS["supports_functions"]
    interpreter.auto_run = INTERPRETER_SETTINGS["auto_run"]
    interpreter.loop = INTERPRETER_SETTINGS["loop"]
    interpreter.llm.temperature = INTERPRETER_SETTINGS["temperature"]
    interpreter.llm.max_tokens = INTERPRETER_SETTINGS["max_tokens"]
    interpreter.llm.context_window = INTERPRETER_SETTINGS["context_window"]
    interpreter.conversation_history_path = INTERPRETER_SETTINGS["conversation_history_path"]
    interpreter.computer.import_computer_api = INTERPRETER_SETTINGS["import_computer_api"]

    providers = ["azure", "openai", "anthropic"]
    
    # Create a new top-level window for provider selectio
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
    config_file = 'provider_config.json'
    
    # Load existing configuration if available
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
    else:
        config = {}

    # Function to get or prompt for a value
    def get_or_prompt(key, prompt):
        if key in config:
            return config[key]
        value = simpledialog.askstring("Input", prompt)
        config[key] = value
        return value

    # Common for all providers
    os.environ["OPENAI_API_KEY"] = get_or_prompt("OPENAI_API_KEY", "Enter OpenAI API Key: (needed for lanchain rag)")

    if provider.lower() == "azure":
        os.environ["AZURE_API_KEY"] = get_or_prompt("AZURE_API_KEY", "Enter Azure API Key:")
        os.environ["AZURE_API_BASE"] = get_or_prompt("AZURE_API_BASE", "Enter Azure API Base:")
        os.environ["AZURE_API_VERSION"] = get_or_prompt("AZURE_API_VERSION", "Enter Azure API Version:")
        model = get_or_prompt("AZURE_MODEL", "Enter Azure Model:")
        interpreter.llm.provider = "azure"
        interpreter.llm.api_key = os.environ["AZURE_API_KEY"]
        interpreter.llm.api_base = os.environ["AZURE_API_BASE"]
        interpreter.llm.api_version = os.environ["AZURE_API_VERSION"]
        interpreter.llm.model = f"azure/{model}"
    elif provider.lower() == "openai":
        model = get_or_prompt("OPENAI_MODEL", "Enter OpenAI Model:")
        interpreter.llm.api_key = os.environ["OPENAI_API_KEY"]
        interpreter.llm.model = model
    elif provider.lower() == "anthropic":
        os.environ["ANTHROPIC_API_KEY"] = get_or_prompt("ANTHROPIC_API_KEY", "Enter Anthropic API Key:")
        model = get_or_prompt("ANTHROPIC_MODEL", "Enter Anthropic Model:")
        interpreter.llm.api_key = os.environ["ANTHROPIC_API_KEY"]
        interpreter.llm.model = f"anthropic/{model}"

    # Save the configuration
    with open(config_file, 'w') as f:
        json.dump(config, f)

    # Set the provider in the configuration
    config['PROVIDER'] = provider.lower()

def generate_beep():
    pygame.mixer.init(frequency=44100, size=-16, channels=2)
    t = np.linspace(0, BEEP_DURATION, int(44100 * BEEP_DURATION), False)
    beep = np.sin(2 * np.pi * BEEP_FREQUENCY * t)
    beep = (beep * 32767).astype(np.int16)
    stereo_beep = np.column_stack((beep, beep))  # Create stereo audio
    return pygame.sndarray.make_sound(stereo_beep)

def send_message(event=None):
    user_input = input_box.get("1.0", tk.END).strip()
    if user_input:
        process_input(user_input)
        input_box.delete("1.0", tk.END)  # Clear the input box after sending

def recognize_speech(event=None):
    # Stop the text-to-speech playback if pygame mixer is initialized
    if pygame.mixer.get_init():
        pygame.mixer.music.stop()
    
    recognizer = sr.Recognizer()
    chat_window.config(state=tk.NORMAL)
    chat_window.insert(tk.END, "System: Listening for command...\n")
    chat_window.config(state=tk.DISABLED)
    chat_window.yview(tk.END)
    with sr.Microphone() as source:
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
        process_input(user_input)
        
    except Exception as e:
        chat_window.config(state=tk.NORMAL)
        chat_window.insert(tk.END, f"System: Error in speech recognition: {str(e)}\n")
        chat_window.config(state=tk.DISABLED)
        chat_window.yview(tk.END)
    finally:
        # Clean up the temporary file
        if 'temp_audio_path' in locals():
            os.unlink(temp_audio_path)

def process_input(user_input):
    chat_window.config(state=tk.NORMAL)
    chat_window.insert(tk.END, "You: " + user_input + "\n")
    chat_window.config(state=tk.DISABLED)
    chat_window.yview(tk.END)
    
    # Update the UI immediately
    root.update_idletasks()
    
    # Query the database
    if use_knowledge and selected_kbs:
        context_text, sources = query_vector_database(user_input, selected_kbs)
    else:
        context_text, sources = None, []
    
    try:
        chat_window.config(state=tk.NORMAL)
        chat_window.insert(tk.END, "Bot: ")
        chat_window.config(state=tk.DISABLED)
        chat_window.yview(tk.END)
        
        response_generator = get_interpreter_response(context_text, user_input)
        full_response = ""
        for message in response_generator:
            if isinstance(message, dict) and 'content' in message:
                content = message['content']
                if content is not None:
                    content = str(content)  # Convert content to string
                    full_response += content
                    chat_window.config(state=tk.NORMAL)
                    chat_window.insert(tk.END, content)
                    chat_window.config(state=tk.DISABLED)
                    chat_window.yview(tk.END)
                    root.update_idletasks()  # Update the UI after each chunk
        
        chat_window.config(state=tk.NORMAL)
        chat_window.insert(tk.END, "\n")
        if use_knowledge and sources:
            chat_window.insert(tk.END, "Sources:\n" + "\n".join(sources) + "\n")
        chat_window.config(state=tk.DISABLED)
        chat_window.yview(tk.END)
        
        if is_voice_mode:
            text_to_speech(full_response)
    except Exception as e:
        error_message = f"There was an error processing your request: {str(e)}"
        chat_window.config(state=tk.NORMAL)
        chat_window.insert(tk.END, "Bot: " + error_message + "\n")
        chat_window.config(state=tk.DISABLED)
        chat_window.yview(tk.END)
        print(f"Error: {e}")  # Print the exception details

def sanitize(filename):
    """Sanitize to remove invalid characters."""
    return re.sub(r'[<>:"/\\|?*\n]', '_', filename)

def get_interpreter_response(context, query):
    # Check if the query is a hard-coded command
    command_response = commands.execute_command(query)
    
    if command_response is None:
        # No command matched, treat as a regular query
        message = query
    else:
        message = command_response

    # If context is None or empty, just use the query
    if not context:
        prompt = query
    else:
        # Combine context and query in a more clear way
        prompt = f"Context: {context}\n\nQuery: {query}"
        
    sanitized_prompt = sanitize(prompt)
    message = sanitized_prompt

    return interpreter.chat(message, display=False, stream=True)

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
    chat_window.insert(tk.END, "System: Interrupted\n")
    chat_window.config(state=tk.DISABLED)
    chat_window.yview(tk.END)

def toggle_mode():
    global is_voice_mode, listen_thread
    is_voice_mode = not is_voice_mode
    if is_voice_mode:
        mode_button.config(text="Switch to Text Mode")
        input_box.pack_forget()
        send_button.pack_forget()
        speak_button.pack(side=tk.LEFT, padx=5)
        # Start continuous listening
        listen_thread = threading.Thread(target=continuous_listen, daemon=True)
        listen_thread.start()
    else:
        mode_button.config(text="Switch to Voice Mode")
        speak_button.pack_forget()
        input_box.pack(padx=10, pady=10, fill=tk.X, expand=False)
        send_button.pack(side=tk.LEFT, padx=5)
        # Stop continuous listening
        if listen_thread:
            global is_listening
            is_listening = False
            listen_thread.join()

def continuous_listen():
    global is_listening
    is_listening = True
    recognizer = sr.Recognizer()
    beep = generate_beep()
    while is_listening:
        try:
            with sr.Microphone() as source:
                print("Listening for wake word...")
                audio = recognizer.listen(source, phrase_time_limit=3)
            
            text = recognizer.recognize_google(audio).lower()
            print(f"Heard: {text}")
            if wake_word in text:
                print("Wake word detected!")
                beep.play()  # Play the beep sound
                recognize_speech()
        except sr.UnknownValueError:
            pass
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")

def toggle_kb(kb_name):
    if kb_name in selected_kbs:
        selected_kbs.remove(kb_name)
    else:
        selected_kbs.append(kb_name)

def create_kb_checkboxes(parent):
    kb_frame = ttk.LabelFrame(parent, text="Knowledge Bases")
    kb_frame.pack(padx=10, pady=10, fill=tk.X)

    # Get the list of knowledge bases (assuming they are subdirectories in the CHROMA_PATH)
    kb_list = [d for d in os.listdir(CHROMA_PATH) if os.path.isdir(os.path.join(CHROMA_PATH, d))]

    for kb in kb_list:
        var = tk.BooleanVar()
        cb = ttk.Checkbutton(kb_frame, text=kb, variable=var, command=lambda k=kb: toggle_kb(k))
        cb.pack(anchor=tk.W)

def open_settings():
    settings_window = tk.Toplevel(root)
    settings_window.title("Settings")
    settings_window.geometry("400x600")

    ttk.Label(settings_window, text="Use Knowledge Base:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
    use_knowledge_var = tk.BooleanVar(value=use_knowledge)
    ttk.Checkbutton(settings_window, variable=use_knowledge_var).grid(row=0, column=1, padx=10, pady=5)

    ttk.Label(settings_window, text="Supports Vision:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
    supports_vision_var = tk.BooleanVar(value=interpreter.llm.supports_vision)
    ttk.Checkbutton(settings_window, variable=supports_vision_var).grid(row=1, column=1, padx=10, pady=5)

    ttk.Label(settings_window, text="Supports Functions:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
    supports_functions_var = tk.BooleanVar(value=interpreter.llm.supports_functions)
    ttk.Checkbutton(settings_window, variable=supports_functions_var).grid(row=2, column=1, padx=10, pady=5)

    ttk.Label(settings_window, text="Loop:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
    loop_var = tk.BooleanVar(value=interpreter.loop)
    ttk.Checkbutton(settings_window, variable=loop_var).grid(row=3, column=1, padx=10, pady=5)

    ttk.Label(settings_window, text="Auto Run:").grid(row=4, column=0, padx=10, pady=5, sticky="w")
    auto_run_var = tk.BooleanVar(value=interpreter.auto_run)
    ttk.Checkbutton(settings_window, variable=auto_run_var).grid(row=4, column=1, padx=10, pady=5)

    ttk.Label(settings_window, text="Temperature:").grid(row=5, column=0, padx=10, pady=5, sticky="w")
    temperature_var = tk.DoubleVar(value=interpreter.llm.temperature)
    ttk.Entry(settings_window, textvariable=temperature_var).grid(row=5, column=1, padx=10, pady=5)

    ttk.Label(settings_window, text="Max Response Tokens:").grid(row=6, column=0, padx=10, pady=5, sticky="w")
    max_tokens_var = tk.IntVar(value=interpreter.llm.max_tokens)
    ttk.Entry(settings_window, textvariable=max_tokens_var).grid(row=6, column=1, padx=10, pady=5)

    ttk.Label(settings_window, text="Max Context Tokens:").grid(row=7, column=0, padx=10, pady=5, sticky="w")
    context_window_var = tk.IntVar(value=interpreter.llm.context_window)
    ttk.Entry(settings_window, textvariable=context_window_var).grid(row=7, column=1, padx=10, pady=5)

    # Add Knowledge Base checkboxes
    kb_frame = ttk.LabelFrame(settings_window, text="Knowledge Bases")
    kb_frame.grid(row=8, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

    # Get the list of knowledge bases (assuming they are subdirectories in the CHROMA_PATH)
    kb_list = [d for d in os.listdir(CHROMA_PATH) if os.path.isdir(os.path.join(CHROMA_PATH, d))]

    kb_vars = {}
    for i, kb in enumerate(kb_list):
        kb_vars[kb] = tk.BooleanVar(value=kb in selected_kbs)
        cb = ttk.Checkbutton(kb_frame, text=kb, variable=kb_vars[kb])
        cb.grid(row=i, column=0, sticky="w", padx=5, pady=2)

    # Add Reset Chat button
    reset_button = ttk.Button(settings_window, text="Reset Chat", command=reset_chat)
    reset_button.grid(row=9, column=0, columnspan=2, pady=5)

    # Add to Knowledge Base button
    add_kb_button = ttk.Button(settings_window, text="Add to Knowledge Base", command=add_to_knowledge_base)
    add_kb_button.grid(row=10, column=0, columnspan=2, pady=5)

    def save_settings():
        global use_knowledge, selected_kbs
        use_knowledge = use_knowledge_var.get()
        interpreter.llm.supports_vision = supports_vision_var.get()
        interpreter.llm.supports_functions = supports_functions_var.get()
        interpreter.loop = loop_var.get()
        interpreter.auto_run = auto_run_var.get()
        interpreter.llm.temperature = temperature_var.get()
        interpreter.llm.max_tokens = max_tokens_var.get()
        interpreter.llm.context_window = context_window_var.get()
        
        # Update selected knowledge bases
        selected_kbs = [kb for kb, var in kb_vars.items() if var.get()]
        
        settings_window.destroy()

    ttk.Button(settings_window, text="Save", command=save_settings).grid(row=11, column=0, columnspan=2, pady=20)

def text_to_speech(text):
    pygame.mixer.init()
    response = client.audio.speech.create(
        model=TTS_SETTINGS["model"],
        voice=TTS_SETTINGS["voice"],
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

def add_to_knowledge_base():
    # Get list of existing knowledge bases
    kb_list = [d for d in os.listdir(KB_PATH) if os.path.isdir(os.path.join(KB_PATH, d))]
    
    # Create a new top-level window for KB selection or creation
    kb_window = tk.Toplevel(root)
    kb_window.title("Add to Knowledge Base")
    kb_window.geometry("300x150")
    
    def select_existing_kb():
        kb_name = kb_var.get()
        kb_window.destroy()
        add_content_to_kb(kb_name)
    
    def create_new_kb():
        new_kb_name = simpledialog.askstring("New Knowledge Base", "Enter name for new knowledge base:")
        if new_kb_name:
            new_kb_path = os.path.join(KB_PATH, new_kb_name)
            os.makedirs(os.path.join(new_kb_path, "docs"), exist_ok=True)
            with open(os.path.join(new_kb_path, "urls.txt"), 'w') as f:
                pass  # Create empty urls.txt file
            kb_window.destroy()
            add_content_to_kb(new_kb_name)
    
    kb_var = tk.StringVar()
    kb_dropdown = ttk.Combobox(kb_window, textvariable=kb_var, values=kb_list, state="readonly")
    kb_dropdown.set("Select knowledge base")
    kb_dropdown.pack(pady=10)
    
    select_button = tk.Button(kb_window, text="Select Existing KB", command=select_existing_kb)
    select_button.pack(pady=5)
    
    create_button = tk.Button(kb_window, text="Create New KB", command=create_new_kb)
    create_button.pack(pady=5)
    
    kb_window.transient(root)
    kb_window.grab_set()
    root.wait_window(kb_window)

def add_content_to_kb(kb_name):
    content_window = tk.Toplevel(root)
    content_window.title(f"Add to {kb_name}")
    content_window.geometry("300x150")
    
    def add_file():
        file_path = filedialog.askopenfilename()
        if file_path:
            dest_path = os.path.join(KB_PATH, kb_name, "docs", os.path.basename(file_path))
            shutil.copy2(file_path, dest_path)
            update_kb()
    
    def add_url():
        url = simpledialog.askstring("Add URL", "Enter URL to add:")
        if url:
            with open(os.path.join(KB_PATH, kb_name, "urls.txt"), 'a') as f:
                f.write(url + '\n')
            update_kb()
    
    def update_kb():
        content_window.destroy()
        build_vector_database(kb_name)  # Pass the specific knowledge base name
        messagebox.showinfo("Success", f"Knowledge base '{kb_name}' updated successfully!")
    
    file_button = tk.Button(content_window, text="Add File", command=add_file)
    file_button.pack(pady=10)
    
    url_button = tk.Button(content_window, text="Add URL", command=add_url)
    url_button.pack(pady=10)
    
    content_window.transient(root)
    content_window.grab_set()
    root.wait_window(content_window)

# Set up the main application window
root = tk.Tk()
root.title("Chat UI")

# Configure the interpreter
configure_interpreter()

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# Create a menu bar
menu_bar = tk.Menu(root)
root.config(menu=menu_bar)

# Create a File menu
file_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Settings", command=open_settings)

# Bind Ctrl+C to the interrupt function
root.bind('<Control-c>', interrupt)
root.bind('<Return>', send_message)

# Create a scrolled text widget for the chat window
chat_window = scrolledtext.ScrolledText(root, wrap=tk.WORD, state=tk.DISABLED)
chat_window.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

# Create a text widget for user input (initially visible)
input_box = tk.Text(root, height=3)
input_box.pack(padx=10, pady=10, fill=tk.X, expand=False)

# Create a frame for buttons
button_frame = tk.Frame(root)
button_frame.pack(padx=10, pady=10, fill=tk.X)

# Create a send button (initially visible)
send_button = tk.Button(button_frame, text="Send", command=send_message)
send_button.pack(side=tk.LEFT, padx=5)

# Create a speak button (initially hidden)
speak_button = tk.Button(button_frame, text="Speak", command=recognize_speech)

# Create an interrupt button
interrupt_button = tk.Button(button_frame, text="Interrupt", command=interrupt)
interrupt_button.pack(side=tk.LEFT, padx=5)

# Create a mode toggle button
mode_button = tk.Button(button_frame, text="Switch to Voice Mode", command=toggle_mode)
mode_button.pack(side=tk.LEFT, padx=5)

# Run the application
root.mainloop()