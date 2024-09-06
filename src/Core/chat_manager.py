import threading
from interpreter import interpreter
from Core.command_manager import CommandExecutor
from Core.context_manager import ContextManager
from Settings.config import *

class ChatManager:
  def __init__(self, chat_ui):
    self.chat_ui = chat_ui
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
    if context is None:
      prompt = f"""
      Look at the available skills and use relevant ones to complete the query: {AVAILABLE_SKILLS}

      Query: {query}
      """
    else:
      prompt = f"""
      Context: {context}

      These are user created skills, Prioritize these available skills if they will help you complete the query : {AVAILABLE_SKILLS}

      Query: {query}
      """
    print(prompt)
    return interpreter.chat(prompt, display=False, stream=True)