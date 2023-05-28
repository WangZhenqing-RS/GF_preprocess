# -*- coding: utf-8 -*-
"""
Created on Tue Jun 21 15:58:47 2022

@author: DELL
"""
import fiona
import rasterio
from rasterio.mask import mask
from build_pyramid import build_pyramid
import os

def extract_by_shp(raster_path, shp_path, out_raster_path):
    
    print("提取...")
    with fiona.open(shp_path, "r", encoding='utf-8') as shapefile:
        # 获取所有要素feature的形状geometry
        geoms = [feature["geometry"] for feature in shapefile]
    
    # print(geoms)
    # 裁剪
    with rasterio.open(raster_path) as src:
        out_image, out_transform = mask(src, geoms, crop=True)
        out_meta = src.meta.copy()
    
    # 更新输出文件的元数据
    out_meta.update({"driver": "GTiff",
                     "height": out_image.shape[1],
                     "width": out_image.shape[2],
                     "transform": out_transform})
    
    # 保存
    with rasterio.open(out_raster_path, "w", **out_meta) as dest:
        dest.write(out_image)
    
    print("创建金字塔")
    # 创建金字塔
    build_pyramid(out_raster_path)

