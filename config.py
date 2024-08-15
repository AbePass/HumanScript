# Assistant Configuration

# Wake word
WAKE_WORD = "hey computer"


# Interpreter settings
INTERPRETER_SETTINGS = {
    "supports_vision": True,
    "supports_functions": True,
    "auto_run": True,
    "loop": True,
    "temperature": 0.3,
    "max_tokens": 4096,
    "context_window": 10000,
    "conversation_history_path": "conversation_history",
    "import_computer_api": True
}

# System message for the interpreter
SYSTEM_MESSAGE = '''
### Permissions and Environment:
- You have **full permission** to run code and shell commands on the user's computer.
- Use the Desktop as your default working directory. Save all files on the Desktop unless directed otherwise.

### Execution and Response:
- When a query involves running a command or code, execute it immediately and provide the output.
- If additional context is provided, use it to inform your actions and responses.
- Expect prompts in the format:

Context: {context}

Query: {query}

- Use the provided context to shape your response accurately.

### Referencing and Searching:
- If you need to refer to prior interactions, access the "conversation_history" folder.
- For web-based queries, utilize the `computer.browser.search(query)` function as needed.

### Communication Style:
- Your responses will be spoken aloud to the user. Therefore, ensure your answers are clear, concise, and naturally suited for verbal communication.
- Do not repeat yourself in your responses.


'''

# Text-to-speech settings
TTS_SETTINGS = {
    "model": "tts-1",
    "voice": "alloy"
}

# Knowledge base settings
USE_KNOWLEDGE = True
CHROMA_PATH = "db"
KB_PATH = "knowledge_bases"

# Default selected knowledge bases
DEFAULT_SELECTED_KBS = []

# Audio settings
BEEP_FREQUENCY = 440  # Frequency of the beep in Hz (A4 note)
BEEP_DURATION = 0.2  # Duration of the beep in seconds