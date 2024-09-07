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
2. **Clone the Repository**: Clone this repository to your local machine using `git clone https://github.com/AbePass/HumanScript.git`.
3. **Run the Installer**: Depending on your operating system, run either `.\HumanScript\installers\oi-windows-installer` or `bash HumanScript\installers\oi-linux-installer` to set up the virtual environment (make sure to activate the environment using `.\opai\Scripts\activate` or `source opai\bin\activate` if it doesn't do it automatically).
4. **Configure your assistant**: Edit the Settings/config.py to set up your assistant.
5. **Run your assistant**: Run the assistant either on your desktop or on your Raspberry Pi using `cd HumanScript` and then `python src/main.py`.
6. **Add your own knowledge**: Add your own knowledge in the settings menu of the UI.

For detailed instructions and tutorials, please refer to the documentation provided in this repository.

## Structure

## Acknowledgements

This project uses [Open Interpreter](https://github.com/KillianLucas/open-interpreter), which is licensed under AGPL.