# -*- coding: utf-8 -*-
"""
Created on Mon May 15 15:59:13 2023

@author: DELL
"""

import os
import re
import glob
import warnings
import numpy as np
import xml.etree.ElementTree as ET

from osgeo import gdal, osr

warnings.filterwarnings ('ignore')

# 获取影像元信息xml文件名、1级影像tiff文件名
def get_meta_image_path(data_dir):
    meta_path = glob.glob(data_dir+"/*.meta.xml")[0]
    
    HH_paths = glob.glob(data_dir+"/*_HH_*.tiff")
    if len(HH_paths) == 0:
        HH_path = None
    else:
        HH_path = HH_paths[0]
    HV_paths = glob.glob(data_dir+"/*_HV_*.tiff")
    if len(HV_paths) == 0:
        HV_path = None
    else:
        HV_path = HV_paths[0]
    VH_paths = glob.glob(data_dir+"/*_VH_*.tiff")
    if len(VH_paths) == 0:
        VH_path = None
    else:
        VH_path = VH_paths[0]
    VV_paths = glob.glob(data_dir+"/*_VV_*.tiff")
    if len(VV_paths) == 0:
        VV_path = None
    else:
        VV_path = VV_paths[0]
    
    image_paths = [HH_path, HV_path, VH_path, VV_path]
    return meta_path, image_paths

# 获取影像rpc文件名(有理多项式系数,rational polynomail cofficient)
def get_rpc_path(data_dir):
    # rpc文件后缀可能为rpb或者rpc
    HH_rpcs = glob.glob(data_dir+"/*_HH_*.rpb") + glob.glob(data_dir+"/*_HH_*.rpc")
    if len(HH_rpcs) == 0:
        HH_rpc = None
    else:
        HH_rpc = HH_rpcs[0]
    HV_rpcs = glob.glob(data_dir+"/*_HV_*.rpb") + glob.glob(data_dir+"/*_HV_*.rpc")
    if len(HV_rpcs) == 0:
        HV_rpc = None
    else:
        HV_rpc = HV_rpcs[0]
    VH_rpcs = glob.glob(data_dir+"/*_VH_*.rpb") + glob.glob(data_dir+"/*_VH_*.rpc")
    if len(VH_rpcs) == 0:
        VH_rpc = None
    else:
        VH_rpc = VH_rpcs[0]
    VV_rpcs = glob.glob(data_dir+"/*_VV_*.rpb") + glob.glob(data_dir+"/*_VV_*.rpc")
    if len(VV_rpcs) == 0:
        VV_rpc = None
    else:
        VV_rpc = VV_rpcs[0]
    
    rpc_paths = [HH_rpc, HV_rpc, VH_rpc, VV_rpc]
    return rpc_paths

# 从元数据中获取归一化峰值qualifyValue与定标常数Calibration
def get_qualifyValue_calibrations(meta_path):
    tree = ET.parse(meta_path)
    
    HH_qualifyValue = tree.findall("imageinfo")[0].find("QualifyValue").find("HH").text
    HV_qualifyValue = tree.findall("imageinfo")[0].find("QualifyValue").find("HV").text
    VH_qualifyValue = tree.findall("imageinfo")[0].find("QualifyValue").find("VH").text
    VV_qualifyValue = tree.findall("imageinfo")[0].find("QualifyValue").find("VV").text
    qualifyValues = [HH_qualifyValue, HV_qualifyValue, VH_qualifyValue, VV_qualifyValue]
    
    HH_calibrationConst = tree.findall("processinfo")[0].find("CalibrationConst").find("HH").text
    HV_calibrationConst = tree.findall("processinfo")[0].find("CalibrationConst").find("HV").text
    VH_calibrationConst = tree.findall("processinfo")[0].find("CalibrationConst").find("VH").text
    VV_calibrationConst = tree.findall("processinfo")[0].find("CalibrationConst").find("VV").text
    calibrationConsts = [HH_calibrationConst, HV_calibrationConst, VH_calibrationConst, VV_calibrationConst]

    return qualifyValues, calibrationConsts

# 从元数据中获取标称分辨率信息/m
def get_resolution(meta_path):
    tree = ET.parse(meta_path)
    
    resolution = float(tree.findall("productinfo")[0].find("NominalResolution").text)
    
    return resolution

