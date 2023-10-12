#%%
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 27 11:16:02 2021

@author: jkalanger
"""

## Hello there, thank you for using pyOTEC. 
## With pyOTEC, you can create spatially and temporally resolved power generation profiles for any technically feasible system size and region.

## This is the main file used to generate 3-hourly power production profiles for ocean thermal energy conversion (OTEC). We try to document the code as
## clear and transparent as possible. Please refer to the paper "The global economic potential of ocean thermal energy conversion" by Langer et al. (2023) for further details and visualisations. If you find pyOTEC
## useful, please cite the abovementioned paper in your work. If you have any questions, please reach out to j.k.a.langer@tudelft.nl

import os
import time
import pandas as pd
import numpy as np
import platform
import matplotlib.pyplot as plt

import CMEMS_download_and_processing as Cdp
import parameters_and_constants as pc
import off_design_analysis as oda
import create_plots as cp
import cost_analysis as co
from scipy.optimize import curve_fit


## Here we define the main function on which pyOTEC is based. The inputs are the studied_region, gross power output of the OTEC plant, and the cost level
## Please scroll down to the bottom for further details on the inputs.
   
def pyOTEC(studied_region,p_gross=-136000,cost_level='low_cost'):
    start = time.time()
    parent_dir = os.getcwd() + '/Data_Results/'
    inputs = pc.parameters_and_constants(p_gross,cost_level,'CMEMS')
    year = inputs['date_start'][0:4]
    
    if platform.system() == 'Windows':
        dl_path = os.path.join(parent_dir,f'{studied_region}\\'.replace(" ","_")) 
        new_path = dl_path + f'{studied_region}_{year}_{-p_gross/1000}_MW_{cost_level}\\'.replace(" ","_")
    else :
        dl_path = os.path.join(parent_dir,f'{studied_region}/'.replace(" ","_")) 
        new_path = dl_path+ f'{studied_region}_{year}_{-p_gross/1000}_MW_{cost_level}/'.replace(" ","_")
    
    if os.path.isdir(new_path):
        pass
    else:
        os.makedirs(new_path)
        

        
    depth_WW = inputs['length_WW_inlet']
    depth_CW = inputs['length_CW_inlet']
      
    files = Cdp.download_data(cost_level,inputs,studied_region,dl_path)
    
    print('\n++ Processing seawater temperature data ++\n')   
    
    sites_df = pd.read_csv('CMEMS_points_with_properties.csv',delimiter=';')
    sites_df = sites_df[(sites_df['region']==studied_region) & (sites_df['water_depth'] <= inputs['min_depth']) & (sites_df['water_depth'] >= inputs['max_depth'])]   
    sites_df = sites_df.sort_values(by=['longitude','latitude'],ascending=True)
    
  
    h5_file_WW = os.path.join(new_path, f'T_{round(depth_WW,0)}m_{year}_{studied_region}.h5'.replace(" ","_"))
    h5_file_CW = os.path.join(new_path, f'T_{round(depth_CW,0)}m_{year}_{studied_region}.h5'.replace(" ","_"))
    
    if os.path.isfile(h5_file_CW):
        T_CW_profiles, T_CW_design, coordinates_CW, id_sites, timestamp, inputs, nan_columns_CW = Cdp.load_temperatures(h5_file_CW, inputs)
        print(f'{h5_file_CW} already exist. No processing necessary.')
    else:
        T_CW_profiles, T_CW_design, coordinates_CW, id_sites, timestamp, inputs, nan_columns_CW = Cdp.data_processing(files[int(len(files)/2):int(len(files))],sites_df,inputs,studied_region,new_path,'CW')
    if os.path.isfile(h5_file_WW):
        T_WW_profiles, T_WW_design, coordinates_WW, id_sites, timestamp, inputs, nan_columns_WW = Cdp.load_temperatures(h5_file_WW, inputs)
        print(f'{h5_file_WW} already exist. No processing necessary.')
    else:
        T_WW_profiles, T_WW_design, coordinates_WW, id_sites, timestamp, inputs, nan_columns_WW = Cdp.data_processing(files[0:int(len(files)/2)],sites_df,inputs,studied_region,new_path,'WW',nan_columns_CW)
         
    otec_plants,capex_opex_comparison = oda.off_design_analysis(T_WW_design,T_CW_design,T_WW_profiles,T_CW_profiles,inputs,coordinates_CW,timestamp,studied_region,new_path,cost_level)  
    
    sites = pd.DataFrame()
    sites.index = np.squeeze(id_sites)
    sites['longitude'] = coordinates_CW[:,0]
    sites['latitude'] = coordinates_CW[:,1]
    sites['p_net_nom'] = -otec_plants['p_net_nom'].T/1000
    sites['AEP'] = -np.nanmean(otec_plants['p_net'],axis=0)*8760/1000000
    sites['CAPEX'] = otec_plants['CAPEX'].T/1000000
    sites['LCOE'] = otec_plants['LCOE'].T
    sites['Configuration'] = otec_plants['Configuration'].T
    sites['T_WW_min'] = T_WW_design[0,:]
    sites['T_WW_med'] = T_WW_design[1,:]
    sites['T_WW_max'] = T_WW_design[2,:]
    sites['T_CW_min'] = T_CW_design[2,:]
    sites['T_CW_med'] = T_CW_design[1,:]
    sites['T_CW_max'] = T_CW_design[0,:]
    
    
    pipe = pd.DataFrame()
    pipe['d_pipes_CW']=otec_plants['d_pipes_CW']
    pipe['num_pipes_CW']=otec_plants['num_pipes_CW']
    pipe['m_pipes_CW']=otec_plants['m_pipes_CW']
    pipe['A_pipes_CW']=otec_plants['A_pipes_CW']
    
    pipe.to_csv(new_path + f'CWP_details_{studied_region}_{year}_{-p_gross/1000}_MW_{cost_level}.csv'.replace(" ","_"),index=True, index_label='id',float_format='%.3f')
    
    
    #prendre en compte la localisation pour le calcul du transport de la conduite
    
    sites = sites.dropna(axis='rows')

    p_net_profile = pd.DataFrame(np.mean(otec_plants['p_net'],axis=1),columns=['p_net'],index=timestamp)
    
    p_gross = inputs['p_gross']
    
    sites.to_csv(new_path + f'OTEC_sites_{studied_region}_{year}_{-p_gross/1000}_MW_{cost_level}.csv'.replace(" ","_"),index=True, index_label='id',float_format='%.3f',sep=';')
    p_net_profile.to_csv(new_path + f'net_power_profiles_{studied_region}_{year}_{-p_gross/1000}_MW_{cost_level}.csv'.replace(" ","_"),index=True,sep=';')
    
    cost_dict = cp.plot_capex_opex(new_path,capex_opex_comparison,sites,p_gross,studied_region)
    #enregistrer ce résultat afin qu'on puisse l'utiliser pour comparer les LCOE etc pour différentes puissances ou différentes hypothèses de calculs (ex: épaisseur de tuyau)
    eco = pd.DataFrame.from_dict(cost_dict)
    eco.to_csv(new_path + f'eco_details_{studied_region}_{year}_{-p_gross/1000}_MW_{cost_level}.csv'.replace(" ","_"),index=True, index_label='Configuration',float_format='%.3f',sep=';')
    
    end = time.time()
    print('Total runtime: ' + str(round((end-start)/60,2)) + ' minutes.')
    
    # co.extract_costs_at_study_location(sites,capex_opex_comparison,user_lon=55.25,user_lat=-20.833)s
    
    return otec_plants, sites_df,capex_opex_comparison,cost_dict

if __name__ == "__main__":
    
    Cdp.save_credentials()
    ## Please enter the region that you want to analyse. Please check the file "download_ranges_per_region.csv"
    ## for the regions that are covered by pyOTEC.
    
    studied_region = "Reunion" #Mayotte"#"Aruba"# "Reunion"    # input('++ Setting up seawater temperature data download ++\n\nEnter the region to be analysed.  ')
    
    ## Please enter the gross power output of the OTEC plants. pyOTEC will determined the economically best system designs for on-design (nominal) and 
    ## off-design (operational) conditions. Make sure that you enter the power output in [kW] as a negative number. For example, if the user wants to size a
    ## 136 MW_gross system, the user needs to enter -136000
    
    p_gross = -3100 #int(input('\nPlease enter the gross power output in [kW] as a negative number (default: -136000 kW).  '))
    
    # OTEC's costs are still uncertain today and estimations in literature can vary significantly.
    # Therefore, we offer two cost models from which the user can choose: "low_cost" and "high_cost"
    
    cost_level = 'low_cost'
    otec_plants, sites,capex_opex_comparison,cost_dict = pyOTEC(studied_region,p_gross,cost_level)
    
    
    # list_p_gross=[-3000,-6500,-10000,-15000,-25000,-40000,-60000,-85000,-115000]
    # # list_p_gross=[-3000,-6500]
    # all_LCOE=[]
    # for p_gross in list_p_gross:
    #     otec_plants, sites,capex_opex_comparison,cost_dict = pyOTEC(studied_region,p_gross,cost_level)
    #     all_LCOE.append(cost_dict['LCOE'][4])
        
    
    # p_plot=[-i for i in list_p_gross]
    # # Fit a quadratic curve to your data
    # # degree = 3  # Degree of the polynomial (cubic)
    # # coefficients = np.polyfit(p_plot, all_LCOE, degree)

    # def exponential_decay(x, a, k, b):
    #     return a * np.exp(-k * x) + b
    
    # def func_powerlaw(x, m, c, c0):
    #     return c0 + x**m * c

    # p0 = (1.,1.e-5,20) # starting search koefs
    
    # # Perform the curve fit
    # popt, _ = curve_fit(exponential_decay, p_plot, all_LCOE,p0)
    
    # sol1 = curve_fit(func_powerlaw, p_plot, all_LCOE, maxfev=2000 )
    # sol2 = curve_fit(func_powerlaw, p_plot, all_LCOE, p0 = np.asarray([-1,10**5,0]))

    # # popt contains the estimated parameters a and b
    # a_fit, k_fit, b_fit = popt
    
    # x_fit = np.linspace(min(p_plot), max(p_plot), 100)
    # y_fit = exponential_decay(x_fit, a_fit, k_fit, b_fit)

    # y1=func_powerlaw(p_plot,sol1)
    # y2=func_powerlaw(p_plot,sol2)
    
    # plt.figure()
    # plt.scatter(p_plot, all_LCOE, label='Scatter Points')
    # plt.plot(x_fit, y_fit, label='Fit. func: $f(x) = %.3f e^{%.3f x} %+.3f$' % (a_fit, k_fit, b_fit), color='red')
    # # plt.plot(x_fit,y1)
    # # plt.plot(x_fit,y2)
    # plt.xlabel('Puissance brute(kW)_Mayotte')
    # plt.ylabel('LCOE(ct/kWh)')
    # plt.legend()
    # plt.savefig('scatter_and_parabola.png',dpi=200)
    # plt.close()
        
        
    # #enregistrer pour chaque configuration dans un fichier 
    # #pouvoir lire les fichiers ensuite pour faire les plots
