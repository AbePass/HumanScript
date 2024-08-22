import customtkinter as ctk
from tkinter import messagebox, simpledialog, filedialog
from Settings.config import INTERPRETER_SETTINGS, CHROMA_PATH, KB_PATH
from Core.knowledge_manager import KnowledgeManager
import json
import os
import shutil
from interpreter import interpreter
import importlib
from Settings.color_settings import *

class SettingsWindow:
  def __init__(self, parent, chat_ui):
    self.parent = parent
    self.chat_ui = chat_ui
    self.window = ctk.CTkToplevel(parent)
    self.window.title("Settings")
    self.window.geometry("600x800")
    self.window.resizable(True, True)
    self.window.configure(fg_color=get_color("BG_PRIMARY"))

    self.knowledge_manager = KnowledgeManager(self.window)

    self.create_widgets()
    self.load_current_settings()

  def create_widgets(self):
    # Interpreter Settings
    interpreter_frame = ctk.CTkFrame(self.window, fg_color=get_color("BG_TERTIARY"))
    interpreter_frame.pack(padx=10, pady=5, fill=ctk.X)

    self.supports_vision_var = ctk.BooleanVar()
    ctk.CTkCheckBox(interpreter_frame, text="Supports Vision", variable=self.supports_vision_var, text_color=get_color("TEXT_PRIMARY")).pack(pady=2)

    self.supports_functions_var = ctk.BooleanVar()
    ctk.CTkCheckBox(interpreter_frame, text="Supports Functions", variable=self.supports_functions_var, text_color=get_color("TEXT_PRIMARY")).pack(pady=2)

    self.auto_run_var = ctk.BooleanVar()
    ctk.CTkCheckBox(interpreter_frame, text="Auto Run", variable=self.auto_run_var, text_color=get_color("TEXT_PRIMARY")).pack(pady=2)

    self.loop_var = ctk.BooleanVar()
    ctk.CTkCheckBox(interpreter_frame, text="Loop", variable=self.loop_var, text_color=get_color("TEXT_PRIMARY")).pack(pady=2)

    ctk.CTkLabel(interpreter_frame, text="Temperature:", text_color=get_color("TEXT_PRIMARY")).pack(pady=2)
    self.temperature_var = ctk.DoubleVar()
    ctk.CTkEntry(interpreter_frame, textvariable=self.temperature_var, fg_color=get_color("BG_INPUT"), text_color=get_color("TEXT_PRIMARY")).pack(pady=2)

    ctk.CTkLabel(interpreter_frame, text="Max Tokens:", text_color=get_color("TEXT_PRIMARY")).pack(pady=2)
    self.max_tokens_var = ctk.IntVar()
    ctk.CTkEntry(interpreter_frame, textvariable=self.max_tokens_var, fg_color=get_color("BG_INPUT"), text_color=get_color("TEXT_PRIMARY")).pack(pady=2)

    ctk.CTkLabel(interpreter_frame, text="Context Window:", text_color=get_color("TEXT_PRIMARY")).pack(pady=2)
    self.context_window_var = ctk.IntVar()
    ctk.CTkEntry(interpreter_frame, textvariable=self.context_window_var, fg_color=get_color("BG_INPUT"), text_color=get_color("TEXT_PRIMARY")).pack(pady=2)

    # Wake Word
    ctk.CTkLabel(self.window, text="Wake Word:", text_color=get_color("TEXT_PRIMARY")).pack(pady=5)
    self.wake_word_entry = ctk.CTkEntry(self.window, width=50, fg_color=get_color("BG_INPUT"), text_color=get_color("TEXT_PRIMARY"))
    self.wake_word_entry.pack(pady=5)

    # Knowledge Bases
    kb_frame = ctk.CTkFrame(self.window, fg_color=get_color("BG_TERTIARY"))
    kb_frame.pack(padx=10, pady=5, fill=ctk.X)

    self.kb_vars = {}
    self.refresh_kb_list(kb_frame)

    # Environment Variables
    env_frame = ctk.CTkFrame(self.window, fg_color=get_color("BG_TERTIARY"))
    env_frame.pack(padx=10, pady=5, fill=ctk.X)

    self.env_vars = {}
    self.refresh_env_vars(env_frame)

    ctk.CTkButton(env_frame, text="Add Environment Variable", command=self.add_env_var, fg_color=BRAND_PRIMARY, text_color=get_color("TEXT_PRIMARY"), hover_color=BRAND_ACCENT).pack(pady=5)

    # Buttons
    button_frame = ctk.CTkFrame(self.window, fg_color=get_color("BG_PRIMARY"))
    button_frame.pack(pady=20)
    ctk.CTkButton(button_frame, text="Save", command=self.save_settings, fg_color=BRAND_PRIMARY, text_color=get_color("TEXT_PRIMARY"), hover_color=BRAND_ACCENT).pack(side=ctk.LEFT, padx=10)
    ctk.CTkButton(button_frame, text="Cancel", command=self.window.destroy, fg_color=BRAND_PRIMARY, text_color=get_color("TEXT_PRIMARY"), hover_color=BRAND_ACCENT).pack(side=ctk.LEFT)
    ctk.CTkButton(button_frame, text="Reset Chat", command=self.chat_ui.reset_chat, fg_color=BRAND_PRIMARY, text_color=get_color("TEXT_PRIMARY"), hover_color=BRAND_ACCENT).pack(side=ctk.LEFT, padx=10)
    ctk.CTkButton(button_frame, text="Add to Knowledge Base", command=self.add_to_knowledge_base, fg_color=BRAND_PRIMARY, text_color=get_color("TEXT_PRIMARY"), hover_color=BRAND_ACCENT).pack(side=ctk.LEFT)
    
    # Add a new button for rebuilding knowledge bases
    rebuild_kb_button = ctk.CTkButton(
        button_frame,
        text="Rebuild Knowledge Bases",
        command=self.rebuild_knowledge_bases,
        fg_color=BRAND_PRIMARY,
        text_color=get_color("TEXT_PRIMARY"),
        hover_color=BRAND_ACCENT
    )
    rebuild_kb_button.pack(side=ctk.LEFT, padx=10)

  def refresh_kb_list(self, kb_frame):
    for widget in kb_frame.winfo_children():
      widget.destroy()

    kb_list = [d for d in os.listdir(CHROMA_PATH) if os.path.isdir(os.path.join(CHROMA_PATH, d))]

    for i, kb in enumerate(kb_list):
      self.kb_vars[kb] = ctk.BooleanVar(value=kb in self.chat_ui.selected_kbs)
      cb = ctk.CTkCheckBox(kb_frame, text=kb, variable=self.kb_vars[kb], text_color=get_color("TEXT_PRIMARY"))
      cb.pack(anchor=ctk.W, padx=5, pady=2)

  def refresh_env_vars(self, env_frame):
    for widget in env_frame.winfo_children():
      widget.destroy()

    for key, value in os.environ.items():
      if key.startswith("CUSTOM_"):
        self.env_vars[key] = ctk.StringVar(value=value)
        row_frame = ctk.CTkFrame(env_frame, fg_color=get_color("BG_TERTIARY"))
        row_frame.pack(fill=ctk.X, padx=5, pady=2)
        ctk.CTkLabel(row_frame, text=key, text_color=get_color("TEXT_PRIMARY")).pack(side=ctk.LEFT)
        ctk.CTkEntry(row_frame, textvariable=self.env_vars[key], show="*", fg_color=get_color("BG_INPUT"), text_color=get_color("TEXT_PRIMARY")).pack(side=ctk.RIGHT, expand=True, fill=ctk.X)

  def add_env_var(self):
    key = simpledialog.askstring("Add Environment Variable", "Enter variable name (will be prefixed with CUSTOM_):")
    if key:
      key = f"CUSTOM_{key}"
      value = simpledialog.askstring("Add Environment Variable", f"Enter value for {key}:")
      if value:
        os.environ[key] = value
        self.env_vars[key] = ctk.StringVar(value=value)
        env_frame = self.window.children['!ctkframe3']
        row_frame = ctk.CTkFrame(env_frame, fg_color=get_color("BG_TERTIARY"))
        row_frame.pack(fill=ctk.X, padx=5, pady=2)
        ctk.CTkLabel(row_frame, text=key, text_color=get_color("TEXT_PRIMARY")).pack(side=ctk.LEFT)
        ctk.CTkEntry(row_frame, textvariable=self.env_vars[key], show="*", fg_color=get_color("BG_INPUT"), text_color=get_color("TEXT_PRIMARY")).pack(side=ctk.RIGHT, expand=True, fill=ctk.X)

  def load_current_settings(self):
    self.wake_word_entry.insert(0, self.chat_ui.wake_word)
    
    self.supports_vision_var.set(self.chat_ui.interpreter_settings["supports_vision"])
    self.supports_functions_var.set(self.chat_ui.interpreter_settings["supports_functions"])
    self.auto_run_var.set(self.chat_ui.interpreter_settings["auto_run"])
    self.loop_var.set(self.chat_ui.interpreter_settings["loop"])
    self.temperature_var.set(self.chat_ui.interpreter_settings["temperature"])
    self.max_tokens_var.set(self.chat_ui.interpreter_settings["max_tokens"])
    self.context_window_var.set(self.chat_ui.interpreter_settings["context_window"])
    
    # Load selected knowledge bases
    for kb in self.kb_vars:
        self.kb_vars[kb].set(kb in self.chat_ui.selected_kbs)
    
    # Load environment variables
    for key, value in self.chat_ui.env_vars.items():
        if key in self.env_vars:
            self.env_vars[key].set(value)

  def save_settings(self):
    # Update ChatUI attributes
    self.chat_ui.selected_kbs = [kb for kb, var in self.kb_vars.items() if var.get()]
    self.chat_ui.wake_word = self.wake_word_entry.get().strip()

    # Update interpreter settings through ChatUI
    self.chat_ui.update_interpreter_settings({
      "supports_vision": self.supports_vision_var.get(),
      "supports_functions": self.supports_functions_var.get(),
      "auto_run": self.auto_run_var.get(),
      "loop": self.loop_var.get(),
      "temperature": self.temperature_var.get(),
      "max_tokens": self.max_tokens_var.get(),
      "context_window": self.context_window_var.get()
    })

    # Update environment variables
    self.chat_ui.update_env_vars({key: var.get() for key, var in self.env_vars.items()})

    # Notify the user
    self.window.destroy()
    messagebox.showinfo("Settings Saved", "Your settings have been successfully updated.")

  def add_to_knowledge_base(self):
    kb_list = [d for d in os.listdir(KB_PATH) if os.path.isdir(os.path.join(KB_PATH, d))]
    
    kb_window = ctk.CTkToplevel(self.window)
    kb_window.title("Add to Knowledge Base")
    kb_window.geometry("300x150")
    kb_window.configure(fg_color=get_color("BG_PRIMARY"))
    
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
    
    kb_var = ctk.StringVar()
    kb_dropdown = ctk.CTkComboBox(kb_window, textvariable=kb_var, values=kb_list, state="readonly", fg_color=get_color("BG_INPUT"), text_color=get_color("TEXT_PRIMARY"))
    kb_dropdown.set("Select knowledge base")
    kb_dropdown.pack(pady=10)
    
    select_button = ctk.CTkButton(kb_window, text="Select Existing KB", command=select_existing_kb, fg_color=BRAND_PRIMARY, text_color=get_color("TEXT_PRIMARY"), hover_color=BRAND_ACCENT)
    select_button.pack(pady=5)
    
    create_button = ctk.CTkButton(kb_window, text="Create New KB", command=create_new_kb, fg_color=BRAND_PRIMARY, text_color=get_color("TEXT_PRIMARY"), hover_color=BRAND_ACCENT)
    create_button.pack(pady=5)
    
    kb_window.transient(self.window)
    kb_window.grab_set()
    self.window.wait_window(kb_window)

  def add_content_to_kb(self, kb_name):
    content_window = ctk.CTkToplevel(self.window)
    content_window.title(f"Add to {kb_name}")
    content_window.geometry("300x150")
    content_window.configure(fg_color=get_color("BG_PRIMARY"))
    
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
      self.refresh_kb_list(self.window.children['!ctkframe2'])
    
    file_button = ctk.CTkButton(content_window, text="Add File", command=add_file, fg_color=BRAND_PRIMARY, text_color=get_color("TEXT_PRIMARY"), hover_color=BRAND_ACCENT)
    file_button.pack(pady=10)
    
    url_button = ctk.CTkButton(content_window, text="Add URL", command=add_url, fg_color=BRAND_PRIMARY, text_color=get_color("TEXT_PRIMARY"), hover_color=BRAND_ACCENT)
    url_button.pack(pady=10)
    
    content_window.transient(self.window)
    content_window.grab_set()
    self.window.wait_window(content_window)

  def rebuild_knowledge_bases(self):
    # Disable the button while rebuilding
    rebuild_button = self.window.nametowidget("!ctkframe5.!ctkbutton4")
    rebuild_button.configure(state="disabled", text="Rebuilding...")
    
    # Schedule the rebuilding process
    self.window.after(100, self.perform_rebuild, rebuild_button)

  def perform_rebuild(self, rebuild_button):
    try:
        # Rebuild all knowledge bases
        self.knowledge_manager.build_vector_database()
        messagebox.showinfo("Success", "Knowledge bases have been rebuilt successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while rebuilding knowledge bases: {str(e)}")
    finally:
        # Re-enable the button
        rebuild_button.configure(state="normal", text="Rebuild Knowledge Bases")
        
        # Refresh the KB list to reflect any changes
        self.refresh_kb_list(self.window.children['!ctkframe2'])