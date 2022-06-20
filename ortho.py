# -*- coding: utf-8 -*-
"""
Created on Sun Jun 19 15:30:42 2022

@author: DELL
ref: https://blog.csdn.net/weixin_43762038/article/details/123500331
https://zhuanlan.zhihu.com/p/430397978
https://www.pythonf.cn/read/61251

"""

import os
from osgeo import gdal, osr


# 正射校正
def ortho(file_name, dem_name, res, out_file_name):
    
    dataset = gdal.Open(file_name, gdal.GA_ReadOnly)
    
    # 是否北半球
    is_north = 1 if os.path.basename(file_name).split('_')[3][0] == 'N' else 0
    # 计算UTM区号
    zone = str(int(float(os.path.basename(file_name).split('_')[2][1:])/6) + 31)
    zone = int('326' + zone) if is_north else int('327' + zone)
    
    dstSRS = osr.SpatialReference()
    dstSRS.ImportFromEPSG(zone)
    
    # dstSRS = 'EPSG:4326'
    
    tmp_ds = gdal.Warp(out_file_name, dataset, format = 'GTiff', 
                       xRes = res, yRes = res, dstSRS = dstSRS, 
                       rpc = True, resampleAlg=gdal.GRIORA_Bilinear,
                       transformerOptions=["RPC_DEM="+dem_name])
    dataset = tds = None

