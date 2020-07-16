def write_hpc(first,last,cmd_line,ncpus,HPC) :

    if HPC == 'SGE' :
        header=f"""\
#!/bin/bash
#$ -N DFlow_{first}_{last}
#$ -S /bin/bash
#$ -q all.q@compute-*
#$ -pe orte {ncpus}
#$ -cwd
#$ -l s_rt=23:55:00
#$ -l h_rt=24:00:00
#$ -o DFlow_{first}_{last}.out
#$ -e DFlow_{first}_{last}.err
"""

    if HPC == 'SLURM' :
        header=f"""\
#!/bin/bash
#SBATCH -p public
#SBATCH --job-name=DFlow_{first}_{last}
#SBATCH -N 1
#SBATCH -n {ncpus}
#SBATCH -t 24:00:00
"""

    if HPC == 'PBS' :
        header=f"""\
#! /bin/bash
#PBS -q  route
#PBS -N DFlow_{first}_{last}
#PBS -l nodes=1:ppn={ncpus}
#PBS -l walltime=24:00:00
#PBS -V
"""

    xargs_cmd=f"""
cat <<EOF | xargs -P{ncpus} -I '{{}}' bash -c '{{}} >/dev/null'
"""

    with open('script.sge','w') as file:
        file.write(header)
        file.write(xargs_cmd)
    
        # Docking Loop
        for i in range(first,last) :
            file.write(cmd_line[i]+'\n')
        file.write('EOF')
