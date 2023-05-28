# -*- coding: utf-8 -*-
"""
Created on Mon Jun 20 09:42:06 2022

@author: DELL
"""

import glob
import os
from unpackage import unpackage
from ortho import ortho
from pansharpen import gdal_pansharpen
from osgeo import gdal
from build_pyramid import build_pyramid
import warnings
warnings.filterwarnings('ignore')

gdal.UseExceptions()

def preprocess(dem_path, tar_dir):
    
    tar_paths = glob.glob(tar_dir+"/*.tar.gz")
    tar_unpackage_dirs = []
    print("开始解压...")
    for tar_index, tar_path in enumerate(tar_paths):
        print(f"{tar_index+1}/{len(tar_paths)}")
        print(os.path.basename(tar_path))
        tar_unpackage_dir = unpackage(tar_path)
        tar_unpackage_dirs.append(tar_unpackage_dir)
    
    print("开始正射校正与融合...")
    for tar_unpackage_index, tar_unpackage_dir in enumerate(tar_unpackage_dirs):
        print(f"{tar_unpackage_index+1}/{len(tar_unpackage_dirs)}")
        
        # 全色数据正射校正
        pan_path = glob.glob(tar_unpackage_dir+"/*PAN*.tiff")[0]
        pan_ortho_path = pan_path.replace(".tiff", "_ortho.tiff")
        pan_res = 0.8
        print(os.path.basename(pan_path),"正射校正...")
        ortho(pan_path, dem_path, pan_res, pan_ortho_path)
        
        # 多光谱数据正射校正
        mss_path = glob.glob(tar_unpackage_dir+"/*MSS*.tiff")[0]
        mss_ortho_path = mss_path.replace(".tiff", "_ortho.tiff")
        mss_res = 3.2
        print(os.path.basename(mss_path),"正射校正...")
        ortho(mss_path, dem_path, mss_res, mss_ortho_path)
        
        # 融合
        print("融合...")
        pansharpen_path = pan_ortho_path.split("PAN")[0]+"pansharpen.tiff"
        gdal_pansharpen(["pass",pan_ortho_path,mss_ortho_path,pansharpen_path])
        print("创建金字塔...")
        build_pyramid(pansharpen_path)
    
if __name__ == '__main__':
    
    # 采用envi自带的dem
    dem_path = r"C:\setup\Exelis\ENVI53\data\GMTED2010.jp2"
    # 一堆压缩包所在文件夹
    tar_dir = r"E:\WangZhenQing\GF2"
    preprocess(dem_path, tar_dir)
