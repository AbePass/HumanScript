import customtkinter as ctk
from UI.chat_window import ChatUI
from UI.provider_window import ProviderSelectionUI
from Core.interpreter_manager import InterpreterManager
from Settings.color_settings import *
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

print("Starting main.py")

class MainApplication:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("OpenPI Chat")
        self.root.geometry("1280x720")  # 16:9 aspect ratio
        self.root.minsize(800, 450)  # Minimum size while maintaining 16:9
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Set custom color theme
        self.set_custom_theme()

        self.provider_ui = None
        self.chat_ui = None
        self.interpreter_manager = None

    def set_custom_theme(self):
        ctk.set_default_color_theme("dark-blue")  # Use a dark built-in theme as a base
        
        # Override specific colors for dark mode
        ctk.ThemeManager.theme["CTk"]["fg_color"] = [get_color("BG_SECONDARY"), get_color("BG_PRIMARY")]
        ctk.ThemeManager.theme["CTk"]["text"] = [get_color("TEXT_SECONDARY"), get_color("TEXT_PRIMARY")]
        ctk.ThemeManager.theme["CTkButton"]["fg_color"] = [BRAND_PRIMARY, BRAND_SECONDARY]
        ctk.ThemeManager.theme["CTkButton"]["hover_color"] = [BRAND_ACCENT, BRAND_ACCENT]
        ctk.ThemeManager.theme["CTkButton"]["text_color"] = [get_color("TEXT_PRIMARY"), get_color("TEXT_PRIMARY")]
        ctk.ThemeManager.theme["CTkEntry"]["fg_color"] = [get_color("BG_INPUT"), get_color("BG_INPUT")]
        ctk.ThemeManager.theme["CTkEntry"]["text_color"] = [get_color("TEXT_SECONDARY"), get_color("TEXT_PRIMARY")]
        ctk.ThemeManager.theme["CTkEntry"]["border_color"] = [BRAND_PRIMARY, BRAND_SECONDARY]
        ctk.ThemeManager.theme["CTkTextbox"]["fg_color"] = [get_color("BG_INPUT"), get_color("BG_INPUT")]
        ctk.ThemeManager.theme["CTkTextbox"]["text_color"] = [get_color("TEXT_SECONDARY"), get_color("TEXT_PRIMARY")]
        ctk.ThemeManager.theme["CTkTextbox"]["border_color"] = [BRAND_PRIMARY, BRAND_SECONDARY]
        
        # Add new theme settings for the chat interface
        ctk.ThemeManager.theme["CTkFrame"]["fg_color"] = [get_color("BG_SECONDARY"), get_color("BG_PRIMARY")]
        ctk.ThemeManager.theme["CTkScrollableFrame"]["fg_color"] = [get_color("BG_SECONDARY"), get_color("BG_PRIMARY")]

    def start(self):
        self.show_provider_selection()

    def show_provider_selection(self):
        self.provider_ui = ProviderSelectionUI(self.root)
        self.provider_ui.create_provider_selection_ui()
        self.root.wait_window(self.provider_ui.window)
        self.process_provider_selection()

    def process_provider_selection(self):
        print("Processing provider selection")
        logging.debug("Processing provider selection")
        provider = self.provider_ui.provider
        config = self.provider_ui.get_config()

        if provider and config:
            self.interpreter_manager = InterpreterManager()
            self.interpreter_manager.configure_provider(provider, config)
            self.show_chat_ui()
        else:
            self.root.quit()

    def show_chat_ui(self):
        self.root.deiconify()  # Show the main window
        try:
            self.chat_ui = ChatUI(self.root, self.interpreter_manager)
            print("Chat UI created, starting mainloop")
            logging.debug("Chat UI created, starting mainloop")
            self.root.mainloop()
        except Exception as e:
            print(f"Error creating ChatUI: {e}")
            logging.exception("Error creating ChatUI")
            self.root.quit()

    def on_closing(self):
        print("Closing application")
        logging.debug("Closing application")
        self.root.quit()

def main():
    ctk.set_appearance_mode("Dark")  # Set appearance mode to Dark
    app = MainApplication()
    app.start()

if __name__ == "__main__":
    print("Starting main function")
    logging.debug("Starting main function")
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}")
        logging.exception("An error occurred")
