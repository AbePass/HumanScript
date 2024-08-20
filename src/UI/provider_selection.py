import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

class ProviderSelectionUI:
  def __init__(self, root):
    self.root = root
    self.provider = None
    self.config = {}
    self.provider_var = tk.StringVar()
    self.credential_entries = {}

  def create_provider_selection_ui(self):
    self.window = tk.Toplevel(self.root)
    self.window.title("Select AI Provider")
    self.window.geometry("300x100")

    providers = ["openai", "azure", "anthropic"]
    
    ttk.Label(self.window, text="Select Provider:").pack(pady=10)
    provider_dropdown = ttk.Combobox(self.window, textvariable=self.provider_var, values=providers)
    provider_dropdown.pack(pady=10)
    provider_dropdown.bind("<<ComboboxSelected>>", self.show_credential_inputs)

  def show_credential_inputs(self, event):
    self.provider = self.provider_var.get()
    self.window.geometry("300x350")  # Resize window for credential inputs and new button
    
    # Clear previous credential inputs
    for widget in self.window.winfo_children():
      if isinstance(widget, ttk.Entry) or isinstance(widget, ttk.Label) or isinstance(widget, ttk.Button):
        widget.destroy()

    ttk.Label(self.window, text=f"Enter credentials for {self.provider}:").pack(pady=10)

    if self.provider == "openai":
      self.create_credential_input("OPENAI_API_KEY")
      self.create_credential_input("OPENAI_MODEL")
    elif self.provider == "azure":
      self.create_credential_input("AZURE_API_KEY")
      self.create_credential_input("AZURE_API_BASE")
      self.create_credential_input("AZURE_API_VERSION")
      self.create_credential_input("AZURE_MODEL")
    elif self.provider == "anthropic":
      self.create_credential_input("ANTHROPIC_API_KEY")
      self.create_credential_input("ANTHROPIC_MODEL")

    ttk.Button(self.window, text="Load from file", command=self.load_from_file).pack(pady=10)
    ttk.Button(self.window, text="Done", command=self.on_done).pack(pady=10)

  def create_credential_input(self, key):
    ttk.Label(self.window, text=key).pack()
    entry = ttk.Entry(self.window)
    entry.pack()
    self.credential_entries[key] = entry

  def load_from_file(self):
    try:
      with open('src/Settings/provider_config.json', 'r') as f:
        saved_config = json.load(f)
      
      for key, entry in self.credential_entries.items():
        if key in saved_config:
          entry.delete(0, tk.END)
          entry.insert(0, saved_config[key])
      
      messagebox.showinfo("Success", "Credentials loaded from file")
    except FileNotFoundError:
      messagebox.showerror("Error", "provider_config.json not found")
    except json.JSONDecodeError:
      messagebox.showerror("Error", "Invalid JSON in provider_config.json")

  def on_done(self):
    for key, entry in self.credential_entries.items():
      self.config[key] = entry.get()
    
    self.window.destroy()

  def get_config(self):
    return self.config