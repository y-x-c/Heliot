"""
Raspberry Pi Camera
Capturing images
"""

import time
import sys
import pickle

#run task will be called with a dataflow object
def run_task():
    print('Running Task Now')
    filepath = '/home/nesl/Downloads/img.jpg'
    binary_file=open(filepath, 'rb')
    data = binary_file.read()
    #print(data)


    #print("*"*100)
    #data_string = pickle.dumps(data)
    #print(data_string)
