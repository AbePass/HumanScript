import tkinter as tk
from UI.chat_window import ChatUI
from UI.provider_selection import ProviderSelectionUI
from Core.interpreter_manager import InterpreterManager

def main():
    root = tk.Tk()
    root.withdraw()  # Hide the main window while selecting provider

    provider_ui = ProviderSelectionUI(root)
    provider_ui.create_provider_selection_ui()
    root.wait_window(provider_ui.window)  # Wait for the provider selection window to close

    provider = provider_ui.provider
    config = provider_ui.get_config()

    if provider and config:
        interpreter_manager = InterpreterManager()
        interpreter_manager.configure_provider(provider, config)

        root.deiconify()  # Show the main window after provider selection
        chat_ui = ChatUI(root)
        chat_ui.interpreter_manager = interpreter_manager  # Set the interpreter_manager
        root.mainloop()
    else:
        print("No provider selected or configuration incomplete. Exiting...")

if __name__ == "__main__":
    main()