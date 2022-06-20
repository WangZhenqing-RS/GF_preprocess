# -*- coding: utf-8 -*-
"""
Created on Mon Jun 20 15:19:22 2022

@author: DELL
"""

from osgeo import gdal

def build_pyramid(file_name):
    dataset = gdal.Open(file_name)
    dataset.BuildOverviews(overviewlist=[2, 4 ,8, 16])
    del dataset