# 图像写入
def imwrite(data, save_path, geotrans=(0,0,0,0,0,0), proj=""):

    if 'int8' in data.dtype.name:
        datatype = gdal.GDT_Byte
    elif 'int16' in data.dtype.name:
        datatype = gdal.GDT_UInt16
    else:
        datatype = gdal.GDT_Float32
    if len(data.shape) == 3:
        im_bands, im_height, im_width = data.shape
    elif len(data.shape) == 2:
        data = np.array([data])
        im_bands, im_height, im_width = data.shape
        
    # 创建文件
    driver = gdal.GetDriverByName("GTiff")
    dataset = driver.Create(save_path, int(im_width), int(im_height), int(im_bands), datatype)
    if (dataset != None):
        dataset.SetGeoTransform(geotrans)  # 写入仿射变换参数
        dataset.SetProjection(proj)  # 写入投影
    for i in range(im_bands):
        dataset.GetRasterBand(i + 1).WriteArray(data[i])
    del dataset

# 读取rpc文件
def read_rpb(rpb_path):
    with open(rpb_path, 'r') as f:
        buff = f.read()

        # Name the url of the reference：http://geotiff.maptools.org/rpc_prop.html
        ERR_BIAS1 = 'errBias'  # Error - deviation. RMS error for all points in the image (in m/horizontal axis) (-1.0, if unknown)
        ERR_BIAS2 = ';'

        ERR_RAND1 = 'errRand'  # Error - random. RMS random error in meters for each horizontal axis of each point in the image (-1.0 if unknown)
        ERR_RAND2 = ';'

        LINE_OFF1 = 'lineOffset'
        LINE_OFF2 = ';'

        SAMP_OFF1 = 'sampOffset'
        SAMP_OFF2 = ';'

        LAT_OFF1 = 'latOffset'
        LAT_OFF2 = ';'

        LONG_OFF1 = 'longOffset'
        LONG_OFF2 = ';'

        HEIGHT_OFF1 = 'heightOffset'
        HEIGHT_OFF2 = ';'

        LINE_SCALE1 = 'lineScale'
        LINE_SCALE2 = ';'

        SAMP_SCALE1 = 'sampScale'
        SAMP_SCALE2 = ';'

        LAT_SCALE1 = 'latScale'
        LAT_SCALE2 = ';'

        LONG_SCALE1 = 'longScale'
        LONG_SCALE2 = ';'

        HEIGHT_SCALE1 = 'heightScale'
        HEIGHT_SCALE2 = ';'

        LINE_NUM_COEFF1 = 'lineNumCoef'
        LINE_NUM_COEFF2 = ';'

        LINE_DEN_COEFF1 = 'lineDenCoef'
        LINE_DEN_COEFF2 = ';'

        SAMP_NUM_COEFF1 = 'sampNumCoef'
        SAMP_NUM_COEFF2 = ';'

        SAMP_DEN_COEFF1 = 'sampDenCoef'
        SAMP_DEN_COEFF2 = ';'

        # Regularized extraction values
        pat_ERR_BIAS = re.compile(ERR_BIAS1 + '(.*?)' + ERR_BIAS2, re.S)
        result_ERR_BIAS = pat_ERR_BIAS.findall(buff)
        ERR_BIAS = result_ERR_BIAS[0]
        ERR_BIAS = ERR_BIAS.replace(" ", "")

        pat_ERR_RAND = re.compile(ERR_RAND1 + '(.*?)' + ERR_RAND2, re.S)
        result_ERR_RAND = pat_ERR_RAND.findall(buff)
        ERR_RAND = result_ERR_RAND[0]
        ERR_RAND = ERR_RAND.replace(" ", "")

        pat_LINE_OFF = re.compile(LINE_OFF1 + '(.*?)' + LINE_OFF2, re.S)
        result_LINE_OFF = pat_LINE_OFF.findall(buff)
        LINE_OFF = result_LINE_OFF[0]
        LINE_OFF = LINE_OFF.replace(" ", "")

        pat_SAMP_OFF = re.compile(SAMP_OFF1 + '(.*?)' + SAMP_OFF2, re.S)
        result_SAMP_OFF = pat_SAMP_OFF.findall(buff)
        SAMP_OFF = result_SAMP_OFF[0]
        SAMP_OFF = SAMP_OFF.replace(" ", "")

        pat_LAT_OFF = re.compile(LAT_OFF1 + '(.*?)' + LAT_OFF2, re.S)
        result_LAT_OFF = pat_LAT_OFF.findall(buff)
        LAT_OFF = result_LAT_OFF[0]
        LAT_OFF = LAT_OFF.replace(" ", "")

        pat_LONG_OFF = re.compile(LONG_OFF1 + '(.*?)' + LONG_OFF2, re.S)
        result_LONG_OFF = pat_LONG_OFF.findall(buff)
        LONG_OFF = result_LONG_OFF[0]
        LONG_OFF = LONG_OFF.replace(" ", "")

        pat_HEIGHT_OFF = re.compile(HEIGHT_OFF1 + '(.*?)' + HEIGHT_OFF2, re.S)
        result_HEIGHT_OFF = pat_HEIGHT_OFF.findall(buff)
        HEIGHT_OFF = result_HEIGHT_OFF[0]
        HEIGHT_OFF = HEIGHT_OFF.replace(" ", "")

        pat_LINE_SCALE = re.compile(LINE_SCALE1 + '(.*?)' + LINE_SCALE2, re.S)
        result_LINE_SCALE = pat_LINE_SCALE.findall(buff)
        LINE_SCALE = result_LINE_SCALE[0]
        LINE_SCALE = LINE_SCALE.replace(" ", "")

        pat_SAMP_SCALE = re.compile(SAMP_SCALE1 + '(.*?)' + SAMP_SCALE2, re.S)
        result_SAMP_SCALE = pat_SAMP_SCALE.findall(buff)
        SAMP_SCALE = result_SAMP_SCALE[0]
        SAMP_SCALE = SAMP_SCALE.replace(" ", "")

        pat_LAT_SCALE = re.compile(LAT_SCALE1 + '(.*?)' + LAT_SCALE2, re.S)
        result_LAT_SCALE = pat_LAT_SCALE.findall(buff)
        LAT_SCALE = result_LAT_SCALE[0]
        LAT_SCALE = LAT_SCALE.replace(" ", "")

        pat_LONG_SCALE = re.compile(LONG_SCALE1 + '(.*?)' + LONG_SCALE2, re.S)
        result_LONG_SCALE = pat_LONG_SCALE.findall(buff)
        LONG_SCALE = result_LONG_SCALE[0]
        LONG_SCALE = LONG_SCALE.replace(" ", "")

        pat_HEIGHT_SCALE = re.compile(HEIGHT_SCALE1 + '(.*?)' + HEIGHT_SCALE2, re.S)
        result_HEIGHT_SCALE = pat_HEIGHT_SCALE.findall(buff)
        HEIGHT_SCALE = result_HEIGHT_SCALE[0]
        HEIGHT_SCALE = HEIGHT_SCALE.replace(" ", "")

        pat_LINE_NUM_COEFF = re.compile(LINE_NUM_COEFF1 + '(.*?)' + LINE_NUM_COEFF2, re.S)
        result_LINE_NUM_COEFF = pat_LINE_NUM_COEFF.findall(buff)
        LINE_NUM_COEFF = result_LINE_NUM_COEFF[0]
        LINE_NUM_COEFF3 = LINE_NUM_COEFF
        # LINE_NUM_COEFF3 = LINE_NUM_COEFF3.strip('()')
        # LINE_NUM_COEFF3 = LINE_NUM_COEFF3.strip('()')
        LINE_NUM_COEFF3 = LINE_NUM_COEFF3.replace(" ", "")
        LINE_NUM_COEFF3 = LINE_NUM_COEFF3.replace('(', '')
        LINE_NUM_COEFF3 = LINE_NUM_COEFF3.replace(')', '')
        LINE_NUM_COEFF3 = LINE_NUM_COEFF3.replace('\n', '')
        LINE_NUM_COEFF3 = LINE_NUM_COEFF3.replace('\t', '')
        LINE_NUM_COEFF3 = LINE_NUM_COEFF3.replace(',', ' ')

        pat_LINE_DEN_COEFF = re.compile(LINE_DEN_COEFF1 + '(.*?)' + LINE_DEN_COEFF2, re.S)
        result_LINE_DEN_COEFF = pat_LINE_DEN_COEFF.findall(buff)
        LINE_DEN_COEFF = result_LINE_DEN_COEFF[0]
        LINE_DEN_COEFF3 = LINE_DEN_COEFF
        LINE_DEN_COEFF3 = LINE_DEN_COEFF3.replace(" ", "")
        LINE_DEN_COEFF3 = LINE_DEN_COEFF3.replace('(', '')
        LINE_DEN_COEFF3 = LINE_DEN_COEFF3.replace(')', '')
        LINE_DEN_COEFF3 = LINE_DEN_COEFF3.replace('\n', '')
        LINE_DEN_COEFF3 = LINE_DEN_COEFF3.replace('\t', '')
        LINE_DEN_COEFF3 = LINE_DEN_COEFF3.replace(',', ' ')

        pat_SAMP_NUM_COEFF = re.compile(SAMP_NUM_COEFF1 + '(.*?)' + SAMP_NUM_COEFF2, re.S)
        result_SAMP_NUM_COEFF = pat_SAMP_NUM_COEFF.findall(buff)
        SAMP_NUM_COEFF = result_SAMP_NUM_COEFF[0]
        SAMP_NUM_COEFF3 = SAMP_NUM_COEFF
        SAMP_NUM_COEFF3 = SAMP_NUM_COEFF3.replace(" ", "")

        SAMP_NUM_COEFF3 = SAMP_NUM_COEFF3.replace('(', '')
        SAMP_NUM_COEFF3 = SAMP_NUM_COEFF3.replace(')', '')
        SAMP_NUM_COEFF3 = SAMP_NUM_COEFF3.replace('\n', '')
        SAMP_NUM_COEFF3 = SAMP_NUM_COEFF3.replace('\t', '')
        SAMP_NUM_COEFF3 = SAMP_NUM_COEFF3.replace(',', ' ')

        pat_SAMP_DEN_COEFF = re.compile(SAMP_DEN_COEFF1 + '(.*?)' + SAMP_DEN_COEFF2, re.S)
        result_SAMP_DEN_COEFF = pat_SAMP_DEN_COEFF.findall(buff)
        SAMP_DEN_COEFF = result_SAMP_DEN_COEFF[0]
        SAMP_DEN_COEFF3 = SAMP_DEN_COEFF
        SAMP_DEN_COEFF3 = SAMP_DEN_COEFF3.replace(" ", "")

        SAMP_DEN_COEFF3 = SAMP_DEN_COEFF3.replace('(', '')
        SAMP_DEN_COEFF3 = SAMP_DEN_COEFF3.replace(')', '')
        SAMP_DEN_COEFF3 = SAMP_DEN_COEFF3.replace('\n', '')
        SAMP_DEN_COEFF3 = SAMP_DEN_COEFF3.replace('\t', '')
        SAMP_DEN_COEFF3 = SAMP_DEN_COEFF3.replace(',', ' ')

    rpc = ['ERR_BIAS'+ERR_BIAS, 'ERR_RAND'+ERR_RAND, 'LINE_OFF'+LINE_OFF,
           'SAMP_OFF'+SAMP_OFF, 'LAT_OFF'+LAT_OFF, 'LONG_OFF'+LONG_OFF,
           'HEIGHT_OFF'+HEIGHT_OFF, 'LINE_SCALE'+LINE_SCALE, 'SAMP_SCALE'+SAMP_SCALE,
           'LAT_SCALE'+LAT_SCALE, 'LONG_SCALE'+LONG_SCALE, 'HEIGHT_SCALE'+HEIGHT_SCALE,
           'LINE_NUM_COEFF'+LINE_NUM_COEFF3,'LINE_DEN_COEFF'+LINE_DEN_COEFF3,
           'SAMP_NUM_COEFF'+SAMP_NUM_COEFF3,'SAMP_DEN_COEFF'+SAMP_DEN_COEFF3]
    #rpc = ['ERR BIAS=' + ERR_BIAS, 'ERR RAND=' + ERR_RAND, 'LINE OFF=' + LINE_OFF, 'SAMP OFF=' + SAMP_OFF,'LAT OFF=' + LAT_OFF, 'LONG OFF=' + LONG_OFF, 'HEIGHT OFF=' + HEIGHT_OFF, 'LINE SCALE=' + LINE_SCALE,'SAMP SCALE=' + SAMP_SCALE, 'LAT SCALE=' + LAT_SCALE, 'LONG SCALE=' + LONG_SCALE,'HEIGHT SCALE=' + HEIGHT_SCALE, 'LINE NUM COEFF=' + LINE_NUM_COEFF3, 'LINE DEN COEFF=' + LINE_DEN_COEFF3,'SAMP NUM COEFF=' + SAMP_NUM_COEFF3, 'SAMP DEN COEFF=' + SAMP_DEN_COEFF3]
    return rpc

