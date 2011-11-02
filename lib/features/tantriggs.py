#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Laurent El Shafey <Laurent.El-Shafey@idiap.ch>

import os 
import torch
import utils


def compute(img_input, pos_input, prep_output,
  CROP_EYES_D, CROP_H, CROP_W, CROP_OH, CROP_OW,
  GAMMA, SIGMA0, SIGMA1, SIZE, THRESHOLD, ALPHA,
  first_annot, force):

  # Initialize cropper and destination array
  FEN = torch.ip.FaceEyesNorm( CROP_EYES_D, CROP_H, CROP_W, CROP_OH, CROP_OW)
  cropped_img = torch.core.array.float64_2(CROP_H, CROP_W)

  # Initialize the Tan and Triggs preprocessing
  TT = torch.ip.TanTriggs( GAMMA, SIGMA0, SIGMA1, SIZE, THRESHOLD, ALPHA)
  preprocessed_img = torch.core.array.float64_2(CROP_H, CROP_W)

  # process the 'dictionary of files'
  for k in img_input:
    if force == True and os.path.exists(prep_output[k]):
      print "Remove old preprocessed image %s." % (prep_output[k])
      os.remove(prep_output[k])

    if os.path.exists(prep_output[k]):
      print "Preprocessed image %s already exists."  % (prep_output[k])
    else:
      print "Preprocessing sample %s with Tan and Triggs." % (img_input[k])

      # input image file
      img_unk = torch.core.array.load( str(img_input[k]) )
      
      # convert to grayscale
      if(img_unk.dimensions() == 3):
        img = torch.ip.rgb_to_gray(img_unk)
      else:
        img = img_unk

      # input eyes position file
      annots = [int(j.strip()) for j in open(pos_input[k]).read().split()]
      if first_annot == 0: LW, LH, RW, RH = annots[0:4]
      else: nb_annots, LW, LH, RW, RH = annots[0:5]

      # extract and crop a face 
      FEN(img, cropped_img, LH, LW, RH, RW) 
      # preprocess a face using Tan and Triggs
      TT(cropped_img, preprocessed_img)

      # vectorize and save
      prep_img_1d = preprocessed_img.as_row()
      prep_img_1d.save(str(prep_output[k]))