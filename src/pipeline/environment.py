'''
Title: environment.py
Author: Clayton Bennett
Created: 23 July 2024
'''
import platform
import sys
import os

def vercel():
    #return not(is_windows()) # conflated, when using any linux that is not a webserver
    # the important questions is actually "are we running on a webserver?"
    return False # hard code this

def matplotlib_enabled():
    #print(f"is_termux() = {is_termux()}")
    if is_termux():
        return False
    else:
        try:
            import matplotlib
            return True
        except ImportError:
            return False
        
def fbx_enabled():
    if is_termux():
        return False
    else:
        return True 
def is_linux():
    if 'linux' in platform.platform().lower():
        linux=True
    else:
        linux=False
    return linux

def is_termux():
    # There might be other android versions that can work with the rise od Debian on android in 2025, but for now, assume all android is termux.
    # I wonder how things would go on pydroid3
    return is_android()

def is_android():
    return "android" in platform.platform().lower()

def is_windows():
    if 'win' in platform.platform().lower():
        windows=True
    else:
        windows=False
    return windows
def is_apple():
    if 'darwin' in platform.platform().lower():
        apple=True
    else:
        apple=False
    return apple
    
def pyinstaller():
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        pyinstaller = True
    else:
        pyinstaller = False
    return pyinstaller

def frozen():
    if getattr(sys, 'frozen', True):
        frozen = True
    else:
        frozen = False
    return frozen

def operatingsystem():
    return platform.system() #determine OS


def open_file_in_default_app(filepath):
    import subprocess
    """Opens a file with its default application based on the OS."""
    if is_windows():
        os.startfile(filepath)
    elif is_termux():
        subprocess.run(['termux-open', filepath])
    elif is_linux():
        subprocess.run(['xdg-open', filepath])
    elif is_apple():
        subprocess.run(['open', filepath])
    else:
        print("Unsupported operating system.")