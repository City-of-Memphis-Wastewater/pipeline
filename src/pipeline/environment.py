'''
Title: environment.py
Author: Clayton Bennett
Created: 23 July 2024
'''
import platform
import sys

def vercel():
    #return not(windows()) # conflated, when using any linux that is not a webserver
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

def is_termux():
    # There might be other android versions that can work with the rise od Debian on android in 2025, but for now, assume all android is termux.
    # I wonder how things would go on pydroid3
    return is_android()

def is_android():
    return "android" in platform.platform().lower()

def windows():
    if 'win' in platform.platform().lower():
        windows=True
    else:
        windows=False
    return windows
    
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
