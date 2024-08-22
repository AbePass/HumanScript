import os
import json
import customtkinter as ctk
from Settings.config import INTERPRETER_SETTINGS, SYSTEM_MESSAGE
from interpreter import interpreter
from tkinter import messagebox  # Import messagebox from tkinter

class InterpreterManager:
  def __init__(self, chat_ui=None):
    self.chat_ui = chat_ui
    self.configure_interpreter()

  def configure_interpreter(self):
    interpreter.llm.supports_vision = INTERPRETER_SETTINGS["supports_vision"]
    interpreter.llm.supports_functions = INTERPRETER_SETTINGS["supports_functions"]
    interpreter.auto_run = INTERPRETER_SETTINGS["auto_run"]
    interpreter.loop = INTERPRETER_SETTINGS["loop"]
    interpreter.llm.temperature = INTERPRETER_SETTINGS["temperature"]
    interpreter.llm.max_tokens = INTERPRETER_SETTINGS["max_tokens"]
    interpreter.llm.context_window = INTERPRETER_SETTINGS["context_window"]
    interpreter.conversation_history_path = INTERPRETER_SETTINGS["conversation_history_path"]
    interpreter.computer.import_computer_api = INTERPRETER_SETTINGS["import_computer_api"]
    interpreter.system_message = SYSTEM_MESSAGE

  def configure_provider(self, provider, config):
    # Common for all providers
    os.environ["OPENAI_API_KEY"] = config.get("OPENAI_API_KEY", "")

    if provider == "azure":
      os.environ["AZURE_API_KEY"] = config["AZURE_API_KEY"]
      os.environ["AZURE_API_BASE"] = config["AZURE_API_BASE"]
      os.environ["AZURE_API_VERSION"] = config["AZURE_API_VERSION"]
      model = config["AZURE_MODEL"]
      interpreter.llm.provider = "azure"
      interpreter.llm.api_key = os.environ["AZURE_API_KEY"]
      interpreter.llm.api_base = os.environ["AZURE_API_BASE"]
      interpreter.llm.api_version = os.environ["AZURE_API_VERSION"]
      interpreter.llm.model = f"azure/{model}"
    elif provider == "openai":
      model = config["OPENAI_MODEL"]
      interpreter.llm.api_key = os.environ["OPENAI_API_KEY"]
      interpreter.llm.model = model
    elif provider == "anthropic":
      os.environ["ANTHROPIC_API_KEY"] = config["ANTHROPIC_API_KEY"]
      model = config["ANTHROPIC_MODEL"]
      interpreter.llm.api_key = os.environ["ANTHROPIC_API_KEY"]
      interpreter.llm.model = f"anthropic/{model}"

    # Prompt user to save credentials
    save_credentials = messagebox.askyesno("Save Credentials", "Do you want to save these credentials to provider_config.json?")
    
    if save_credentials:
      try:
        with open('src/Settings/provider_config.json', 'w') as f:
          json.dump(config, f)
        messagebox.showinfo("Success", "Credentials saved to provider_config.json")
      except Exception as e:
        messagebox.showerror("Error", f"Failed to save credentials: {str(e)}")

    # Set the provider in the configuration
    config['PROVIDER'] = provider