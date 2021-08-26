#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 25 14:52:30 2021

@author: ronan
"""
from queue import Empty

def clearQueue(queue):
    while not queue.empty():
        queue.get()
    return 0

# def clearQueue(q):
#     try:
#         while True:
#             q.get_nowait()
#     except Empty:
#         pass
