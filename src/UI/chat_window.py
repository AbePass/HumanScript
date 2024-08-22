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

def sanitize_filename(filename):
    # Remove or replace invalid characters
    sanitized = re.sub(r'[\\/*?:"<>|\n\r\t]', '', filename)
    sanitized = re.sub(r'\s+', '_', sanitized)  # Replace whitespace with underscore
    sanitized = sanitized.strip('._')  # Remove leading/trailing dots and underscores
    return sanitized or 'unnamed_conversation'  # Default name if empty

class ChatUI:
    def __init__(self, root, interpreter_manager):
        logging.debug("Initializing ChatUI")
        self.root = root
        self.root.title("OpenPI Chat")

        self.selected_kbs = DEFAULT_SELECTED_KBS.copy()
        self.wake_word = WAKE_WORD
        self.is_listening = False
        self.listen_thread = None
        self.is_voice_mode = False
        self.continuous_listen_thread = None
        self.interpreter_settings = INTERPRETER_SETTINGS.copy()
        self.env_vars = {k: v for k, v in os.environ.items() if k.startswith("CUSTOM_")}
        self.streaming_message = ""
        self.last_message_type = None  # To keep track of the last message type (user or AI)

        self.chat_manager = ChatManager(self)
        self.audio_manager = AudioManager()
        self.knowledge_manager = KnowledgeManager(self)
        self.interpreter_manager = interpreter_manager
        self.context_manager = ContextManager(self)

        self.input_box = ctk.CTkTextbox(root, height=50, fg_color=get_color("BG_INPUT"), text_color=get_color("TEXT_PRIMARY"))
        
        self.create_ui()

    def create_ui(self):
        logging.debug("Creating UI")
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
        logging.debug("UI creation complete")

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

    def create_chat_window(self, parent):
        logging.debug("Creating chat window")
        chat_frame = ctk.CTkFrame(parent, fg_color=get_color("BG_TERTIARY"))
        chat_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        chat_frame.grid_rowconfigure(0, weight=1)
        chat_frame.grid_columnconfigure(0, weight=1)

        self.chat_window = ctk.CTkTextbox(chat_frame, wrap="word", state="disabled", cursor="arrow", fg_color=get_color("BG_TERTIARY"), text_color=get_color("TEXT_PRIMARY"))
        self.chat_window.grid(row=0, column=0, sticky="nsew")

        # Configure tags for text coloring and alignment
        self.chat_window.tag_config("user", foreground=BRAND_PRIMARY, justify="right")
        self.chat_window.tag_config("bot", foreground=BRAND_SECONDARY, justify="left")
        self.chat_window.tag_config("bot_stream", foreground=get_color("TEXT_SECONDARY"), justify="left")
        self.chat_window.tag_config("bot_final", foreground=BRAND_SECONDARY, justify="left")

        scrollbar = ctk.CTkScrollbar(chat_frame, command=self.chat_window.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.chat_window.configure(yscrollcommand=scrollbar.set)

    def create_input_area(self, parent):
        logging.debug("Creating input area")
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
                    self.chat_window.configure(state="normal")
                    self.chat_window.insert(ctk.END, "Listening...\n", "bot_stream")
                    self.chat_window.configure(state="disabled")
                    self.chat_window.yview(ctk.END)
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
        self.interpreter_manager.update_selected_kbs(self.selected_kbs)

    def send_message(self, user_input=None):
        if not self.is_voice_mode:
            user_input = self.input_box.get("1.0", ctk.END).strip()
        
        if user_input:
            self.chat_window.configure(state="normal")
            self.chat_window.insert(ctk.END, "You: " + user_input + "\n", "user")
            self.chat_window.configure(state="disabled")
            self.chat_window.see(ctk.END)
            self.root.update_idletasks()

            if not self.is_voice_mode:
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
        self.chat_window.configure(state="normal")
        self.chat_window.insert(ctk.END, "Bot: ", "bot")
        
        # Add indicator for knowledge base query
        if self.selected_kbs:
            self.chat_window.insert(ctk.END, "Knowledge bases being queried:\n", "bot_stream")
            for kb in self.selected_kbs:
                self.chat_window.insert(ctk.END, f"- {kb}\n", "bot_stream")
        self.chat_window.see(ctk.END)
        self.root.update_idletasks()
        
        stream_start = self.chat_window.index(ctk.END)
        full_response = ""

        try:
            for message in response_generator:
                if isinstance(message, dict) and 'content' in message:
                    content = message['content']
                    if content is not None:
                        content = str(content)
                        full_response += content
                        self.chat_window.insert(ctk.END, content, "bot_stream")
                        self.chat_window.see(ctk.END)
                        self.root.update_idletasks()
        except Exception as e:
            print(f"Error processing response: {e}")
            logging.exception("Error processing response")

        # Get the final response from the last message
        final_response = interpreter.messages[-1]['content'] if interpreter.messages else full_response
        
        # Insert a newline before the final response
        self.chat_window.insert(ctk.END, "\n", "bot")
        
        # Insert the final response on a new line
        self.chat_window.insert(ctk.END, "Final response:\n", "bot_final")
        self.chat_window.insert(ctk.END, final_response, "bot_final")
        
        if sources:
            self.chat_window.insert(ctk.END, "\nSources:\n", "bot_final")
            for source in sources:
                self.chat_window.insert(ctk.END, f"- {source}\n", "bot_stream")
        
        self.chat_window.insert(ctk.END, "\n")
        self.chat_window.configure(state="disabled")
        self.chat_window.see(ctk.END)
        
        if self.is_voice_mode:
            threading.Thread(target=self.audio_manager.text_to_speech, args=(final_response,), daemon=True).start()

    def reset_chat(self):
        interpreter.reset()
        self.chat_window.configure(state="normal")
        self.chat_window.delete("1.0", ctk.END)
        self.chat_window.configure(state="disabled")

    def open_settings(self):
        SettingsWindow(self.root, self)
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
        custom_env_vars = list(self.env_vars.keys())
        env_var_message = "The following custom environment variables are available: " + ", ".join(custom_env_vars)
        interpreter.system_message = interpreter.system_message.split("\n\n")[0] + f"\n\n{env_var_message}"
        # Update ChatManager
        self.chat_manager.update_env_vars(self.env_vars)