import os
from pathlib import Path
import time

def memory_opt_directory_processor(directory):
    for x in Path(directory).iterdir():
        try:
            if os.listdir(x):
                # fazer algo
                pass
        except: pass

def time_opt_directory_processor(dirpath):
    for p in os.listdir(dirpath):
        try:
            for fn in os.listdir(p):
                # do something
                break
        except: pass

def main():
    t0 = time.time()
    time_opt_directory_processor('.')
    # memory_opt_directory_processor('.')
    t0 = time.time() - t0
    print(t0)

if __name__=='__main__': main()
