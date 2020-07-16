import os
import time

def makedirs(ndirs):
    n = len(str(ndirs))-1
    for i in range(ndirs):
        os.mkdir(f'{i:0n}')

def main():
    os.mkdir('makedirs')
    os.chdir('makedirs')
    t0 = time.time()
    makedirs(1000000)
    t0 = time.time() - t0
    print(t0)
    os.chdir('../')

if __name__=='__main__': main()
