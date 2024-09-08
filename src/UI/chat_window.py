import customtkinter as ctk
import os
import threading
import logging
from datetime import datetime
from Settings.config import *
from Core.chat_manager import ChatManager
from Core.audio_manager import AudioManager
from Core.knowledge_manager import KnowledgeManager
from Core.interpreter_manager import InterpreterManager
from Core.context_manager import ContextManager
from interpreter import interpreter
from UI.settings_window import SettingsWindow
from Settings.color_settings import *
import re
import tkinter as tk
from tkinter import ttk, filedialog, simpledialog, messagebox
from collections import OrderedDict

def sanitize_filename(filename):
  # Remove or replace invalid characters
  sanitized = re.sub(r'[\\/*?:"<>|\n\r\t]', '', filename)
  sanitized = re.sub(r'\s+', '_', sanitized)  # Replace whitespace with underscore
  sanitized = sanitized.strip('._')  # Remove leading/trailing dots and underscores
  return sanitized or 'unnamed_conversation'  # Default name if empty

class ChatUI:
  def __init__(self, root, interpreter_manager):
    self.root = root
    self.root.title("HumanScript Chat")

    self.selected_kbs = DEFAULT_SELECTED_KBS.copy()
    self.wake_word = WAKE_WORD
    self.is_listening = False
    self.listen_thread = None
    self.is_voice_mode = False
    self.continuous_listen_thread = None
    self.interpreter_settings = INTERPRETER_SETTINGS.copy()
    self.env_vars = OrderedDict()
    self.streaming_message = ""
    self.last_message_type = None  # To keep track of the last message type (user or AI)
    print(interpreter.system_message)

    self.chat_manager = ChatManager(self)
    self.audio_manager = AudioManager()
    self.knowledge_manager = KnowledgeManager(self)
    self.context_manager = ContextManager(self)

    self.input_box = ctk.CTkTextbox(root, height=50, fg_color=get_color("BG_INPUT"), text_color=get_color("TEXT_PRIMARY"))
    
    self.create_ui()
    self.streaming_label = None

  def create_ui(self):
    self.root.grid_rowconfigure(0, weight=1)
    self.root.grid_columnconfigure(1, weight=1)

    # Sidebar
    self.sidebar = ctk.CTkFrame(self.root, width=250, fg_color=get_color("BG_SECONDARY"))
    self.sidebar.grid(row=0, column=0, sticky="nsew")
    self.create_sidebar()

    # Main chat area
    self.main_frame = ctk.CTkFrame(self.root, fg_color=get_color("BG_PRIMARY"))
    self.main_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
    self.main_frame.grid_rowconfigure(0, weight=1)
    self.main_frame.grid_columnconfigure(0, weight=1)

    self.create_chat_window(self.main_frame)
    self.create_input_area(self.main_frame)

    self.root.bind('<Return>', self.send_message)

  def create_sidebar(self):
    # Knowledge base section
    kb_label = ctk.CTkLabel(self.sidebar, text="Knowledge Bases:", anchor="w")
    kb_label.pack(padx=20, pady=(20, 5), fill="x")

    self.kb_frame = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent")
    self.kb_frame.pack(padx=20, pady=(0, 20), fill="both", expand=True)

    self.kb_toggles = {}
    for kb in self.knowledge_manager.get_knowledge_bases():
      toggle = ctk.CTkCheckBox(self.kb_frame, text=kb, command=lambda kb=kb: self.toggle_kb(kb))
      toggle.pack(anchor="w", pady=2)
      self.kb_toggles[kb] = toggle

    # Add settings icon to the sidebar
    settings_icon = ctk.CTkButton(
      self.sidebar, 
      text="⚙️ Settings", 
      command=self.open_settings, 
      fg_color=get_color("BG_INPUT"), 
      text_color=BRAND_PRIMARY, 
      hover_color=BRAND_ACCENT, 
      border_width=2, 
      border_color=BRAND_PRIMARY,
      font=("Helvetica", 16)
    )
    settings_icon.pack(pady=10, padx=20, fill="x")

  def refresh_knowledge_bases(self):
    # Clear the current knowledge base toggles
    for widget in self.kb_frame.winfo_children():
      widget.destroy()

    # Recreate the knowledge base toggles
    self.kb_toggles = {}
    for kb in self.knowledge_manager.get_knowledge_bases():
      toggle = ctk.CTkCheckBox(self.kb_frame, text=kb, command=lambda kb=kb: self.toggle_kb(kb))
      toggle.pack(anchor="w", pady=2)
      self.kb_toggles[kb] = toggle

    # Update the selected knowledge bases in the knowledge manager
    selected_kbs = [kb for kb, toggle in self.kb_toggles.items() if toggle.get()]
    self.knowledge_manager.update_selected_kbs(selected_kbs)


  def create_chat_window(self, parent):
    chat_frame = ctk.CTkFrame(parent, fg_color=get_color("BG_TERTIARY"))
    chat_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
    chat_frame.grid_rowconfigure(0, weight=1)
    chat_frame.grid_columnconfigure(0, weight=1)

    self.chat_canvas = ctk.CTkCanvas(chat_frame, bg=get_color("BG_TERTIARY"), highlightthickness=0)
    self.chat_canvas.grid(row=0, column=0, sticky="nsew")

    self.message_frame = ctk.CTkFrame(self.chat_canvas, fg_color=get_color("BG_TERTIARY"))
    self.canvas_frame = self.chat_canvas.create_window((0, 0), window=self.message_frame, anchor="nw")

    scrollbar = ctk.CTkScrollbar(chat_frame, command=self.chat_canvas.yview)
    scrollbar.grid(row=0, column=1, sticky="ns")

    self.chat_canvas.configure(yscrollcommand=scrollbar.set)

    self.message_frame.bind("<Configure>", self.on_frame_configure)
    self.chat_canvas.bind("<Configure>", self.on_canvas_configure)

  def on_frame_configure(self, event):
    self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all"))

  def on_canvas_configure(self, event):
    self.chat_canvas.itemconfig(self.canvas_frame, width=event.width)

  def create_chat_bubble(self, message, is_user):
    bubble_frame = ctk.CTkFrame(self.message_frame, fg_color=BRAND_PRIMARY if is_user else BRAND_SECONDARY)
    bubble_frame.pack(pady=5, padx=10, anchor="e" if is_user else "w")

    message_label = ctk.CTkLabel(
      bubble_frame,
      text=message,
      wraplength=400,
      justify="right" if is_user else "left",
      text_color=get_color("TEXT_PRIMARY")
    )
    message_label.pack(padx=10, pady=5)

    self.chat_canvas.update_idletasks()
    self.chat_canvas.yview_moveto(1.0)

  def create_streaming_label(self):
    self.streaming_label = ctk.CTkLabel(
      self.message_frame,
      text="",
      wraplength=400,
      justify="left",
      text_color=get_color("TEXT_PRIMARY")
    )
    self.streaming_label.pack(pady=5, padx=10, anchor="w")

  def update_streaming_label(self, text):
    if self.streaming_label:
      self.streaming_label.configure(text=text)
      self.chat_canvas.update_idletasks()
      self.chat_canvas.yview_moveto(1.0)

  def create_input_area(self, parent):
    input_frame = ctk.CTkFrame(parent, fg_color=get_color("BG_PRIMARY"))
    input_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
    input_frame.grid_columnconfigure(0, weight=1)

    self.input_box = ctk.CTkTextbox(input_frame, height=50, fg_color=get_color("BG_INPUT"), text_color=get_color("TEXT_PRIMARY"))
    self.input_box.grid(row=0, column=0, sticky="ew", padx=(0, 5))

    # Use Unicode microphone character
    self.mode_button = ctk.CTkButton(input_frame, text="🎤", width=50, height=50, command=self.toggle_mode, 
                                     fg_color=get_color("BG_INPUT"), text_color=BRAND_PRIMARY, 
                                     hover_color=BRAND_ACCENT, border_width=2, border_color=BRAND_PRIMARY,
                                     font=("Helvetica", 16))
    self.mode_button.grid(row=0, column=1)

  def toggle_mode(self):
    self.is_voice_mode = not self.is_voice_mode
    if self.is_voice_mode:
      self.mode_button.configure(fg_color=BRAND_PRIMARY, text_color=get_color("TEXT_PRIMARY"), border_width=0)
      self.input_box.configure(state="disabled")
      self.start_listening()
    else:
      self.mode_button.configure(fg_color="transparent", text_color=BRAND_PRIMARY, border_width=2)
      self.input_box.configure(state="normal")
      self.stop_listening()

  def continuous_listen(self):
    while self.audio_manager.is_listening:
      try:
        wake_word_detected = self.audio_manager.listen_for_wake_word(wake_word=self.wake_word)
        if wake_word_detected:
          self.audio_manager.generate_beep()
          self.create_chat_bubble("Listening...", is_user=False)
          self.process_speech_input()
      except Exception as e:
        logging.error(f"Error in continuous listening: {str(e)}")

  def process_speech_input(self):
    user_input = self.audio_manager.recognize_speech()
    if user_input and not user_input.startswith("Error"):
      self.send_message(user_input=user_input)

  def start_listening(self):
    self.audio_manager.is_listening = True
    self.continuous_listen_thread = threading.Thread(target=self.continuous_listen, daemon=True)
    self.continuous_listen_thread.start()

  def stop_listening(self):
    if self.continuous_listen_thread:
      self.audio_manager.is_listening = False
      self.continuous_listen_thread.join(timeout=2)
    if self.continuous_listen_thread.is_alive():
      logging.warning("Continuous listen thread did not stop in time")

  def toggle_kb(self, kb):
    is_active = self.kb_toggles[kb].get()
    if is_active:
      self.selected_kbs.append(kb)
    else:
      self.selected_kbs.remove(kb)
      self.context_manager.clear_custom_instructions()  # Clear custom instructions when KB is turned off
    self.knowledge_manager.update_selected_kbs(self.selected_kbs)

  def send_message(self, user_input=None):
    if not self.is_voice_mode:
      user_input = self.input_box.get("1.0", ctk.END).strip()
    
    if user_input:
      self.create_chat_bubble(f"{user_input}", is_user=True)
      self.input_box.delete("1.0", ctk.END)
      # Modify the filename generation for the interpreter
      timestamp = datetime.now().strftime("%Y_%m_%d_%H-%M-%S")
      sanitized_query = sanitize_filename(user_input[:50])  # Limit to first 50 characters
      filename = f"Context_{sanitized_query}_{timestamp}.json"
      
      # Set the custom filename for the interpreter
      interpreter.conversation_filename = filename
      
      # Start a new thread for processing the response
      threading.Thread(target=self.process_response, args=(user_input,), daemon=True).start()
      
  def process_response(self, user_input):
    response_generator, sources = self.chat_manager.process_input(user_input, self.selected_kbs)
    
    # Add indicator for knowledge base query
    if self.selected_kbs:
      kb_info = "Knowledge bases being queried:\n" + "\n".join(f"- {kb}" for kb in self.selected_kbs)
      self.create_chat_bubble(kb_info, is_user=False)
    
    self.create_streaming_label()
    full_response = ""
    for message in response_generator:
      if isinstance(message, dict) and 'content' in message:
        content = message['content']
        if content is not None:
          content = str(content)
          full_response += content
          self.update_streaming_label(f"{full_response}")

    # Remove the streaming label
    if self.streaming_label:
      self.streaming_label.destroy()
      self.streaming_label = None

    # Get the final response from the last message if the role is "assistant" otherwise return "no response"
    if interpreter.messages and interpreter.messages[-1]['role'] == 'assistant':
      final_response = interpreter.messages[-1]['content']
    else:
      final_response = "no response"
    
    # Insert the final response as a chat bubble
    self.create_chat_bubble(f"{final_response}", is_user=False)
    
    if sources:
      sources_text = "Sources:\n" + "\n".join(f"- {source}" for source in sources)
      self.create_chat_bubble(sources_text, is_user=False)
    
    if self.is_voice_mode:
      threading.Thread(target=self.audio_manager.text_to_speech, args=(final_response,), daemon=True).start()

  def reset_chat(self):
    interpreter.reset()
    for widget in self.message_frame.winfo_children():
      widget.destroy()
    self.streaming_label = None

  def open_settings(self):
    # Clear the main frame and display settings
    for widget in self.main_frame.winfo_children():
      widget.destroy()
    SettingsWindow(self.main_frame, self)
    # After settings are saved, update the chat manager
    self.chat_manager.update_selected_kbs(self.selected_kbs)
    self.chat_manager.update_wake_word(self.wake_word)

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
      custom_env_vars = sorted(set(key for key in self.env_vars.keys() if key.startswith("CUSTOM_")))
      env_var_message = "\n- ".join(custom_env_vars)
      
      interpreter.system_message = (
          f"{SYSTEM_MESSAGE}\n"
          f"{SYSTEM_MESSAGE_ENV_VARS}\n"
          f"\n- {env_var_message}"
      )
      print(interpreter.system_message)
      
      # Update ChatManager
      self.chat_manager.update_env_vars(self.env_vars)
