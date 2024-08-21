# Dark mode colors
DARK_BG_PRIMARY = "#121212"
DARK_BG_SECONDARY = "#1E1E1E"
DARK_BG_TERTIARY = "#2A2A2A"
DARK_BG_INPUT = "#3A3A3A"

DARK_TEXT_PRIMARY = "#FFFFFF"
DARK_TEXT_SECONDARY = "#4A4A4A"

# Light mode colors (for future use)
LIGHT_BG_PRIMARY = "#FFFFFF"
LIGHT_BG_SECONDARY = "#F4F4F4"
LIGHT_BG_TERTIARY = "#E0E0E0"
LIGHT_BG_INPUT = "#D0D0D0"

LIGHT_TEXT_PRIMARY = "#000000"
LIGHT_TEXT_SECONDARY = "#8A8A8A"

# Brand colors
BRAND_PRIMARY = "#9755FF"
BRAND_SECONDARY = "#168275"
BRAND_ACCENT = "#FFAA3B"

# Functional colors
SUCCESS_COLOR = "#4CAF50"
ERROR_COLOR = "#F44336"
WARNING_COLOR = "#FFC107"

# Current theme (can be changed dynamically if we implement theme switching)
CURRENT_THEME = "DARK"

def get_color(color_name):
    if CURRENT_THEME == "DARK":
        return globals()[f"DARK_{color_name}"]
    else:
        return globals()[f"LIGHT_{color_name}"]

# Usage example:
# bg_color = get_color("BG_PRIMARY")
# text_color = get_color("TEXT_PRIMARY")