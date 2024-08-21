import tkinter as tk
from tkinter import simpledialog, ttk, filedialog, messagebox
import os
import threading
import logging
import importlib
from Settings.config import *
from Core.chat_manager import ChatManager
from Core.audio_manager import AudioManager
from Core.knowledge_manager import KnowledgeManager
from Core.interpreter_manager import InterpreterManager
from Core.context_manager import ContextManager
from interpreter import interpreter
from UI.settings_window import SettingsWindow

class ChatUI:
  def __init__(self, root):
    self.selected_kbs = DEFAULT_SELECTED_KBS.copy()
    self.wake_word = WAKE_WORD
    self.is_listening = False
    self.listen_thread = None
    self.is_voice_mode = False
    self.continuous_listen_thread = None
    self.interpreter_settings = INTERPRETER_SETTINGS.copy()
    self.env_vars = {k: v for k, v in os.environ.items() if k.startswith("CUSTOM_")}

    self.root = root
    self.root.title("OpenPI Chat")

    self.chat_manager = ChatManager(self)  # Pass self to ChatManager
    self.audio_manager = AudioManager()
    self.knowledge_manager = KnowledgeManager(self)
    self.interpreter_manager = InterpreterManager()
    self.context_manager = ContextManager(self)  # Pass self to ContextManager

    self.create_chat_window()
    self.create_input_box()
    self.create_buttons()

    self.root.bind('<Return>', self.send_message)

  def send_message(self, user_input=None):
    if not self.is_voice_mode:
      user_input = self.input_box.get("1.0", tk.END).strip()
    
    if user_input:
      self.chat_window.config(state=tk.NORMAL)
      self.chat_window.insert(tk.END, "You: " + user_input + "\n", "user")
      self.chat_window.config(state=tk.DISABLED)
      self.chat_window.yview(tk.END)
      self.root.update_idletasks()

      if not self.is_voice_mode:
        self.input_box.delete("1.0", tk.END)
      
      # Start a new thread for processing the response
      threading.Thread(target=self.process_response, args=(user_input,), daemon=True).start()

  def process_response(self, user_input):
    response_generator, sources = self.chat_manager.process_input(user_input, self.selected_kbs)
    print(sources)
    self.chat_window.config(state=tk.NORMAL)
    self.chat_window.insert(tk.END, "Bot: ", "bot")
    
    stream_start = self.chat_window.index(tk.END)
    full_response = ""

    for message in response_generator:
        if isinstance(message, dict) and 'content' in message:
            content = message['content']
            if content is not None:
                content = str(content)
                full_response += content
                self.chat_window.insert(tk.END, content, "bot_stream")
                self.chat_window.see(tk.END)
                self.root.update_idletasks()

    # Get the final response from the last message
    final_response = interpreter.messages[-1]['content'] if interpreter.messages else full_response
    self.chat_window.insert(tk.END, final_response, "bot_final")
    
    if sources:
        self.chat_window.insert(tk.END, "\nSources:\n" + "\n".join(sources) + "\n")
    
    self.chat_window.insert(tk.END, "\n\n")
    self.chat_window.config(state=tk.DISABLED)
    self.chat_window.yview(tk.END)
    
    if self.is_voice_mode:
      threading.Thread(target=self.audio_manager.text_to_speech, args=(final_response,), daemon=True).start()

  def reset_chat(self):
    self.chat_manager.reset()
    self.chat_window.config(state=tk.NORMAL)
    self.chat_window.delete("1.0", tk.END)
    self.chat_window.config(state=tk.DISABLED)

  def toggle_mode(self):
    self.is_voice_mode = not self.is_voice_mode
    if self.is_voice_mode:
        self.mode_button.config(text="Switch to Text Mode")
        self.input_box.pack_forget()
        self.send_button.pack_forget()
        self.speak_button.pack(side=tk.LEFT, padx=5)
        self.start_continuous_listening()
    else:
        self.mode_button.config(text="Switch to Voice Mode")
        self.speak_button.pack_forget()
        self.input_box.pack(padx=10, pady=10, fill=tk.X, expand=False)
        self.send_button.pack(side=tk.LEFT, padx=5)
        self.stop_continuous_listening()

  def start_continuous_listening(self):
    self.audio_manager.is_listening = True
    self.continuous_listen_thread = threading.Thread(target=self.continuous_listen, daemon=True)
    self.continuous_listen_thread.start()

  def stop_continuous_listening(self):
    if self.continuous_listen_thread:
        self.audio_manager.is_listening = False
        self.continuous_listen_thread.join(timeout=2)
        if self.continuous_listen_thread.is_alive():
            logging.warning("Continuous listen thread did not stop in time")

  def continuous_listen(self):
    while self.audio_manager.is_listening:
        try:
            wake_word_detected = self.audio_manager.listen_for_wake_word(wake_word=self.wake_word)
            if wake_word_detected:
                self.audio_manager.generate_beep()
                self.chat_window.config(state=tk.NORMAL)
                self.chat_window.insert(tk.END, "Listening...\n", "bot")
                self.chat_window.config(state=tk.DISABLED)
                self.chat_window.yview(tk.END)
                self.process_speech_input()
        except Exception as e:
            logging.error(f"Error in continuous listening: {str(e)}")

  def process_speech_input(self):
    user_input = self.audio_manager.recognize_speech()
    if user_input and not user_input.startswith("Error"):
      self.send_message(user_input=user_input)

  def create_chat_window(self):
    chat_frame = tk.Frame(self.root)
    chat_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
    self.chat_window = tk.Text(chat_frame, wrap=tk.WORD, state=tk.DISABLED, cursor="arrow")
    self.chat_window.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar = ttk.Scrollbar(chat_frame, command=self.chat_window.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    self.chat_window.config(yscrollcommand=scrollbar.set)
    self.chat_window.tag_configure("user", justify="right", foreground="blue")
    self.chat_window.tag_configure("bot", justify="left", foreground="green")
    self.chat_window.tag_configure("bot_stream", justify="left", foreground="gray")
    self.chat_window.tag_configure("bot_final", justify="left", foreground="green")

  def create_input_box(self):
    self.input_box = tk.Text(self.root, height=3)
    self.input_box.pack(padx=10, pady=10, fill=tk.X, expand=False)

  def open_settings(self):
    SettingsWindow(self.root, self)
    # After settings are saved, update the chat manager
    self.chat_manager.update_selected_kbs(self.selected_kbs)###updated sucsessfully
    self.chat_manager.update_wake_word(self.wake_word)

  def create_buttons(self):
    button_frame = tk.Frame(self.root)
    button_frame.pack(padx=10, pady=10, fill=tk.X)
    self.send_button = tk.Button(button_frame, text="Send", command=self.send_message)
    self.send_button.pack(side=tk.LEFT, padx=5)
    self.speak_button = tk.Button(button_frame, text="Speak", command=self.process_speech_input)
    self.mode_button = tk.Button(button_frame, text="Switch to Voice Mode", command=self.toggle_mode)
    self.mode_button.pack(side=tk.LEFT, padx=5)
    self.settings_button = tk.Button(button_frame, text="Settings", command=self.open_settings)
    self.settings_button.pack(side=tk.LEFT, padx=5)
    self.interrupt_button = tk.Button(button_frame, text="Interrupt", command=self.toggle_mode)
    self.interrupt_button.pack(side=tk.LEFT, padx=5)

  def update_interpreter_settings(self, new_settings):
    self.interpreter_settings.update(new_settings)
    # Update interpreter directly
    interpreter.llm.supports_vision = new_settings["supports_vision"]
    interpreter.llm.supports_functions = new_settings["supports_functions"]
    interpreter.auto_run = new_settings["auto_run"]
    interpreter.loop = new_settings["loop"]
    interpreter.llm.temperature = new_settings["temperature"]
    interpreter.llm.max_tokens = new_settings["max_tokens"]
    interpreter.llm.context_window = new_settings["context_window"]
    # Update ChatManager
    self.chat_manager.update_interpreter_settings(self.interpreter_settings)

  def update_env_vars(self, new_env_vars):
    self.env_vars.update(new_env_vars)
    for key, value in new_env_vars.items():
      os.environ[key] = value
    # Update system message
    custom_env_vars = list(self.env_vars.keys())
    env_var_message = "The following custom environment variables are available: " + ", ".join(custom_env_vars)
    interpreter.system_message = interpreter.system_message.split("\n\n")[0] + f"\n\n{env_var_message}"
    # Update ChatManager
    self.chat_manager.update_env_vars(self.env_vars)