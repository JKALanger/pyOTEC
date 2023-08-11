# -*- coding: utf-8 -*-
"""
Created on Tue Apr 27 11:16:02 2021

@author: jkalanger
"""

## Hello there, thank you for using pyOTEC. 
## With pyOTEC, you can create spatially and temporally resolved power generation profiles for any technically feasible system size and region.

## This is the main file used to generate 3-hourly power production profiles for ocean thermal energy conversion (OTEC). We try to document the code as
## clear and transparent as possible. Please refer to the paper "TITLE PAPER" by Langer (2023) for further details and visualisations. If you find pyOTEC
## useful, please cite the abovementioned paper in your work. If you have any questions, please reach out to j.k.a.langer@tudelft.nl

import os
import time
import pandas as pd
import numpy as np

from parameters_and_constants import parameters_and_constants
from off_design_analysis import off_design_analysis
from CMEMS_download_and_processing import download_data,data_processing,load_temperatures

## Here we define the main function on which pyOTEC is based. The inputs are the studied_region, gross power output of the OTEC plant, and the cost level
## Please scroll down to the bottom for further details on the inputs.
   
def pyOTEC(studied_region,p_gross=-136000,cost_level='low_cost'):
    start = time.time()
    parent_dir = os.getcwd()
    
    new_path = os.path.join(parent_dir,f'{studied_region}\\'.replace(" ","_"))
    
    if os.path.isdir(new_path):
        pass
    else:
        os.mkdir(new_path)
        
    inputs = parameters_and_constants(p_gross,cost_level,'CMEMS')
    year = inputs['date_start'][0:4]   
        
    depth_WW = inputs['length_WW_inlet']
    depth_CW = inputs['length_CW_inlet']
      
    files = download_data(cost_level,inputs,studied_region,new_path)
    
    print('\n++ Processing seawater temperature data ++\n')   
    
    sites_df = pd.read_csv('CMEMS_points_with_properties.csv',delimiter=';',encoding='latin-1')
    sites_df = sites_df[(sites_df['region']==studied_region) & (sites_df['water_depth'] <= inputs['min_depth']) & (sites_df['water_depth'] >= inputs['max_depth'])]   
    sites_df = sites_df.sort_values(by=['longitude','latitude'],ascending=True)
    
    h5_file_WW = os.path.join(new_path, f'T_{round(depth_WW,0)}m_{year}_{studied_region}.h5'.replace(" ","_"))
    h5_file_CW = os.path.join(new_path, f'T_{round(depth_CW,0)}m_{year}_{studied_region}.h5'.replace(" ","_"))
    
    if os.path.isfile(h5_file_CW):
        T_CW_profiles, T_CW_design, coordinates_CW, id_sites, timestamp, inputs, nan_columns_CW = load_temperatures(h5_file_CW, inputs)
        print(f'{h5_file_CW} already exist. No processing necessary.')
    else:
        T_CW_profiles, T_CW_design, coordinates_CW, id_sites, timestamp, inputs, nan_columns_CW = data_processing(files[int(len(files)/2):int(len(files))],sites_df,inputs,studied_region,new_path,'CW')
    
    if os.path.isfile(h5_file_WW):
        T_WW_profiles, T_WW_design, coordinates_WW, id_sites, timestamp, inputs, nan_columns_WW = load_temperatures(h5_file_WW, inputs)
        print(f'{h5_file_WW} already exist. No processing necessary.')
    else:
        T_WW_profiles, T_WW_design, coordinates_WW, id_sites, timestamp, inputs, nan_columns_WW = data_processing(files[0:int(len(files)/2)],sites_df,inputs,studied_region,new_path,'WW',nan_columns_CW)
         
    otec_plants = off_design_analysis(T_WW_design,T_CW_design,T_WW_profiles,T_CW_profiles,inputs,coordinates_CW,timestamp,studied_region,new_path,cost_level)  
    
    sites = pd.DataFrame()
    sites.index = np.squeeze(id_sites)
    sites['longitude'] = coordinates_CW[:,0]
    sites['latitude'] = coordinates_CW[:,1]
    sites['p_net_nom'] = -otec_plants['p_net_nom'].T/1000
    sites['AEP'] = -np.mean(otec_plants['p_net'],axis=0)*8760/1000000
    sites['CAPEX'] = otec_plants['CAPEX'].T/1000000
    sites['LCOE'] = otec_plants['LCOE'].T
    sites['Configuration'] = otec_plants['Configuration'].T
    sites['T_WW_min'] = T_WW_design[0,:]
    sites['T_WW_med'] = T_WW_design[1,:]
    sites['T_WW_max'] = T_WW_design[2,:]
    sites['T_CW_min'] = T_CW_design[2,:]
    sites['T_CW_med'] = T_CW_design[1,:]
    sites['T_CW_max'] = T_CW_design[0,:]
    
    sites = sites.dropna(axis='rows')

    p_net_profile = pd.DataFrame(np.mean(otec_plants['p_net'],axis=1),columns=['p_net'],index=timestamp)
    
    p_gross = inputs['p_gross']
    
    sites.to_csv(new_path + f'OTEC_sites_{studied_region}_{year}_{-p_gross/1000}_MW_{cost_level}.csv'.replace(" ","_"),index=True, index_label='id',float_format='%.3f')
    p_net_profile.to_csv(new_path + f'net_power_profiles_{studied_region}_{year}_{-p_gross/1000}_MW_{cost_level}.csv'.replace(" ","_"),index=True)
    
    end = time.time()
    print('Total runtime: ' + str(round((end-start)/60,2)) + ' minutes.')
    
    return otec_plants, sites_df

if __name__ == "__main__":
    
    ## Please enter the region that you want to analyse. Please check the file "download_ranges_per_region.csv"
    ## for the regions that are covered by pyOTEC.
    
    studied_region = input('++ Setting up seawater temperature data download ++\n\nEnter the region to be analysed.  ')
    
    ## Please enter the gross power output of the OTEC plants. pyOTEC will determined the economically best system designs for on-design (nominal) and 
    ## off-design (operational) conditions. Make sure that you enter the power output in [kW] as a negative number. For example, if the user wants to size a
    ## 136 MW_gross system, the user needs to enter -136000
    
    p_gross = int(input('\nPlease enter the gross power output in [kW] as a negative number (default: -136000 kW).  '))
    
    ## OTEC's costs are still uncertain today and estimations in literature can vary significantly.
    ## Therefore, we offer two cost models from which the user can choose: "low_cost" and "high_cost"
    
    cost_level = 'low_cost'
    
    otec_plants, sites = pyOTEC(studied_region,p_gross,cost_level)