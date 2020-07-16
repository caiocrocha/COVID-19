import os
import multiprocessing as mp
import multiprocessing.pool
import time

# examples for process and thread
USE_THREAD_POOL = False
if USE_THREAD_POOL:
    Pool = multiprocessing.pool.ThreadPool
else:
    Pool = multiprocessing.Pool

def _directory_worker(dirpath):
    try:
        for fn in os.listdir(dirpath):
            if 'ligand' in fn:
                return
    except: pass

def directory_processor(dirpath):
    subdirs = [p for p in os.listdir(dirpath)]
    lensubd = len(subdirs)
    # pick number of workers....
    worker_count = min(int(mp.cpu_count()), lensubd)
    with Pool(worker_count) as pool:
        pool.map(_directory_worker, subdirs, 
            chunksize=int(lensubd/worker_count)))

def main():
    t0 = time.time()
    directory_processor('.')
    t0 = time.time() - t0
    print(t0)

if __name__=='__main__': main()
