import threading
from interpreter import interpreter
from Core.command_manager import CommandExecutor
from Core.context_manager import ContextManager
from Settings.config import *

class ChatManager:
  def __init__(self):
    self.use_knowledge = USE_KNOWLEDGE
    self.selected_kbs = DEFAULT_SELECTED_KBS.copy()
    self.is_voice_mode = False
    self.listen_thread = None
    self.context_manager = ContextManager()
    self.command_executor = CommandExecutor()

  def process_input(self, user_input):
      global is_voice_mode, interpreter
      # Query the database
      if self.use_knowledge and self.selected_kbs:
          print("Querying vector database")
          context_text, sources = self.context_manager.query_vector_database(user_input, self.selected_kbs)
      else:
          context_text, sources = None, []

      full_response = ""
      response_generator = self.get_interpreter_response(context_text, user_input)

      return response_generator,sources

  def get_interpreter_response(self, context, query):
    command_response = self.command_executor.execute_command(query)

    if command_response is not None:
      prompt = command_response
    elif not context:
      prompt = query
    else:
      prompt = f"Context: {context}\n\nQuery: {query}"

    return interpreter.chat(prompt, display=False, stream=True)