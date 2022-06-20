# -*- coding: utf-8 -*-
"""
Created on Mon Jun 20 09:38:38 2022

@author: DELL
"""
import tarfile

# 解压
def unpackage(file_name):
    
    # 提取解压文件夹名
    if ".tar.gz" in file_name:
        out_dir = file_name.split(".tar.gz")[0]
    else:
        out_dir = file_name.split(".")[0]
    # 进行解压
    with tarfile.open(file_name) as file:
        file.extractall(path = out_dir)
    return out_dir