# Assistant Configuration

# Wake word
WAKE_WORD = "assistant"

# Interpreter settings
INTERPRETER_SETTINGS = {
    "supports_vision": True,
    "supports_functions": True,
    "auto_run": True,
    "loop": False,
    "temperature": 0.2,
    "max_tokens": 4096,
    "context_window": 10000,
    "conversation_history_path": "conversation_history",
    "import_computer_api": True
    }

# System message for the interpreter
SYSTEM_MESSAGE_PERMISSIONS_ENV = '''
### Permissions and Environment:
- You have **full permission** to run code and shell commands on the user's computer.
'''

SYSTEM_MESSAGE_EXECUTION_RESPONSE = '''
### Execution and Response:
- If one of your skills is relevant, use it.
- If additional context is provided, use it to inform your actions and responses.
- Use the provided context to answer the query.
'''

SYSTEM_MESSAGE_REFERENCING_SEARCHING = '''
### Referencing and Searching:
- If you need to refer to prior interactions, access the "conversation_history" folder.
- If the user prompt asks to do something that requires accessing an internet browser, use the Computer.browser.search function.
'''

SYSTEM_MESSAGE_SKILLS = '''
### Skills:
- You have access to a folder called "Skillset" located in the current working directory, this contains text files with step by step instructions on how to complete tasks.
- When getting a new prompt, if you think a skill will help you complete a task, read the contents of the skill and follow the instructions strictly do not deviate from them unless specified otherwise.
- If you recieve an error, retry from the last checkpoint.
- DO NOT IGNORE! If a user asks you to save something as a skill, follow "Save_Task_as_Skill.txt" strictly. They are referring to whatever task it was you executed for them. They are not referring to the results of the task unless they explicitly say so. In this case you must use the "Save_Task_as_Skill.txt" skill to fulfill the request. Follow the instuctions in that skill without deviation.
- Here are the skills you have access to:
    {AVAILABLE_SKILLS}
'''

AVAILABLE_SKILLS = '''
Here are the skills and their uses.
- "Computer_browser_search_skill.txt" This skill should be used to retrieve information from the internet, such as checking the weather, web searches, acessing accounts, anything that requires getting online.
- "monkey_skill.txt": download an image of a monkey.
- "HRMD_skill.txt" This should be used whenever you need to create markdown documents that are both human-readable and optimized for providing clear instructions to language learning models (LLMs). This is the default format for skills.
- "pdf_to_markdown_skill.txt": General guidelines for converting PDFs to markdown files.
- "pdf_list_to_markdown_skill.txt": This guide details converting PDF lists under headings into a readable Markdown file by extracting text, identifying headings, and formatting lists.
- "Save_Task_as_Skill.txt": This skill guides the LLM on how to save a user-requested task as a repeatable skill, following a specific format and process, when the user asks to save something as a skill.
'''

SYSTEM_MESSAGE_ENV_VARS = '''
### Environment Variables:
- The user's environment variables will be added below with the format CUSTOM_ENV_VARIABLE_NAME.
- These will hold secure values set by the user, such as API keys, passwords, and other sensitive information.
- Do not overwrite any existing environment variables.
- Do not print the environment variables to the console.
- The following custom environment variables are available:
'''

COMPUTER_SYSTEM_MESSAGE = '''
A python `computer` module is ALREADY IMPORTED, and can be used for web search:

```python
computer.browser.search(query) # Google search results will be returned from this function as a string
```
'''

SYSTEM_MESSAGE = SYSTEM_MESSAGE_PERMISSIONS_ENV + SYSTEM_MESSAGE_EXECUTION_RESPONSE + SYSTEM_MESSAGE_REFERENCING_SEARCHING + SYSTEM_MESSAGE_SKILLS

# Text-to-speech settings
TTS_SETTINGS = {
    "model": "tts-1",
    "voice": "alloy"
}

CHROMA_PATH = "src/Databases"
KB_PATH = "Knowledge"

# Default selected knowledge bases
DEFAULT_SELECTED_KBS = []

BEEP_DURATION = 0.25
BEEP_FREQUENCY = 440