# 使用 RPC 的几何校正
def geometric_correction(image_L1B_path, rpc_path, resolution, dem_path, output_dir):
    image_L2_name = os.path.basename(image_L1B_path).replace('L1B', 'L2')
    image_L2_path = os.path.join(output_dir, image_L2_name)
    
    # 读取rpc并嵌入dataset
    rpc = read_rpb(rpc_path)
    dataset = gdal.Open(image_L1B_path)
    dataset.SetMetadata(rpc, 'RPC')
    
    # 是否北半球
    is_north = 1 if os.path.basename(image_L2_path).split('_')[5][0] == 'N' else 0
    # 计算UTM区号
    zone = str(int(float(os.path.basename(image_L2_path).split('_')[4][1:])/6) + 31)
    zone = int('326' + zone) if is_north else int('327' + zone)
    dstSRS = osr.SpatialReference()
    dstSRS.ImportFromEPSG(zone)
    
    gdal.Warp(image_L2_path, dataset, dstSRS=dstSRS, 
              xRes=resolution, yRes=resolution, rpc=True,
              transformerOptions=["RPC_DEM="+dem_path])
    del dataset

# GF3号L1A级数据生产出L2级
def GF3_L1A_2_L2(image_path, qualifyValue1A, calibrationConst, rpc_path, resolution, dem_path, output_dir):
    image_name = os.path.basename(image_path)
    
    # 获取L1A单视复数产品值
    image = gdal.Open(image_path)
    IQ = image.ReadAsArray()
    
    # 获取复数中的实部I与虚部Q
    I = np.array(IQ[0, :, :], dtype='float32')
    Q = np.array(IQ[1, :, :], dtype='float32')
    
    # 多视处理（由复数数据得到强度数据）
    # 计算强度P与振幅A
    P = (I ** 2 + Q ** 2)
    
    # 辐射定标
    backscatter = 10 * np.log10(P * (qualifyValue1A / 32767) ** 2) - calibrationConst
    
    # # 高分三号卫星的等效噪声系数为-25dB
    # # 后向散射系数最小值对应于SAR传感器的等效噪声系数
    # # 考虑到部分GF3元文件中定标系数为空不可用，计算得到的后向散射系数为相对值，所以等效噪声系数暂不使用
    # equivalent_noise = -25
    
    # log(0)=-inf ,将inf赋值为最小值
    backscatter[np.isinf(-backscatter)] = np.nan
    backscatter[np.isnan(-backscatter)] = np.nanmin(backscatter)
    
    image_L1B_name = image_name.replace('L1A', 'L1B')
    image_L1B_path = os.path.join(output_dir, image_L1B_name)
    imwrite(backscatter, image_L1B_path)
    
    # 几何校正
    geometric_correction(image_L1B_path, rpc_path, resolution, dem_path, output_dir)

