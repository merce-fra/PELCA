# -*- coding: utf-8 -*-
"""
Created on Mon Mar 20 17:57:17 2023

@author: baudais
"""

import numpy as np
import pandas as pd
import os
import time
import csv
import shutil
import pickle
  
def _rd_np(directory,filename):
    # Path
    path = os.path.join(directory,filename)    
    with open(path, 'rb') as fp:
        data = np.load(fp)
    return data

def _rd_pkl(directory,filename):
    # Path
    path = os.path.join(directory,filename)    
    with open(path, 'rb') as fp:
        data = pickle.load(fp)
    return data