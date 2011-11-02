#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Laurent El Shafey <Laurent.El-Shafey@idiap.ch>

import os, math
import utils
import argparse

def main():

  parser = argparse.ArgumentParser(description=__doc__,
      formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('-c', '--config-file', metavar='FILE', type=str,
      dest='config_file', default="", help='Filename of the configuration file to use to run the script on the grid (defaults to "%(default)s")')
  parser.add_argument('-f', '--force', dest='force', action='store_true',
      default=False, help='Force to erase former data if already exist')
  parser.add_argument('--grid', dest='grid', action='store_true',
      default=False, help='If set, assumes it is being run using a parametric grid job. It orders all ids to be processed and picks the one at the position given by ${SGE_TASK_ID}-1')
  args = parser.parse_args()

  # Loads the configuration 
  import imp 
  config = imp.load_source('config', args.config_file)

  # Directories containing the images and the annotations
  db = config.db
  img_input = db.files(directory=config.img_input_dir, extension=config.img_input_ext, protocol=config.protocol, **config.all_files_options)
  pos_input = db.files(directory=config.pos_input_dir, extension=config.pos_input_ext, protocol=config.protocol, **config.all_files_options)
  features_output = []
  for ig in range(0, config.N_FREQ*config.N_ORIENT):
    subdir = "f%do%d" % (ig / config.N_ORIENT, ig % config.N_ORIENT)
    features_output.append(db.files(directory=os.path.join(config.features_dir,subdir), extension=config.features_ext, protocol=config.protocol, **config.all_files_options))

  # finally, if we are on a grid environment, just find what I have to process.
  if args.grid:
    pos = int(os.environ['SGE_TASK_ID']) - 1
    n_total = config.TOTAL_ARRAY_JOBS
    n_per_job = math.ceil(len(img_input) / float(config.TOTAL_ARRAY_JOBS))
    
    if pos >= n_total:
      raise RuntimeError, "Grid request for job %d on a setup with %d jobs" % \
          (pos, n_total)
    img_input_g = utils.split_dictionary(img_input, n_per_job)[pos]
    pos_input_g = utils.split_dictionary(pos_input, n_per_job)[pos]
    img_input = img_input_g
    pos_input = pos_input_g

  # Checks that the directories for storing the features exists
  utils.ensure_dir(config.features_dir)
  for ig in range(0, config.N_FREQ*config.N_ORIENT):
    subdir = "f%do%d" % (ig / config.N_ORIENT, ig % config.N_ORIENT)
    utils.ensure_dir(os.path.join(config.features_dir, subdir))

  import features
  features.lgbphs.compute(img_input, pos_input, features_output,
    config.CROP_EYES_D, config.CROP_H, config.CROP_W, config.CROP_OH, config.CROP_OW,
    config.GAMMA, config.SIGMA0, config.SIGMA1, config.SIZE, config.THRESHOLD, config.ALPHA,
    config.N_ORIENT, config.N_FREQ, config.FMAX, config.ORIENTATION_FULL, config.K, config.P, 
    config.OPTIMAL_GAMMA_ETA, config.GAMMA_G, config.ETA_G, config.PF, config.CANCEL_DC, config.USE_ENVELOPE, 
    config.BLOCK_H, config.BLOCK_W, config.OVERLAP_H, config.OVERLAP_W, config.RADIUS, config.P_N, config.CIRCULAR,
    config.TO_AVERAGE, config.ADD_AVERAGE_BIT, config.UNIFORM, config.ROT_INV,
    config.first_annot, args.force)

if __name__ == "__main__": 
  main()