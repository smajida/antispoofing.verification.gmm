#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Laurent El Shafey <Laurent.El-Shafey@idiap.ch>

import os, math
import torch


def normalizeBlocks(src):
  for i in range(src.extent(0)):
    block = src[i, :, :]
    mean = torch.core.array.float64_2.mean(block)
    std = torch.core.array.float64_2.sum((block - mean) ** 2) / block.size()
    if std == 0:
      std = 1
    else:
      std = math.sqrt(std)

    src[i, :, :] = (block - mean) / std

    
def normalizeDCT(src):
  for i in range(src.extent(1)):
    col = src[:, i]
    mean = torch.core.array.float64_1.mean(col)
    std = torch.core.array.float64_1.sum((col - mean) ** 2) / col.size()
    if std == 0:
      std = 1
    else:
      std = math.sqrt(std)

    src[:, i] = (col - mean) / std


def dctfeatures(prep, A_BLOCK_H, A_BLOCK_W, A_OVERLAP_H, A_OVERLAP_W, 
    A_N_DCT_COEF, norm_before, norm_after, add_xy):
  
  blockShape = torch.ip.getBlockShape(prep, A_BLOCK_H, A_BLOCK_W, A_OVERLAP_H, A_OVERLAP_W)
  blocks = torch.core.array.float64_3(blockShape)
  torch.ip.block(prep, blocks, A_BLOCK_H, A_BLOCK_W, A_OVERLAP_H, A_OVERLAP_W)

  if norm_before:
    normalizeBlocks(blocks)

  if add_xy:
    real_DCT_coef = A_N_DCT_COEF - 2
  else:
    real_DCT_coef = A_N_DCT_COEF

  
  # Initializes cropper and destination array
  DCTF = torch.ip.DCTFeatures(A_BLOCK_H, A_BLOCK_W, A_OVERLAP_H, A_OVERLAP_W, real_DCT_coef)
  
  # Calls the preprocessing algorithm
  dct_blocks = DCTF(blocks)

  n_blocks = blockShape[0]

  dct_blocks_min = 0
  dct_blocks_max = A_N_DCT_COEF
  TMP_tensor_min = 0
  TMP_tensor_max = A_N_DCT_COEF

  if norm_before:
    dct_blocks_min += 1
    TMP_tensor_max -= 1

  if add_xy:
    dct_blocks_max -= 2
    TMP_tensor_min += 2
  
  TMP_tensor = torch.core.array.float64_2(n_blocks, TMP_tensor_max)
  
  nBlocks = torch.ip.getNBlocks(prep, A_BLOCK_H, A_BLOCK_W, A_OVERLAP_H, A_OVERLAP_W)
  for by in range(nBlocks[0]):
    for bx in range(nBlocks[1]):
      bi = bx + by * nBlocks[1]
      if add_xy:
        TMP_tensor[bi, 0] = bx
        TMP_tensor[bi, 1] = by
      
      TMP_tensor[bi, TMP_tensor_min:TMP_tensor_max] = dct_blocks[bi, dct_blocks_min:dct_blocks_max]

  if norm_after:
    normalizeDCT(TMP_tensor)

  return TMP_tensor


def compute(img_input, pos_input, features_output,
  CROP_EYES_D, CROP_H, CROP_W, CROP_OH, CROP_OW,
  GAMMA, SIGMA0, SIGMA1, SIZE, THRESHOLD, ALPHA,
  N_ORIENT, N_FREQ, FMAX, ORIENTATION_FULL, K, P, OPTIMAL_GAMMA_ETA,
  GAMMA_G, ETA_G, PF, CANCEL_DC, USE_ENVELOPE,
  BLOCK_H, BLOCK_W, OVERLAP_H, OVERLAP_W, N_DCT_COEF, 
  first_annot, force):

  # Initializes cropper and destination array
  FEN = torch.ip.FaceEyesNorm( CROP_EYES_D, CROP_H, CROP_W, CROP_OH, CROP_OW)
  cropped_img = torch.core.array.float64_2(CROP_H, CROP_W)

  # Initializes the Tan and Triggs preprocessing
  TT = torch.ip.TanTriggs( GAMMA, SIGMA0, SIGMA1, SIZE, THRESHOLD, ALPHA)
  preprocessed_img = torch.core.array.float64_2(CROP_H, CROP_W)

  # Initializes the Gabor filterbank and the destination arrays
  GB = torch.ip.GaborBankFrequency( CROP_H, CROP_W, N_ORIENT, N_FREQ, FMAX, ORIENTATION_FULL, 
          K, P, OPTIMAL_GAMMA_ETA, GAMMA_G, ETA_G, PF, CANCEL_DC)
  if USE_ENVELOPE == False: GB.use_envelope = False
  gabor_imgs = torch.core.array.complex128_3( N_ORIENT*N_FREQ, CROP_H, CROP_W)
  gabor_imgs_mag_2d=[]
  for ig in range(0,N_ORIENT*N_FREQ):
    gabor_imgs_mag_2d.append(torch.core.array.float64_2( CROP_H, CROP_W))

  # Processes the 'dictionary of files'
  for k in img_input:
    print img_input[k]
    for ig in range(0,N_ORIENT*N_FREQ):
      if force == True and os.path.exists(features_output[ig][k]):
        print "Remove old features %s." % (features_output[ig][k])
        os.remove(features_output[ig][k])

    exist = True
    for ig in range(0,N_ORIENT*N_FREQ):
      if not os.path.exists(features_output[ig][k]):
        exist = False

    if exist:
      print "Features for sample %s already exists."  % (img_input[k])
    else:
      print "Computing features from sample %s." % (img_input[k])

      # Loads image file
      img_unk = torch.core.array.load( str(img_input[k]) )
      
      # Converts to grayscale
      if(img_unk.dimensions() == 3):
        img = torch.ip.rgb_to_gray(img_unk)
      else:
        img = img_unk

      # Input eyes position file
      annots = [int(j.strip()) for j in open(pos_input[k]).read().split()]
      if first_annot == 0: LW, LH, RW, RH = annots[0:4]
      else: nb_annots, LW, LH, RW, RH = annots[0:5]

      # Extracts and crops a face 
      FEN(img, cropped_img, LH, LW, RH, RW) 
       
      # Preprocesses a face using Tan and Triggs
      TT(cropped_img, preprocessed_img)
      preprocessed_img_s=preprocessed_img.convert('uint8', sourceRange=(-THRESHOLD,THRESHOLD))

      # Computes Gabor magnitude maps
      src_cplx = preprocessed_img_s.cast('complex128')
      # Calls the preprocessing algorithm
      GB(src_cplx, gabor_imgs)
      # Converts 3D array to a list of 2D arrays
      for x in range(gabor_imgs.extent(0)):
        for y in range(gabor_imgs.extent(1)):
          for z in range(gabor_imgs.extent(2)):
            gabor_imgs_mag_2d[x][y,z] = abs(gabor_imgs[x,y,z])
      
      for ig in range(0,len(gabor_imgs_mag_2d)):
        # Computes DCT features
        dct_blocks=dctfeatures(gabor_imgs_mag_2d[ig], BLOCK_H, BLOCK_W, OVERLAP_H, OVERLAP_W, N_DCT_COEF,
                                True, True, False)
        # Saves to file
        dct_blocks.save(str(features_output[ig][k]))