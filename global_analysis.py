# -*- coding: utf-8 -*-
"""
Created on Tue Apr 27 11:16:02 2021

@author: jkalanger
"""

import os
import time
import pandas as pd
import numpy as np
import platform

from parameters_and_constants import parameters_and_constants
from off_design_analysis import off_design_analysis
from CMEMS_download_and_processing import download_data,data_processing,load_temperatures
   
def pyOTEC(studied_region,p_gross=-136000,cost_level='low_cost'):
    start = time.time()
    parent_dir = os.getcwd() + 'Data_Results/'
    
    if platform.system() == 'Windows':
        new_path = os.path.join(parent_dir,f'{studied_region}\\'.replace(" ","_"))
    else :
        new_path = os.path.join(parent_dir,f'{studied_region}/'.replace(" ","_"))
    
    if os.path.isdir(new_path):
        pass
    else:
        os.mkdir(new_path)
        
    inputs = parameters_and_constants(p_gross,cost_level,'CMEMS')
    year = inputs['date_start'][0:4]  
    
    # if os.path.isfile(new_path+f'net_power_profiles_{studied_region}_{year}__{-p_gross/1000}_MW_{cost_level}.csv'.replace(" ","_")):
    #     print(f'{studied_region} already analysed.')
    # else:
  
        
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
    p_net_profile.to_csv(new_path + f'net_power_profiles_{studied_region}_{year}__{-p_gross/1000}_MW_{cost_level}.csv'.replace(" ","_"),index=True)
    
    end = time.time()
    print('Total runtime: ' + str(round((end-start)/60,2)) + ' minutes.')
    
    return otec_plants, sites_df

if __name__ == "__main__":
    
    unique_regions = pd.read_csv('HYCOM_download_ranges_per_region.csv',delimiter=';',encoding='latin-1').drop_duplicates(subset=['region'])   
    regions = list(unique_regions['region'])   
    demand = list(unique_regions['demand'])
    cost_level = 'low_cost'
    
    for index,region in enumerate(regions):
        studied_region = region
        if np.isnan(demand[index]) or demand[index] == 0:
            continue
        elif -demand[index]*1000000000/8760 < -136000:
            p_gross = -136000
        else:
            p_gross = int(-demand[index]*1000000000/8760)
        pyOTEC(studied_region,p_gross,cost_level)
