
def run_commands(HPC,njobs,ncpus,cmd_line,submit) :
    '''
    Run in parallel using python multiprocessing facility

    If HPC is enabled, user must provide the appropriate header for his/her HPC environment.

    '''
    import subprocess
    from write_hpc import *

    if HPC :

        if HPC in ['SGE','PBS'] :
            submit_command='qsub'
        if HPC in ['SLURM'] :
            submit_command='sbatch'

        max_lines=len(cmd_line)

        for i in range(0,max_lines,njobs) :

            if i+njobs <= max_lines :
                    write_hpc(i,i+njobs,cmd_line,ncpus,HPC)
            else:
                    write_hpc(i,max_lines,cmd_line,ncpus,HPC)

            if submit :
                    job=subprocess.check_output([submit_command, 'script.sge']).decode('ascii')
                    with open('.job','w') as file:
                            file.write(job)
                
    else :
        import multiprocessing
        p = multiprocessing.Pool(ncpus)
        p.map(mp_worker, cmd_line)


def mp_worker(inputs):
    import os
    os.system(inputs)

