import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from Settings.config import USE_KNOWLEDGE, DEFAULT_SELECTED_KBS, WAKE_WORD, INTERPRETER_SETTINGS, CHROMA_PATH, KB_PATH
from Core.knowledge_manager import KnowledgeManager
import json
import os
import shutil
from interpreter import interpreter

class SettingsWindow:
  def __init__(self, parent, chat_ui):
    self.parent = parent
    self.chat_ui = chat_ui
    self.window = tk.Toplevel(parent)
    self.window.title("Settings")
    self.window.geometry("500x700")
    self.window.resizable(False, False)

    self.knowledge_manager = KnowledgeManager(self.window)

    self.create_widgets()
    self.load_current_settings()

  def create_widgets(self):
    # Use Knowledge
    self.use_knowledge_var = tk.BooleanVar()
    ttk.Checkbutton(self.window, text="Use Knowledge", variable=self.use_knowledge_var).pack(pady=5)

    # Interpreter Settings
    interpreter_frame = ttk.LabelFrame(self.window, text="Interpreter Settings")
    interpreter_frame.pack(padx=10, pady=5, fill=tk.X)

    self.supports_vision_var = tk.BooleanVar()
    ttk.Checkbutton(interpreter_frame, text="Supports Vision", variable=self.supports_vision_var).pack(pady=2)

    self.supports_functions_var = tk.BooleanVar()
    ttk.Checkbutton(interpreter_frame, text="Supports Functions", variable=self.supports_functions_var).pack(pady=2)

    self.auto_run_var = tk.BooleanVar()
    ttk.Checkbutton(interpreter_frame, text="Auto Run", variable=self.auto_run_var).pack(pady=2)

    self.loop_var = tk.BooleanVar()
    ttk.Checkbutton(interpreter_frame, text="Loop", variable=self.loop_var).pack(pady=2)

    ttk.Label(interpreter_frame, text="Temperature:").pack(pady=2)
    self.temperature_var = tk.DoubleVar()
    ttk.Entry(interpreter_frame, textvariable=self.temperature_var).pack(pady=2)

    ttk.Label(interpreter_frame, text="Max Tokens:").pack(pady=2)
    self.max_tokens_var = tk.IntVar()
    ttk.Entry(interpreter_frame, textvariable=self.max_tokens_var).pack(pady=2)

    ttk.Label(interpreter_frame, text="Context Window:").pack(pady=2)
    self.context_window_var = tk.IntVar()
    ttk.Entry(interpreter_frame, textvariable=self.context_window_var).pack(pady=2)

    # Wake Word
    ttk.Label(self.window, text="Wake Word:").pack(pady=5)
    self.wake_word_entry = ttk.Entry(self.window, width=50)
    self.wake_word_entry.pack(pady=5)

    # Knowledge Bases
    kb_frame = ttk.LabelFrame(self.window, text="Knowledge Bases")
    kb_frame.pack(padx=10, pady=5, fill=tk.X)

    self.kb_vars = {}
    self.refresh_kb_list(kb_frame)

    # Environment Variables
    env_frame = ttk.LabelFrame(self.window, text="Environment Variables")
    env_frame.pack(padx=10, pady=5, fill=tk.X)

    self.env_vars = {}
    self.refresh_env_vars(env_frame)

    ttk.Button(env_frame, text="Add Environment Variable", command=self.add_env_var).pack(pady=5)

    # Buttons
    button_frame = ttk.Frame(self.window)
    button_frame.pack(pady=20)
    ttk.Button(button_frame, text="Save", command=self.save_settings).pack(side=tk.LEFT, padx=10)
    ttk.Button(button_frame, text="Cancel", command=self.window.destroy).pack(side=tk.LEFT)
    ttk.Button(button_frame, text="Reset Chat", command=self.chat_ui.reset_chat).pack(side=tk.LEFT, padx=10)
    ttk.Button(button_frame, text="Add to Knowledge Base", command=self.add_to_knowledge_base).pack(side=tk.LEFT)

  def refresh_kb_list(self, kb_frame):
    for widget in kb_frame.winfo_children():
      widget.destroy()

    kb_list = [d for d in os.listdir(CHROMA_PATH) if os.path.isdir(os.path.join(CHROMA_PATH, d))]

    for i, kb in enumerate(kb_list):
      self.kb_vars[kb] = tk.BooleanVar(value=kb in self.chat_ui.selected_kbs)
      cb = ttk.Checkbutton(kb_frame, text=kb, variable=self.kb_vars[kb])
      cb.pack(anchor=tk.W, padx=5, pady=2)

  def refresh_env_vars(self, env_frame):
    for widget in env_frame.winfo_children():
      widget.destroy()

    for key, value in os.environ.items():
      if key.startswith("CUSTOM_"):
        self.env_vars[key] = tk.StringVar(value=value)
        row_frame = ttk.Frame(env_frame)
        row_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(row_frame, text=key).pack(side=tk.LEFT)
        ttk.Entry(row_frame, textvariable=self.env_vars[key], show="*").pack(side=tk.RIGHT, expand=True, fill=tk.X)

  def add_env_var(self):
    key = simpledialog.askstring("Add Environment Variable", "Enter variable name (will be prefixed with CUSTOM_):")
    if key:
      key = f"CUSTOM_{key}"
      value = simpledialog.askstring("Add Environment Variable", f"Enter value for {key}:")
      if value:
        os.environ[key] = value
        self.env_vars[key] = tk.StringVar(value=value)
        env_frame = self.window.children['!labelframe3']
        row_frame = ttk.Frame(env_frame)
        row_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(row_frame, text=key).pack(side=tk.LEFT)
        ttk.Entry(row_frame, textvariable=self.env_vars[key], show="*").pack(side=tk.RIGHT, expand=True, fill=tk.X)

  def load_current_settings(self):
    self.use_knowledge_var.set(self.chat_ui.use_knowledge)
    self.wake_word_entry.insert(0, self.chat_ui.wake_word)
    
    self.supports_vision_var.set(INTERPRETER_SETTINGS["supports_vision"])
    self.supports_functions_var.set(INTERPRETER_SETTINGS["supports_functions"])
    self.auto_run_var.set(INTERPRETER_SETTINGS["auto_run"])
    self.loop_var.set(INTERPRETER_SETTINGS["loop"])
    self.temperature_var.set(INTERPRETER_SETTINGS["temperature"])
    self.max_tokens_var.set(INTERPRETER_SETTINGS["max_tokens"])
    self.context_window_var.set(INTERPRETER_SETTINGS["context_window"])

  def save_settings(self):
    new_use_knowledge = self.use_knowledge_var.get()
    new_wake_word = self.wake_word_entry.get().strip()
    new_selected_kbs = [kb for kb, var in self.kb_vars.items() if var.get()]

    # Update ChatUI instance
    self.chat_ui.use_knowledge = new_use_knowledge
    self.chat_ui.selected_kbs = new_selected_kbs
    self.chat_ui.wake_word = new_wake_word

    # Update config file
    config_path = os.path.join(os.path.dirname(__file__), "..", "Settings", "config.py")
    with open(config_path, "r") as f:
      config_content = f.read()

    config_content = config_content.replace(f"USE_KNOWLEDGE = {USE_KNOWLEDGE}", f"USE_KNOWLEDGE = {new_use_knowledge}")
    config_content = config_content.replace(f"DEFAULT_SELECTED_KBS = {json.dumps(DEFAULT_SELECTED_KBS)}", f"DEFAULT_SELECTED_KBS = {json.dumps(new_selected_kbs)}")
    config_content = config_content.replace(f"WAKE_WORD = '{WAKE_WORD}'", f"WAKE_WORD = '{new_wake_word}'")

    # Update INTERPRETER_SETTINGS
    new_interpreter_settings = {
      "supports_vision": self.supports_vision_var.get(),
      "supports_functions": self.supports_functions_var.get(),
      "auto_run": self.auto_run_var.get(),
      "loop": self.loop_var.get(),
      "temperature": self.temperature_var.get(),
      "max_tokens": self.max_tokens_var.get(),
      "context_window": self.context_window_var.get(),
    }
    config_content = config_content.replace(f"INTERPRETER_SETTINGS = {json.dumps(INTERPRETER_SETTINGS, indent=4)}", f"INTERPRETER_SETTINGS = {json.dumps(new_interpreter_settings, indent=4)}")

    with open(config_path, "w") as f:
      f.write(config_content)

    # Save environment variables
    for key, var in self.env_vars.items():
      os.environ[key] = var.get()

    # Update system message with environment variable names
    custom_env_vars = [key for key in os.environ if key.startswith("CUSTOM_")]
    env_var_message = "The following custom environment variables are available: " + ", ".join(custom_env_vars)
    interpreter.system_message += f"\n\n{env_var_message}"

    messagebox.showinfo("Settings Saved", "Settings have been updated successfully.")
    self.window.destroy()

  def add_to_knowledge_base(self):
    kb_list = [d for d in os.listdir(KB_PATH) if os.path.isdir(os.path.join(KB_PATH, d))]
    
    kb_window = tk.Toplevel(self.window)
    kb_window.title("Add to Knowledge Base")
    kb_window.geometry("300x150")
    
    def select_existing_kb():
      kb_name = kb_var.get()
      kb_window.destroy()
      self.add_content_to_kb(kb_name)
    
    def create_new_kb():
      new_kb_name = simpledialog.askstring("New Knowledge Base", "Enter name for new knowledge base:")
      if new_kb_name:
        new_kb_path = os.path.join(KB_PATH, new_kb_name)
        os.makedirs(os.path.join(new_kb_path, "docs"), exist_ok=True)
        with open(os.path.join(new_kb_path, "urls.txt"), 'w') as f:
          pass  # Create empty urls.txt file
        kb_window.destroy()
        self.add_content_to_kb(new_kb_name)
    
    kb_var = tk.StringVar()
    kb_dropdown = ttk.Combobox(kb_window, textvariable=kb_var, values=kb_list, state="readonly")
    kb_dropdown.set("Select knowledge base")
    kb_dropdown.pack(pady=10)
    
    select_button = tk.Button(kb_window, text="Select Existing KB", command=select_existing_kb)
    select_button.pack(pady=5)
    
    create_button = tk.Button(kb_window, text="Create New KB", command=create_new_kb)
    create_button.pack(pady=5)
    
    kb_window.transient(self.window)
    kb_window.grab_set()
    self.window.wait_window(kb_window)

  def add_content_to_kb(self, kb_name):
    content_window = tk.Toplevel(self.window)
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
      self.knowledge_manager.build_vector_database(kb_name)
      messagebox.showinfo("Success", f"Knowledge base '{kb_name}' updated successfully!")
      self.refresh_kb_list(self.window.children['!labelframe2'])
    
    file_button = tk.Button(content_window, text="Add File", command=add_file)
    file_button.pack(pady=10)
    
    url_button = tk.Button(content_window, text="Add URL", command=add_url)
    url_button.pack(pady=10)
    
    content_window.transient(self.window)
    content_window.grab_set()
    self.window.wait_window(content_window)