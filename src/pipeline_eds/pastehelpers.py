'''
title: pastehelpers.py
author: Clayton Bennett
created: 30 July 2025

why: These functions will not be useful if imported. You'll need to paste the meat.
'''
from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
import inspect
def current_function_name():
    return inspect.currentframe().f_code.co_name
