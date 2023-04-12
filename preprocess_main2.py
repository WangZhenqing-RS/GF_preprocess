# -*- coding: utf-8 -*-
"""
Created on Mon Jun 20 09:42:06 2022

@author: DELL
"""


import os
import time
import glob
from osgeo import gdal
from ortho import ortho
from unpackage import unpackage
from pansharpen import gdal_pansharpen
from build_pyramid import build_pyramid
import warnings
warnings.filterwarnings('ignore')

gdal.UseExceptions()

def preprocess(dem_path, tar_path):
    
    print("开始解压...")
    tar_unpackage_dir = unpackage(tar_path)
    
    print("开始正射校正与融合...")
    # try:
    # 全色数据正射校正
    pan_path = glob.glob(tar_unpackage_dir+"/*PAN*.tiff")[0]
    pan_ortho_path = pan_path.replace(".tiff", "_ortho.tiff")
    
    if "GF1" in pan_path:
        pan_res = 2
    elif "GF2" in pan_path:
        pan_res = 1
    elif "GF6" in pan_path:
        pan_res = 2
    else:
        print("error!")
     
    print(os.path.basename(pan_path),"正射校正...")
    ortho(pan_path, dem_path, pan_res, pan_ortho_path)
    
    # 多光谱数据正射校正
    try:
        mss_path = glob.glob(tar_unpackage_dir+"/*MSS*.tiff")[0]
    except:
        mss_path = glob.glob(tar_unpackage_dir+"/*MUX*.tiff")[0]
    mss_ortho_path = mss_path.replace(".tiff", "_ortho.tiff")
    mss_res = pan_res * 4
    print(os.path.basename(mss_path),"正射校正...")
    ortho(mss_path, dem_path, mss_res, mss_ortho_path)
    
    # 融合
    print("融合...")
    pansharpen_path = pan_ortho_path.split("PAN")[0]+"pansharpen.tiff"
    gdal_pansharpen(["pass",pan_ortho_path,mss_ortho_path,pansharpen_path])
    
    tar_unpackage_dir_paths = glob.glob(tar_unpackage_dir+"/*")
    for tar_unpackage_dir_path in tar_unpackage_dir_paths:
        if tar_unpackage_dir_path==pansharpen_path:
            pass
        else:
            os.remove(tar_unpackage_dir_path)
            
    print("创建金字塔...")
    build_pyramid(pansharpen_path)
    
    print("该景图像处理完成, 并删除压缩包.")
    # except:
    #     print(f"{tar_unpackage_dir} is error!")
    
if __name__ == '__main__':
    
    print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    # 采用envi自带的dem
    dem_path = r"C:\setup\Exelis\ENVI53\data\GMTED2010.jp2"
    # 一堆压缩包所在主文件夹
    tar_dir = "H:/HYF"
    tar_paths = []
    # 假设最多5级文件夹嵌套
    for i in range(5):
        nest_dir = "/*" * i
        tar_paths += glob.glob(f"{tar_dir}{nest_dir}/*.tar.gz")
    
    
    print(f"文件共有{len(tar_paths)}个.")
    for tar_index, tar_path in enumerate(tar_paths):
        print(f"{tar_index+1}/{len(tar_paths)}")
        preprocess(dem_path, tar_path)
        # 删除压缩包
        os.remove(tar_path)
        print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
