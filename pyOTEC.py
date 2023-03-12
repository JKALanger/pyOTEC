# -*- coding: utf-8 -*-
"""
Created on Tue Apr 27 11:16:02 2021

@author: jkalanger
"""

import os
import time
import pandas as pd
import numpy as np

from parameters_and_constants import parameters_and_constants
from off_design_analysis import off_design_analysis
from HYCOM_download_and_processing import get_HYCOM_data,data_processing,load_temperatures
   
def pyOTEC():
    start = time.time()
    parent_dir = os.getcwd()
    
    ## OTEC's costs are still uncertain today and estimations in literature can vary significantly.
    ## Therefore, we offer two cost models from which the user can choose: "low_cost" and "high_cost"
    
    cost_level = 'low_cost'
    
    ## Please enter the region that you want to analyse. Please check the file "HYCOM_download_ranges_per_region.csv"
    ## for the regions that are covered by pyOTEC.
    
    studied_region = input('++ Setting up HYCOM download ++\n\nEnter the region to be analysed.  ')
    
    new_path = os.path.join(parent_dir,f'{studied_region}\\')
    
    if os.path.isdir(new_path):
        pass
    else:
        os.mkdir(new_path)
    
    inputs = parameters_and_constants(cost_level)
    depth_WW = inputs['length_WW_inlet']
    depth_CW = inputs['length_CW_inlet']
    
    files = get_HYCOM_data(cost_level,inputs,studied_region,new_path)
    
    print('\n++ Processing HYCOM data ++\n')   
    
    sites_df = pd.read_csv('HYCOM_points_with_properties.csv',delimiter=';')
    sites_df = sites_df[(sites_df['region']==studied_region) & (sites_df['water_depth'] <= inputs['min_depth']) & (sites_df['water_depth'] >= inputs['max_depth'])]   
    sites_df = sites_df.sort_values(by=['longitude','latitude'],ascending=True)
    
    h5_file_WW = os.path.join(new_path, f'T_{depth_WW}m_2011_{studied_region}.h5')
    h5_file_CW = os.path.join(new_path, f'T_{depth_CW}m_2011_{studied_region}.h5')
    
    if os.path.isfile(h5_file_CW):
        T_CW_profiles, T_CW_design, coordinates_CW, timestamp, inputs, nan_columns_CW = load_temperatures(h5_file_CW, inputs)
        print(f'T_{depth_CW}m_2011_{studied_region}.h5 already exist. No processing necessary.')
    else:
        T_CW_profiles, T_CW_design, coordinates_CW, timestamp, inputs, nan_columns_CW = data_processing(files[int(len(files)/2):int(len(files))],sites_df,inputs,studied_region,new_path,'CW')
    
    if os.path.isfile(h5_file_WW):
        T_WW_profiles, T_WW_design, coordinates_WW, timestamp, inputs, nan_columns_WW = load_temperatures(h5_file_WW, inputs)
        print(f'T_{depth_WW}m_2011_{studied_region}.h5 already exist. No processing necessary.')
    else:
        T_WW_profiles, T_WW_design, coordinates_WW, timestamp, inputs, nan_columns_WW = data_processing(files[0:int(len(files)/2)],sites_df,inputs,studied_region,new_path,'WW',nan_columns_CW)
         
    otec_plants = off_design_analysis(T_WW_design,T_CW_design,T_WW_profiles,T_CW_profiles,inputs,coordinates_CW,timestamp,studied_region,new_path,cost_level)  
    
    sites = pd.DataFrame()
    sites['longitude'] = coordinates_CW[:,0]
    sites['latitude'] = coordinates_CW[:,1]
    sites['p_net_nom'] = -otec_plants['p_net_nom'].T/1000
    sites['AEP'] = -np.sum(otec_plants['p_net'].T)*3/1000000
    sites['CAPEX'] = otec_plants['CAPEX'].T/1000000
    sites['LCOE'] = otec_plants['LCOE'].T
    
    date_start = inputs['date_start']
    p_gross = inputs['p_gross']
    
    sites.to_csv(new_path + f'OTEC_sites_{studied_region}_{date_start[0:4]}_{-p_gross/1000}_MW_{cost_level}.csv',index=True,float_format='%.3f')
    
    end = time.time()
    print('Total runtime: ' + str(round((end-start)/60,2)) + ' minutes.')
    
    return otec_plants, sites_df

if __name__ == "__main__":
    otec_plants, sites_df = pyOTEC()