#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Laurent El Shafey <Laurent.El-Shafey@idiap.ch>

import os
import torch
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
      default=False, help='It is currently not possible to paralellize this script, and hence useless for the time being.')
  args = parser.parse_args()

  # Loads the configuration 
  import imp 
  config = imp.load_source('config', args.config_file)

  # Database
  db = config.db

  # Remove old file if required
  if args.force and os.path.exists(config.ubm_filename):
    print "Removing old UBM"
    os.remove(config.ubm_filename)

  # Checks that the base directory for storing the ubm exists
  utils.ensure_dir(os.path.dirname(config.ubm_filename))

  if os.path.exists(config.ubm_filename):
    print "Loading UBM"
  else:
    print "Training UBM"
    train_files = db.files(directory=config.features_dir, extension=config.features_ext,
                           protocol=config.protocol, groups='world', **config.world_options) 
    #                      expressions='neutral', world_sampling=1, world_noflash=True)
    print "Number of training files: " + str(len(train_files))
    import gmm
    ubm = gmm.gmm_train_UBM(train_files, config.ubm_filename, 
                   config.nb_gaussians, config.iterk, config.iterg_train, config.end_acc, config.var_thd,
                   config.update_weights, config.update_means, config.update_variances, config.norm_KMeans)


if __name__ == "__main__": 
  main()