## Platform Agnostic Assistant Framework by Abraham Passmore at Human Devices

This repository by Abraham Passmore at Human Devices (humandevices.co) presents a platform agnostic assistant framework designed to run on a Raspberry Pi but can also be run on any platform as a desktop assistant. The framework provides tools like customizable knowledge bases, wakeword recognition for handsfree use, and chat memory, offering a versatile and powerful platform for various uses, including but not limited to:

- Home automation
- IoT projects
- Educational tools
- Prototyping and development
- Accessibility

### Features

- **Open Interpreter Integration**: Seamlessly integrates with Open Interpreter to provide advanced functionalities and ease of use.
- **Customizable Knowledge Bases**: Allows you to create and manage knowledge bases tailored to your specific needs.
- **Wakeword Recognition**: Enables handsfree use through wakeword detection.
- **Chat Memory**: Remembers previous interactions to provide a more coherent and context-aware assistant experience.
- **Versatile Applications**: Suitable for a wide range of projects and applications.
- **User-Friendly**: Designed to be easy to set up and use, even for beginners.

### Getting Started

To get started with this assistant framework, follow these steps:

1. **Prerequisites**: Ensure you have Python, Git, and C++ development tools installed on your system.
2. **Clone the Repository**: Clone this repository to your local machine using `git clone https://github.com/AbePass/OpenPI.git`.
3. **Run the Installer**: Depending on your operating system, run either `.OpenPI\installers\oi-windows-installer` or `bash OpenPI\installers\oi-linux-installer` to set up the virtual environment (make sure to activate the environment using `.\opai\Scripts\activate` or `source opai\bin\activate` if it doesn't do it automatically).
4. **Configure your assistant**: Edit the Settings/config.py to set up your assistant.
5. **Run your assistant**: Run the assistant either on your desktop or on your Raspberry Pi using `python OpenPI/UI/chat.py`.
6. **Add your own knowledge**: Add your own knowledge in the settings menu of the UI.

For detailed instructions and tutorials, please refer to the documentation provided in this repository.

## Structure

### Folder Structure

The repository is organized into the following main directories:

- **UI/**: Contains the user interface components, including the main chat application (`chat.py`).
- **tools/**: Includes various utility scripts for building and querying the vector database, as well as command execution.
  - `build_vector_database.py`: Script to build and update the vector database.
  - `query_vector_database.py`: Script to query the vector database.
  - `commands.py`: Script to handle different commands and their execution.
- **Settings/**: Contains configuration files for setting up the assistant.
- **conversation_history/**: Stores the history of conversations for context-aware interactions.
- **Databases/**: Directory where the vector databases are stored.
- **Knowledge/**: Directory for storing knowledge bases.
- **User_Data/**: Contains user-specific data and configurations.

## Acknowledgements

This project uses [Open Interpreter](https://github.com/KillianLucas/open-interpreter), which is licensed under AGPL.