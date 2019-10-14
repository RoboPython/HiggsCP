#!/bin/bash -l
## Job name
#SBATCH -J TrainBetaRHORHO
## Number of nodes
#SBATCH -N 1
## Number of tasks per node
#SBATCH --ntasks-per-node=1
## Memory per CPU (default: 5GB)
#SBATCH --mem-per-cpu=40GB
## Max job time (HH:MM:SS format)
#SBATCH --time=72:00:00
## Pratition specification
#SBATCH -p plgrid
#SBATCH --array=0-19

## Setup
if [ -f setup ]; then source setup; fi
export PYTHONPATH=$ANACONDA_PYTHON_PATH
module add plgrid/apps/cuda/7.5

## Chaninging dir to workdir
cd $WORKDIR

## Command
BETAS=(0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1.0 1.1 1.2 1.3 1.4 1.5 1.6 1.7 1.8 1.9 2.0)
BETA=${BETAS[$SLURM_ARRAY_TASK_ID]}

echo "TrainBeta rhorho Job. Beta: " $BETA

$ANACONDA_PYTHON_PATH/python2.7 $WORKDIR/main.py -t nn_rhorho -i $RHORHO_DATA -e 50 -f Variant-3.1 -d 0.2 --beta $BETA -l 6 -s 300
