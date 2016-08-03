#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Script minimale per avviare il gioco.
"""

# PyChecker
#import os
#os.environ["PYCHECKER"] = "--stdlib"
#import pychecker.checker

import os.path

if __name__ == "__main__":
    if not os.path.isdir("log"):   #Create log dir if not present
        os.mkdir("log")
        print("Creata cartella log")
    from src.engine import engine
    engine.start()
