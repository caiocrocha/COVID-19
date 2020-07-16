import os
import multiprocessing as mp
import multiprocessing.pool
from functools import partial
import time

# examples for process and thread
USE_THREAD_POOL = False
if USE_THREAD_POOL:
    Pool = multiprocessing.pool.ThreadPool
else:
    Pool = multiprocessing.Pool

def _makedirs_worker(directory, n):
    os.mkdir(f'{directory:0n}')

def makedirs(ndirs):
    num = len(str(ndirs))-1
    # pick number of workers....
    worker_count = min(int(os.cpu_count()), ndirs)
    with Pool(worker_count) as pool:
        pool.map(partial(_makedirs_worker,n=num),range(ndirs), 
            chunksize=int(ndirs/worker_count))

def main():
    os.mkdir('makedirs')
    os.chdir('makedirs')
    t0 = time.time()
    makedirs(1000000)
    t0 = time.time() - t0
    print(t0)
    os.chdir('../')

if __name__=='__main__': main()
