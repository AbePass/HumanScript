import os
import json
import customtkinter as ctk
from Settings.config import INTERPRETER_SETTINGS, COMPUTER_SYSTEM_MESSAGE, SYSTEM_MESSAGE
from interpreter import interpreter
from tkinter import messagebox  # Import messagebox from tkinter

class InterpreterManager:
  def __init__(self, knowledge_manager =None, chat_ui = None):
    self.knowledge_manager = knowledge_manager  # Initialize knowledge_manager
    self.chat_ui = chat_ui
    self.configure_interpreter()
    
    # Initialize any other necessary attributes here
  def configure_interpreter(self):
    interpreter.llm.supports_vision = INTERPRETER_SETTINGS["supports_vision"]
    interpreter.auto_run = INTERPRETER_SETTINGS["auto_run"]
    interpreter.loop = INTERPRETER_SETTINGS["loop"]
    interpreter.llm.temperature = INTERPRETER_SETTINGS["temperature"]
    interpreter.llm.max_tokens = INTERPRETER_SETTINGS["max_tokens"]
    interpreter.llm.context_window = INTERPRETER_SETTINGS["context_window"]
    interpreter.conversation_history_path = INTERPRETER_SETTINGS["conversation_history_path"]
    interpreter.computer.import_computer_api = INTERPRETER_SETTINGS["import_computer_api"]
    interpreter.computer.system_message = COMPUTER_SYSTEM_MESSAGE
    print(interpreter.computer.system_message)
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

  def update_system_message(self, selected_kbs):
    # Use self.knowledge_manager to get available skills
    skills = self.knowledge_manager.get_available_skills()
    # Append instructions from selected knowledge bases
    for kb in selected_kbs:
        instructions = self.knowledge_manager.instructions.get(kb, "")
        if instructions:
            interpreter.system_message += "\n" + instructions
    # Append dynamically retrieved skills with their file paths
    skill_list = "\n    - ".join([f"{name} (Path: {path})" for name, path in skills])
    SYSTEM_MESSAGE_SKILLS = '''
    ### Skills:
    - You have access to various skills from the selected knowledge bases. Each skill contains step-by-step instructions on how to complete specific tasks.
    - If you think a skill will help you complete a task, read the contents of the skill file at the provided path to see if it can help you.
    - If it will help you complete the task, follow the instructions strictly. Do not deviate unless specified otherwise.
    - If you receive an error, retry from the last checkpoint.
    - Here are the skills you have access to:
    ''' + "\n    - " + skill_list
    interpreter.system_message = SYSTEM_MESSAGE + "\n" + SYSTEM_MESSAGE_SKILLS
    # Update the interpreter's system message
    # Print the updated system message and available skills
    print(f"System Message Updated:\n{interpreter.system_message}")

    print(f"Available Skills: {[name + ' (' + path + ')' for name, path in skills]}")