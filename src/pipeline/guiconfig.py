# pipeline/guiconfig.py
from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
import tkinter as tk
from tkinter import simpledialog
from typing import Optional


def gui_get_input(prompt_message: str, hide_input: bool = False) -> Optional[str]:
    """
    Displays a modal GUI popup to get input when no terminal is available.
    """
    try:
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        
        # Determine the display character for password input
        show_char = '*' if hide_input else None

        # Use the simpledialog module for a standard input box
        value = simpledialog.askstring(
            title="Config Input",
            prompt=prompt_message,
            show=show_char  # '*' for hidden/password input
        )
        
        root.destroy()
        return value
        
    except Exception:
        # Fails if tkinter is not installed or the display is not running
        return None