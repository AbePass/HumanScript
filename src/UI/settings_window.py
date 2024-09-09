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
    self.selected_files = []
    self.selected_urls = []
    self.selected_kb = ctk.StringVar()
    self.create_widgets()
    self.load_current_settings()

  def create_widgets(self):
    # Create a scrollable frame for settings
    self.scrollable_frame = ctk.CTkScrollableFrame(self.parent, fg_color=get_color("BG_PRIMARY"))
    self.scrollable_frame.pack(padx=10, pady=10, fill="both", expand=True)

    # Interpreter Settings
    self.create_collapsible_section("Interpreter Settings", self.create_interpreter_settings)

    # Wake Word
    self.create_collapsible_section("Wake Word", self.create_wake_word_settings)

    # Environment Variables
    self.create_collapsible_section("Environment Variables", self.create_env_var_settings)

    # Knowledge Base Management
    self.create_collapsible_section("Knowledge Base Management", self.create_kb_management_settings)

    # Buttons
    button_frame = ctk.CTkFrame(self.scrollable_frame, fg_color=get_color("BG_PRIMARY"))
    button_frame.pack(pady=20, anchor="w")
    ctk.CTkButton(button_frame, text="Save", command=self.save_settings, fg_color=get_color("BG_INPUT"), text_color=get_color("TEXT_PRIMARY"), hover_color=get_color("BG_SECONDARY")).pack(side=ctk.LEFT, padx=10)
    ctk.CTkButton(button_frame, text="Cancel", command=self.cancel, fg_color=get_color("BG_INPUT"), text_color=get_color("TEXT_PRIMARY"), hover_color=get_color("BG_SECONDARY")).pack(side=ctk.LEFT)
    ctk.CTkButton(button_frame, text="Reset Chat", command=self.reset_interpreter, fg_color=get_color("BG_INPUT"), text_color=get_color("TEXT_PRIMARY"), hover_color=get_color("BG_SECONDARY")).pack(side=ctk.LEFT, padx=10)

  def create_collapsible_section(self, title, create_content_func):
    section_frame = ctk.CTkFrame(self.scrollable_frame, fg_color=get_color("BG_TERTIARY"))
    section_frame.pack(padx=10, pady=5, fill="x", anchor="w")

    section_button = ctk.CTkButton(section_frame, text=title, command=lambda: self.toggle_section(section_content), fg_color=get_color("BG_INPUT"), text_color=get_color("TEXT_PRIMARY"), hover_color=get_color("BG_SECONDARY"), border_width=2, border_color=get_color("TEXT_PRIMARY"), font=("Helvetica", 16))
    section_button.pack(fill="x")

    section_content = ctk.CTkFrame(section_frame, fg_color=get_color("BG_PRIMARY"))
    section_content.pack(fill="x", expand=True, anchor="w")
    create_content_func(section_content)
    section_content.pack_forget()

  def toggle_section(self, section_content):
    if section_content.winfo_ismapped():
      section_content.pack_forget()
    else:
      section_content.pack(fill="x", expand=True, anchor="w")

  def create_interpreter_settings(self, parent):
    self.supports_vision_var = ctk.BooleanVar()
    ctk.CTkCheckBox(parent, text="Supports Vision", variable=self.supports_vision_var, text_color=get_color("TEXT_PRIMARY")).pack(pady=2, anchor="w")

    self.supports_functions_var = ctk.BooleanVar()
    ctk.CTkCheckBox(parent, text="Supports Functions", variable=self.supports_functions_var, text_color=get_color("TEXT_PRIMARY")).pack(pady=2, anchor="w")

    self.auto_run_var = ctk.BooleanVar()
    ctk.CTkCheckBox(parent, text="Auto Run", variable=self.auto_run_var, text_color=get_color("TEXT_PRIMARY")).pack(pady=2, anchor="w")

    self.loop_var = ctk.BooleanVar()
    ctk.CTkCheckBox(parent, text="Loop", variable=self.loop_var, text_color=get_color("TEXT_PRIMARY")).pack(pady=2, anchor="w")

    ctk.CTkLabel(parent, text="Temperature:", text_color=get_color("TEXT_PRIMARY")).pack(pady=2, anchor="w")
    self.temperature_var = ctk.DoubleVar()
    ctk.CTkEntry(parent, textvariable=self.temperature_var, fg_color=get_color("BG_INPUT"), text_color=get_color("TEXT_PRIMARY")).pack(pady=2, anchor="w")

    ctk.CTkLabel(parent, text="Max Tokens:", text_color=get_color("TEXT_PRIMARY")).pack(pady=2, anchor="w")
    self.max_tokens_var = ctk.IntVar()
    ctk.CTkEntry(parent, textvariable=self.max_tokens_var, fg_color=get_color("BG_INPUT"), text_color=get_color("TEXT_PRIMARY")).pack(pady=2, anchor="w")

    ctk.CTkLabel(parent, text="Context Window:", text_color=get_color("TEXT_PRIMARY")).pack(pady=2, anchor="w")
    self.context_window_var = ctk.IntVar()
    ctk.CTkEntry(parent, textvariable=self.context_window_var, fg_color=get_color("BG_INPUT"), text_color=get_color("TEXT_PRIMARY")).pack(pady=2, anchor="w")

  def create_wake_word_settings(self, parent):
    ctk.CTkLabel(parent, text="Wake Word:", text_color=get_color("TEXT_PRIMARY")).pack(pady=5, anchor="w")
    self.wake_word_entry = ctk.CTkEntry(parent, width=50, fg_color=get_color("BG_INPUT"), text_color=get_color("TEXT_PRIMARY"))
    self.wake_word_entry.pack(pady=5, anchor="w")

  def create_env_var_settings(self, parent):
    self.env_vars = {}
    self.refresh_env_vars(parent)

    ctk.CTkButton(parent, text="Add Environment Variable", command=self.add_env_var, fg_color=get_color("BG_INPUT"), text_color=get_color("TEXT_PRIMARY"), hover_color=get_color("BG_SECONDARY")).pack(pady=5, anchor="w")

  def refresh_env_vars(self, env_frame):
    for widget in env_frame.winfo_children():
      widget.destroy()

    for key, value in os.environ.items():
      if key.startswith("CUSTOM_"):
        self.env_vars[key] = ctk.StringVar(value=value)
        row_frame = ctk.CTkFrame(env_frame, fg_color=get_color("BG_TERTIARY"))
        row_frame.pack(fill=ctk.X, padx=5, pady=2, anchor="w")
        ctk.CTkLabel(row_frame, text=key, text_color=get_color("TEXT_PRIMARY")).pack(side=ctk.LEFT)
        ctk.CTkEntry(row_frame, textvariable=self.env_vars[key], show="*", fg_color=get_color("BG_INPUT"), text_color=get_color("TEXT_PRIMARY")).pack(side=ctk.RIGHT, expand=True, fill=ctk.X)

  def add_env_var(self):
    key = simpledialog.askstring("Add Environment Variable", "Enter variable name (will be prefixed with CUSTOM_):")
    if key:
      key = f"CUSTOM_{key.upper().replace(' ', '_')}"
      value = simpledialog.askstring("Add Environment Variable", f"Enter value for {key}:")
      if value:
        os.environ[key] = value
        self.env_vars[key] = ctk.StringVar(value=value)
        env_frame = self.parent.children['!ctkframe3']
        row_frame = ctk.CTkFrame(env_frame, fg_color=get_color("BG_TERTIARY"))
        row_frame.pack(fill=ctk.X, padx=5, pady=2, anchor="w")
        ctk.CTkLabel(row_frame, text=key, text_color=get_color("TEXT_PRIMARY")).pack(side=ctk.LEFT)
        ctk.CTkEntry(row_frame, textvariable=self.env_vars[key], show="*", fg_color=get_color("BG_INPUT"), text_color=get_color("TEXT_PRIMARY")).pack(side=ctk.RIGHT, expand=True, fill=ctk.X)

  def create_kb_management_settings(self, parent):
    ctk.CTkLabel(parent, text="Select files and URLs to be added to the knowledge base:", text_color=get_color("TEXT_PRIMARY")).pack(pady=5, anchor="w")
    
    button_frame = ctk.CTkFrame(parent, fg_color=get_color("BG_PRIMARY"))
    button_frame.pack(pady=5, anchor="w", fill="x")
    
    ctk.CTkButton(button_frame, text="Add File", command=self.add_file, fg_color=get_color("BG_INPUT"), text_color=get_color("TEXT_PRIMARY"), hover_color=get_color("BG_SECONDARY")).pack(side="left", padx=(0, 5))
    ctk.CTkButton(button_frame, text="Add URL", command=self.add_url, fg_color=get_color("BG_INPUT"), text_color=get_color("TEXT_PRIMARY"), hover_color=get_color("BG_SECONDARY")).pack(side="left")

    self.kb_dropdown = ctk.CTkComboBox(parent, values=self.chat_ui.knowledge_manager.get_knowledge_bases() + ["New Knowledge Base"], fg_color=get_color("BG_INPUT"), text_color=get_color("TEXT_PRIMARY"))
    self.kb_dropdown.pack(pady=10, anchor="w")

    action_frame = ctk.CTkFrame(parent, fg_color=get_color("BG_PRIMARY"))
    action_frame.pack(pady=5, anchor="w", fill="x")

    ctk.CTkButton(action_frame, text="Add to Knowledge Base", command=self.submit_kb, fg_color=get_color("BG_INPUT"), text_color=get_color("TEXT_PRIMARY"), hover_color=get_color("BG_SECONDARY")).pack(side="left", padx=(0, 5))
    ctk.CTkButton(action_frame, text="Clear Queue", command=self.clear_queue, fg_color=get_color("BG_INPUT"), text_color=get_color("TEXT_PRIMARY"), hover_color=get_color("BG_SECONDARY")).pack(side="left")

    ctk.CTkLabel(parent, text="Queue:", text_color=get_color("TEXT_PRIMARY")).pack(pady=(10, 5), anchor="w")
    self.queue_display = ctk.CTkTextbox(parent, height=100, fg_color=get_color("BG_INPUT"), text_color=get_color("TEXT_PRIMARY"))
    self.queue_display.pack(pady=5, fill="x", expand=True)

    ctk.CTkButton(parent, text="Refresh Selected Knowledge Base", command=self.refresh_selected_kb, fg_color=get_color("BG_INPUT"), text_color=get_color("TEXT_PRIMARY"), hover_color=get_color("BG_SECONDARY")).pack(pady=(10, 5), anchor="w")

  def clear_queue(self):
    self.selected_files.clear()
    self.selected_urls.clear()
    self.update_queue_display()

  def update_queue_display(self):
    self.queue_display.delete("1.0", ctk.END)
    for file in self.selected_files:
      self.queue_display.insert(ctk.END, f"File: {os.path.basename(file)}\n")
    for url in self.selected_urls:
      self.queue_display.insert(ctk.END, f"URL: {url}\n")

  def add_file(self):
    file_paths = filedialog.askopenfilenames()
    if file_paths:
      self.selected_files.extend(file_paths)
      self.update_queue_display()
      messagebox.showinfo("Files Added", f"Added {len(file_paths)} files.")

  def add_url(self):
    url = simpledialog.askstring("Add URL", "Enter URL:")
    if url:
      self.selected_urls.append(url)
      self.update_queue_display()
      messagebox.showinfo("URL Added", f"Added URL: {url}")

  def submit_kb(self):
    kb_name = self.kb_dropdown.get()
    if kb_name == "New Knowledge Base":
      kb_name = simpledialog.askstring("New Knowledge Base", "Enter name for the new knowledge base:")
      if not kb_name:
        messagebox.showerror("Error", "Please enter a name for the new knowledge base.")
        return

    kb_path = os.path.join(KB_PATH, kb_name)
    os.makedirs(kb_path, exist_ok=True)

    docs_path = os.path.join(kb_path, "docs")
    os.makedirs(docs_path, exist_ok=True)

    urls_path = os.path.join(kb_path, "urls.txt")

    for file_path in self.selected_files:
      shutil.copy(file_path, docs_path)

    with open(urls_path, "a") as f:
      for url in self.selected_urls:
        f.write(url + "\n")

    self.selected_files.clear()
    self.selected_urls.clear()
    self.update_queue_display()
    messagebox.showinfo("Knowledge Base Updated", f"Files and URLs have been added to {kb_name}.")

  def refresh_selected_kb(self):
    selected_kb = self.kb_dropdown.get()
    if selected_kb == "New Knowledge Base":
      messagebox.showwarning("Invalid Selection", "Please select an existing knowledge base to refresh.")
      return

    try:
      self.chat_ui.knowledge_manager.build_vector_database(selected_kb)
      self.chat_ui.refresh_knowledge_bases()  # Update the UI
      messagebox.showinfo("Knowledge Base Refreshed", f"The knowledge base '{selected_kb}' has been refreshed.")
    except Exception as e:
      messagebox.showerror("Error", f"An error occurred while refreshing the knowledge base: {str(e)}")

  def load_current_settings(self):
    self.wake_word_entry.insert(0, self.chat_ui.wake_word)
    
    self.supports_vision_var.set(self.chat_ui.interpreter_settings["supports_vision"])
    self.supports_functions_var.set(self.chat_ui.interpreter_settings["supports_functions"])
    self.auto_run_var.set(self.chat_ui.interpreter_settings["auto_run"])
    self.loop_var.set(self.chat_ui.interpreter_settings["loop"])
    self.temperature_var.set(self.chat_ui.interpreter_settings["temperature"])
    self.max_tokens_var.set(self.chat_ui.interpreter_settings["max_tokens"])
    self.context_window_var.set(self.chat_ui.interpreter_settings["context_window"])
    
    # Load environment variables
    for key, value in self.chat_ui.env_vars.items():
        if key in self.env_vars:
            self.env_vars[key].set(value)

  def save_settings(self):
    # Update ChatUI attributes
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
    messagebox.showinfo("Settings Saved", "Your settings have been successfully updated.")
    # Update the sidebar checkboxes
    self.chat_ui.refresh_knowledge_bases()
    # Return to chat window
    self.return_to_chat()

  def cancel(self):
    # Return to chat window
    self.return_to_chat()

  def return_to_chat(self):
    # Clear the settings UI and recreate the chat window
    for widget in self.parent.winfo_children():
      widget.destroy()
    self.chat_ui.create_chat_window(self.parent)
    self.chat_ui.create_input_area(self.parent)

  def reset_interpreter(self):
    interpreter.reset()
    messagebox.showinfo("Interpreter Reset", "The interpreter has been reset.")
    self.return_to_chat()