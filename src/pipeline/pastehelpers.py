'''
title: pastehelpers.py
author: Clayton Bennett
created: 30 July 2025

why: These functions will not be useful if imported. You'll need to paste the meat.
'''
import inspect
def current_function_name():
    return inspect.currentframe().f_code.co_name
