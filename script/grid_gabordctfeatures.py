#!/usr/bin/env python
# Laurent El Shafey <Laurent.El-Shafey@idiap.ch>

"""Submits all feature creation jobs to the Idiap grid"""

import os, sys
import argparse

def checked_directory(base, name):
  """Checks and returns the directory composed of os.path.join(base, name). If
  the directory does not exist, raise a RuntimeError.
  """
  retval = os.path.join(base, name)
  if not os.path.exists(retval):
    raise RuntimeError, "You have not created a link to '%s' at your '%s' installation - you don't have to, but then you need to edit this script to eliminate this error" % (name, base)
  return retval

# Finds myself first
FACEVERIFLIB_DIR = os.path.dirname(os.path.dirname(os.path.realpath(sys.argv[0])))

# Defines the gridtk installation root - by default we look at a fixed location
# in the currently detected FACEVERIFLIB_DIR. You can change this and hard-code
# whatever you prefer.
GRIDTK_DIR = checked_directory(FACEVERIFLIB_DIR, 'gridtk')
sys.path.insert(0, GRIDTK_DIR)

# Defines the torch5spro installation root - by default we look at a fixed
# location in the currently detected FACEVERIFLIB_DIR. You can change this and
# hard-code whatever you prefer.
#TORCH_DIR = checked_directory('/idiap/home/lelshafey/work/development/', 'torch')
#TORCH_DIR = checked_directory(FACEVERIFLIB_DIR, 'torch')

# Defines the replay attack installation root - by default we look at a fixed
# location in the currently detected FACEVERIFLIB_DIR. You can change this and
# hard-code whatever you prefer.
#REPLAY_DIR = checked_directory(FACEVERIFLIB_DIR, 'replay')

# Defines the face annotations installation root - by default we look at a
# fixed location in the currently detected FACEVERIFLIB_DIR. You can change this
# and hard-code whatever you prefer.
#FACES_DIR = checked_directory(FACEVERIFLIB_DIR, 'faces')

# This is a hard-coded number of array jobs we are targeting, for
# parametric jobs.
#TOTAL_REPLAY_FILES = 1200

# The wrapper is required to bracket the execution environment for the faceveriflib
# scripts:
FACEVERIFLIB_WRAPPER = os.path.join(FACEVERIFLIB_DIR, 'shell.py')

# The environment assures the correct execution of the wrapper and the correct
# location of both the 'facevefilib' and 'torch' packages.
FACEVERIFLIB_WRAPPER_ENVIRONMENT = [
    'FACEVERIFLIB_DIR=%s' % FACEVERIFLIB_DIR
#    'TORCH_DIR=%s' % TORCH_DIR,
    ]

def submit(job_manager, command, dependencies=[], array=None):
  """Submits one job using our specialized shell wrapper. We hard-code certain
  parameters we like to use. You can change general submission parameters
  directly at this method."""
 
  from gridtk.tools import make_python_wrapper, random_logdir
  name = os.path.splitext(os.path.basename(command[0]))[0]
  logdir = os.path.join('logs', random_logdir())

  use_cmd = make_python_wrapper([FACEVERIFLIB_WRAPPER, '-d'], command)
  return job_manager.submit(use_cmd, deps=dependencies, cwd=True,
      queue='all.q', stdout=logdir, stderr=logdir, name=name, array=array,
      env=FACEVERIFLIB_WRAPPER_ENVIRONMENT)


def main():
  """The main entry point, control here the jobs options and other details"""

  # Parses options
  parser = argparse.ArgumentParser(description=__doc__,
      formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('-s', '--script-file', metavar='FILE', type=str,
      dest='script_file', default="", help='Filename of the script to run on the grid (defaults to "%(default)s")')
  parser.add_argument('-c', '--config-file', metavar='FILE', type=str,
      dest='config_file', default="", help='Filename of the configuration file to use to run the script on the grid (defaults to "%(default)s")')
  args = parser.parse_args()

  # Loads the configuration 
  import imp
  config = imp.load_source('config', args.config_file)
  TOTAL_ARRAY_JOBS = config.TOTAL_ARRAY_JOBS

  # Let's create the job manager
  from gridtk.manager import JobManager
  jm = JobManager()

  # Runs the jobs
  cmd = [
      'gabordctfeatures.py',
      '--config-file=%s' % args.config_file,
      '--grid'
        ]
  print cmd
  array = (1,TOTAL_ARRAY_JOBS,1)
  job = submit(jm, cmd, array=array)
  print 'submitted:', job


if __name__ == '__main__':
  main()