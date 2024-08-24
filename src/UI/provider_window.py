import customtkinter as ctk
from tkinter import messagebox
import json
import os

class ProviderSelectionUI:
  def __init__(self, root):
    self.root = root
    self.provider = None
    self.config = {}
    self.provider_var = ctk.StringVar()
    self.provider_var.trace_add("write", self.on_provider_changed)  # Add trace
    self.credential_entries = {}

  def create_provider_selection_ui(self):
    self.window = ctk.CTkToplevel(self.root)
    self.window.title("Select AI Provider")
    self.window.geometry("300x200")  # Increased height for debug label
    self.window.configure(fg_color=["#1E1E1E", "#121212"])

    providers = ["openai", "azure", "anthropic"]
    
    ctk.CTkLabel(self.window, text="Select Provider:", text_color=["#F4F4F4", "#FFFFFF"]).pack(pady=10)
    provider_dropdown = ctk.CTkComboBox(self.window, variable=self.provider_var, values=providers, fg_color=["#2A2A2A", "#2A2A2A"], text_color=["#F4F4F4", "#FFFFFF"], button_color="#9755FF", button_hover_color="#FFAA3B")
    provider_dropdown.pack(pady=10)

    self.continue_button = ctk.CTkButton(self.window, text="Continue", command=self.show_credential_inputs, state="disabled", fg_color="#9755FF", text_color="#FFFFFF", hover_color="#FFAA3B")
    self.continue_button.pack(pady=10)

  def on_provider_changed(self, *args):
    print(f"Provider changed to: {self.provider_var.get()}")  # Debug print
    self.refresh_ui()

  def refresh_ui(self):
    selected_provider = self.provider_var.get()
    if selected_provider:
      self.continue_button.configure(state="normal")
    else:
      self.continue_button.configure(state="disabled")

  def show_credential_inputs(self):
    print("show_credential_inputs called")  # Debug print
    self.provider = self.provider_var.get()
    if not self.provider:
      messagebox.showerror("Error", "Please select a provider before continuing.")
      return

    print(f"Selected provider: {self.provider}")  # Debug print

    self.window.geometry("300x350")  # Resize window for credential inputs
    
    # Clear previous credential inputs
    for widget in self.window.winfo_children():
      widget.destroy()

    ctk.CTkLabel(self.window, text=f"Enter credentials for {self.provider}:", text_color=["#F4F4F4", "#FFFFFF"]).pack(pady=10)

    if self.provider == "openai":
      self.create_credential_input("OPENAI_API_KEY")
      self.create_credential_input("OPENAI_MODEL")
    elif self.provider == "azure":
      self.create_credential_input("OPENAI_API_KEY")
      self.create_credential_input("AZURE_API_KEY")
      self.create_credential_input("AZURE_API_BASE")
      self.create_credential_input("AZURE_API_VERSION")
      self.create_credential_input("AZURE_MODEL")
    elif self.provider == "anthropic":
      self.create_credential_input("OPENAI_API_KEY")
      self.create_credential_input("ANTHROPIC_API_KEY")
      self.create_credential_input("ANTHROPIC_MODEL")

    ctk.CTkButton(self.window, text="Load from file", command=self.load_from_file, fg_color="#9755FF", text_color="#FFFFFF", hover_color="#FFAA3B").pack(pady=10)
    ctk.CTkButton(self.window, text="Done", command=self.on_done, fg_color="#9755FF", text_color="#FFFFFF", hover_color="#FFAA3B").pack(pady=10)

  def create_credential_input(self, key):
    ctk.CTkLabel(self.window, text=key, text_color=["#F4F4F4", "#FFFFFF"]).pack()
    entry = ctk.CTkEntry(self.window, fg_color=["#2A2A2A", "#2A2A2A"], text_color=["#F4F4F4", "#FFFFFF"], border_color="#9755FF")
    entry.pack()
    self.credential_entries[key] = entry

  def load_from_file(self):
    try:
      with open('src/Settings/provider_config.json', 'r') as f:
        saved_config = json.load(f)
      
      for key, entry in self.credential_entries.items():
        if key in saved_config:
          entry.delete(0, ctk.END)
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