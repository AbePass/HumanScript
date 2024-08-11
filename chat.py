import tkinter as tk
from tkinter import scrolledtext, simpledialog, ttk
from interpreter import interpreter
import os
import speech_recognition as sr
from openai import OpenAI
import threading
from query_vector_database import query_vector_database, CHROMA_PATH
import tempfile
import re
import pygame
import time
import numpy as np

use_knowledge = True
# Add this global variable to store the selected knowledge bases
selected_kbs = []

# Add these global variables at the top of your file
wake_word = "hey computer"
is_listening = False
listen_thread = None

def configure_interpreter():
    #TODO: system_message use that
    interpreter.system_message = '''

    ### Permissions and Environment:
    - You have **full permission** to run code and shell commands on the user's computer.
    - Use the Desktop as your default working directory. Save all files on the Desktop unless directed otherwise.

    ### Execution and Response:
    - When a query involves running a command or code, execute it immediately and provide the output.
    - If additional context is provided, use it to inform your actions and responses.
    - Expect prompts in the format:

    Context: {context}

    Query: {query}

    - Use the provided context to shape your response accurately.

    ### Referencing and Searching:
    - If you need to refer to prior interactions, access the "conversation_history" folder.
    - For web-based queries, utilize the `computer.browser.search(query)` function as needed.

    ### Communication Style:
    - Your responses will be spoken aloud to the user. Therefore, ensure your answers are clear, concise, and naturally suited for verbal communication.
    - Do not repeat yourself in your responses.

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
    interpreter.loop = True
    interpreter.llm.temperature = 0.3
    interpreter.llm.max_tokens = 4096
    interpreter.llm.context_window = 10000
    interpreter.conversation_history_path = "conversation_history"
    interpreter.computer.import_computer_api = True

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
        interpreter.llm.model = f"anthropic/{model}"

def send_message(event=None):
    user_input = input_box.get("1.0", tk.END).strip()
    if user_input:
        chat_window.config(state=tk.NORMAL)
        chat_window.insert(tk.END, "You: " + user_input + "\n")
        chat_window.config(state=tk.DISABLED)
        input_box.delete("1.0", tk.END)
        # Query the database
        if use_knowledge and selected_kbs:
            context_text, sources = query_vector_database(user_input, selected_kbs)
        else:
            context_text, sources = None, []
        
        try:
            response = get_interpreter_response(context_text, user_input)
        except Exception as e:
            response = f"There was an error processing your request: {e}"
            print(f"Error: {e}")  # Print the exception details
        
        chat_window.config(state=tk.NORMAL)
        chat_window.insert(tk.END, "Bot: " + response + "\n")
        if use_knowledge and sources:
            chat_window.insert(tk.END, "Sources:\n" + "\n".join(sources) + "\n")
        chat_window.config(state=tk.DISABLED)
        chat_window.yview(tk.END)
        
        if tts_var.get():
            text_to_speech(response)

def sanitize(filename):
    """Sanitize to remove invalid characters."""
    return re.sub(r'[<>:"/\\|?*\n]', '_', filename)

def get_interpreter_response(context, query):
    # If context is None or empty, just use the query
    if not context:
        prompt = query
    else:
        # Combine context and query in a more clear way
        prompt = f"Context: {context}\n\nQuery: {query}"
    
    sanitized_prompt = sanitize(prompt)
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

def generate_beep():
    pygame.mixer.init(frequency=44100, size=-16, channels=2)
    duration = 0.2  # Duration of the beep in seconds
    frequency = 440  # Frequency of the beep in Hz (A4 note)
    sample_rate = 44100
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    beep = np.sin(2 * np.pi * frequency * t)
    beep = (beep * 32767).astype(np.int16)
    stereo_beep = np.column_stack((beep, beep))  # Create stereo audio
    return pygame.sndarray.make_sound(stereo_beep)

def continuous_listen():
    global is_listening
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

def recognize_speech(event=None):
    # Stop the text-to-speech playback if pygame mixer is initialized
    if pygame.mixer.get_init():
        pygame.mixer.music.stop()
    
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        chat_window.config(state=tk.NORMAL)
        chat_window.insert(tk.END, "System: Listening for command...\n")
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

def toggle_listening():
    global is_listening, listen_thread
    if is_listening:
        is_listening = False
        listen_button.config(text="Start Listening")
        chat_window.config(state=tk.NORMAL)
        chat_window.insert(tk.END, "System: Stopped listening for wake word.\n")
        chat_window.config(state=tk.DISABLED)
        chat_window.yview(tk.END)
    else:
        is_listening = True
        listen_button.config(text="Stop Listening")
        chat_window.config(state=tk.NORMAL)
        chat_window.insert(tk.END, "System: Started listening for wake word.\n")
        chat_window.config(state=tk.DISABLED)
        chat_window.yview(tk.END)
        listen_thread = threading.Thread(target=continuous_listen, daemon=True)
        listen_thread.start()

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
    settings_window.geometry("400x400")  # Increased height to accommodate KB checkboxes

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

    ttk.Button(settings_window, text="Save", command=save_settings).grid(row=9, column=0, columnspan=2, pady=20)

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

# Set up the main application window
root = tk.Tk()
root.title("Chat UI")

# Configure the interpreter
configure_interpreter()

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# Bind Ctrl+C to the interrupt function
root.bind('<Control-c>', interrupt)
root.bind('<Return>', send_message)

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

# Create a toggle listening button
listen_button = tk.Button(button_frame, text="Start Listening", command=toggle_listening)
listen_button.pack(side=tk.LEFT, padx=5)

# Add a Speak button
speak_button = tk.Button(button_frame, text="Speak", command=recognize_speech)
speak_button.pack(side=tk.LEFT, padx=5)

# Run the application
root.mainloop()