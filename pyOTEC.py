# -*- coding: utf-8 -*-
"""
Created on Tue Apr 27 11:16:02 2021

@author: jkalanger
"""

## Hello there, thank you for using pyOTEC. 
## With pyOTEC, you can create spatially and temporally resolved power generation profiles from ocean thermal energy conversion (OTEC)
## for any technically feasible system size and region.

## This is the main file and heart of pyOTEC. We try to document the code as clear and transparent as possible. Please refer to the paper 
## "TITLE PAPER" by Langer (2023) for further details and visualisations. If you use pyOTEC for your own research, please remember to cite the abovementioned
## paper. If you have any questions, please reach out to j.k.a.langer@tudelft.nl

import os
import time
import pandas as pd
import numpy as np

from parameters_and_constants import parameters_and_constants
from off_design_analysis import off_design_analysis
from HYCOM_download_and_processing import get_HYCOM_data,data_processing,load_temperatures

## Here we define the main function on which pyOTEC is based. The inputs are the studied_region, gross power output of the OTEC plant, and the cost level
## Please scroll down to the bottom for further details on the inputs.
   
def pyOTEC(studied_region,p_gross=-136000,cost_level='low_cost'):
    start = time.time()
    parent_dir = os.getcwd()      
    new_path = os.path.join(parent_dir,f'{studied_region}\\'.replace(" ","_"))
    
    ## create a new folder in which all downloaded and generated files will be stored 
    if os.path.isdir(new_path):
        pass
    else:
        os.mkdir(new_path)
    
    ## Here, we load all technical and economic inputs used for the analysis
    inputs = parameters_and_constants(p_gross,cost_level)
    
    ## If the seawater temperature data does not exist in the results folder, it is downloaded here. 
    files = get_HYCOM_data(cost_level,inputs,studied_region,new_path)
    
    print('\n++ Processing HYCOM data ++\n')   
    
    ## Here, we load all HYCOM points that could represent a site for an OTEC plant
    ## These points are inside the Exclusive Economic Zone (EEZ) of a country/territory and outside of Marine Protected Areas (MPA)
    ## Below, the sites are filtered for water depth thresholds defined by the user, e.g. a range of 1000 to 3000 m  depth
    
    sites_hycom = pd.read_csv('HYCOM_points_with_properties.csv',delimiter=';')
    sites_hycom = sites_hycom[(sites_hycom['region']==studied_region) & (sites_hycom['water_depth'] <= inputs['min_depth']) & (sites_hycom['water_depth'] >= inputs['max_depth'])]   
    sites_hycom = sites_hycom.sort_values(by=['longitude','latitude'],ascending=True)
    
    ## After downloading the raw HYCOM data, we process the data further. We define the filenames and check whether the files already exist in the results folder
    ## If the files already exist, we merely have to load them. If they don't exist yet, they are generated now. WW stands for Warm Water, CW stands for Cold Water
    depth_WW = inputs['length_WW_inlet']
    depth_CW = inputs['length_CW_inlet']
    
    h5_file_WW = os.path.join(new_path, f'T_{depth_WW}m_2011_{studied_region}.h5'.replace(" ","_"))
    h5_file_CW = os.path.join(new_path, f'T_{depth_CW}m_2011_{studied_region}.h5'.replace(" ","_"))
    
    if os.path.isfile(h5_file_CW):
        T_CW_profiles, T_CW_design, coordinates_CW, timestamp, inputs, nan_columns_CW = load_temperatures(h5_file_CW, inputs)
        print(f'{h5_file_CW} already exist. No processing necessary.')
    else:
        T_CW_profiles, T_CW_design, coordinates_CW, timestamp, inputs, nan_columns_CW = data_processing(files[int(len(files)/2):int(len(files))],sites_hycom,inputs,studied_region,new_path,'CW')
    
    if os.path.isfile(h5_file_WW):
        T_WW_profiles, T_WW_design, coordinates_WW, timestamp, inputs, nan_columns_WW = load_temperatures(h5_file_WW, inputs)
        print(f'{h5_file_WW} already exist. No processing necessary.')
    else:
        T_WW_profiles, T_WW_design, coordinates_WW, timestamp, inputs, nan_columns_WW = data_processing(files[0:int(len(files)/2)],sites_hycom,inputs,studied_region,new_path,'WW',nan_columns_CW)
    
    ## After data processing, we move on to the actual technical and economic analysis. The output of the code below are all OTEC plants designed for best
    ## economic off-design performance across the studied region. The results are stored as extensive h5 files that show the plant characteristics and time
    ## series data for their technical performance    

    otec_plants = off_design_analysis(T_WW_design,T_CW_design,T_WW_profiles,T_CW_profiles,inputs,coordinates_CW,timestamp,studied_region,new_path,cost_level)  
    
    ## If the user is more interested in the "big-picture" results, we generate a simple csv file that shows the locations of all analysed plants as well as
    ## key results like nominal and actual net power output, LCOE, and CAPEX
    
    sites = pd.DataFrame()
    sites['longitude'] = coordinates_CW[:,0]
    sites['latitude'] = coordinates_CW[:,1]
    sites['p_net_nom'] = -otec_plants['p_net_nom'].T/1000
    sites['AEP'] = -np.sum(otec_plants['p_net'].T)*3/1000000
    sites['CAPEX'] = otec_plants['CAPEX'].T/1000000
    sites['LCOE'] = otec_plants['LCOE'].T
    
    date_start = inputs['date_start']
    p_gross = inputs['p_gross']
    
    sites.to_csv(new_path + f'OTEC_sites_{studied_region}_{date_start[0:4]}_{-p_gross/1000}_MW_{cost_level}.csv'.replace(" ","_"),index=True,float_format='%.3f')
    
    end = time.time()
    print('Total runtime: ' + str(round((end-start)/60,2)) + ' minutes.')
    
    return otec_plants, sites

if __name__ == "__main__":
    
    ## Please enter the region that you want to analyse. Please check the file "HYCOM_download_ranges_per_region.csv"
    ## for the regions that are covered by pyOTEC.
    
    studied_region = input('++ Setting up HYCOM download ++\n\nEnter the region to be analysed.  ')
    
    ## Please enter the gross power output of the OTEC plants. pyOTEC will determined the economically best system designs for on-design (nominal) and 
    ## off-design (operational) conditions. Make sure that you enter the power output in [kW] as a negative number. For example, if the user wants to size a
    ## 136 MW_gross system, the user needs to enter -136000
    
    p_gross = int(input('\nPlease enter the gross power output in [kW] as a negative number (default: -136000 kW).  '))
    
    ## OTEC's costs are still uncertain today and estimations in literature can vary significantly.
    ## Therefore, we offer two cost models from which the user can choose: "low_cost" and "high_cost"
    
    cost_level = 'low_cost'
    
    otec_plants, sites = pyOTEC(studied_region,p_gross,cost_level)