# 对不同极化方式数据进行L2级生成
def GF3_L1A_2_L2_batch(meta_path, image_paths, rpc_paths, resolution, dem_path, output_dir):
    qualifyValues, calibrationConsts = get_qualifyValue_calibrations(meta_path)
    for image_path, rpc_path, qualifyValue1A, calibrationConst in zip(image_paths, rpc_paths, qualifyValues, calibrationConsts):
        if image_path != None:
            image_name = os.path.basename(image_path)
            print(f"正在处理{image_name}.")
            if qualifyValue1A == "NULL":
                qualifyValue1A = np.nan
            else:
                qualifyValue1A = float(qualifyValue1A)
            if calibrationConst == "NULL":
                calibrationConst = 0
                print("注意: 元文件中定标系数缺失,以0作为定标系数计算后向散射系数相对值.")
            else:
                calibrationConst = float(calibrationConst)
            GF3_L1A_2_L2(image_path, qualifyValue1A, calibrationConst, rpc_path, resolution, dem_path, output_dir)
            
if __name__ == '__main__':
    
    dem_path = r"C:\setup\Exelis\ENVI53\data\GMTED2010.jp2"
    data_dir = r"E:\WangZhenQing\GF3_preprocess\GF3_KAS_FSII_030839_E113.5_N22.7_20220619_L1A_HHHV_L10006536542"
    output_dir = data_dir+'_output'
    
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
        
    meta_path, image_paths = get_meta_image_path(data_dir)
    resolution = get_resolution(meta_path)
    rpc_paths = get_rpc_path(data_dir)
    
    GF3_L1A_2_L2_batch(meta_path, image_paths, rpc_paths, resolution, dem_path, output_dir)