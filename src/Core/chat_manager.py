import threading
from interpreter import interpreter
from Core.command_manager import CommandExecutor
from Core.context_manager import ContextManager
from Settings.config import *


class ChatManager:
  def __init__(self, interpreter_manager, chat_ui):  # Added chat_ui parameter
    self.interpreter_manager = interpreter_manager
    self.knowledge_manager = chat_ui.knowledge_manager  # Access KnowledgeManager instance
    # If InterpreterManager needs KnowledgeManager, set it here
    self.interpreter_manager.knowledge_manager = self.knowledge_manager
    self.chat_ui = chat_ui  # Now defined
    self.selected_kbs = chat_ui.selected_kbs
    self.wake_word = chat_ui.wake_word
    self.interpreter_settings = chat_ui.interpreter_settings
    self.env_vars = chat_ui.env_vars
    self.is_voice_mode = False
    self.listen_thread = None
    self.context_manager = ContextManager(chat_ui)
    self.command_executor = CommandExecutor()

  def update_selected_kbs(self, selected_kbs):
    self.selected_kbs = selected_kbs
    self.interpreter_manager.update_system_message(selected_kbs)

  def update_wake_word(self, wake_word):
    self.wake_word = wake_word

  def update_interpreter_settings(self, interpreter_settings):
    self.interpreter_settings = interpreter_settings

  def update_env_vars(self, env_vars):
    self.env_vars = env_vars

  def process_input(self, user_input, selected_kbs):
      # Check for command first
      command_response = self.command_executor.execute_command(user_input)
      if command_response is not None:
          response_generator = self.get_interpreter_response(context=None, query=command_response)
          return response_generator, []

      # Query the database if no command is found
      if selected_kbs:
          print(f"Querying selected knowledge bases: {selected_kbs}")
          context_text, sources = self.context_manager.query_vector_database(user_input, selected_kbs)
      else:
          context_text, sources = None, []

      response_generator = self.get_interpreter_response(context_text, user_input)

      return response_generator, sources

  def get_interpreter_response(self, context, query):
    available_skills = self.knowledge_manager.get_available_skills()
    if available_skills:
      # Extract skill names and paths from the tuples
      skill_info = [f"{name} (Path: {path})\n" for name, path in available_skills]
      #available_skills_str = ", ".join(skill_info)
      base_prompt = f"""
Available skills: {skill_info}

Instructions:
1. Analyze the query carefully.
2. If any available skills are relevant, read the contents of the skill file at the provided path to see if it can help you.
3. If no skills are relevant or if the query is simple, respond naturally without mentioning or using skills.
4. Always prioritize giving a helpful and appropriate response over using skills unnecessarily.

Query: {query}
"""
    else:
        base_prompt = f"""
        {query}
        """
    if context is not None:
        context_prompt = f"""
        Consider the following context when formulating your response:
        {context}
        """
        prompt = context_prompt + "\n" + base_prompt
    else:
        prompt = base_prompt
    
    print(prompt)
    return interpreter.chat(prompt, display=False, stream=True)
