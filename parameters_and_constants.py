# -*- coding: utf-8 -*-
"""
Created on Wed Feb 22 15:28:39 2023

@author: jkalanger
"""

import pandas as pd
import numpy as np

def parameters_and_constants(p_gross=-136000,cost_level='low_cost',data='CMEMS'):
    
    
    if data == 'HYCOM':
        ## Setup for HYCOM seawater resource data download
        glb = 'GLBu0.08'  
        horizontal_stride = 3      
        time_origin = '2000-01-01 00:00:00' 
        
        year = 2011           
        date_start = '2011-01-01 00:00:00'      
        date_end = '2011-12-31 21:00:00'
        time_stride = 1
            
        # depths = [0,2,4,6,8,10,12,15,20,25,30,35,40,45,50,60,70,80,90,100,125,150,200,250,300,350,400,500,600,700,800,900,1000,1250,1500,2000,2500,3000,4000,5000]
    else:
        ## Setup for CMEMS data download using motu
    
        time_origin = '1950-01-01 00:00:00'
        
        year = 2020          
        date_start = '2020-01-01 00:00:00'      
        date_end = '2020-12-31 21:00:00'
        
    t_resolution = '24H'    

    ## Physical properties
    
    rho_NH3 = 625       # density of ammonia in kg/m3
    rho_WW = 1024       # density of warm seawater in kg/m3
    rho_CW = 1027       # density of cold seawater in kg/m3
    
    cp_water = 4.0      # specific heat capacity of seawater in kJ/kgK
    
    fluid_properties = [rho_NH3,rho_WW,rho_CW,cp_water]
    
    roughness_pipe = 0.0053     # roughness of pipe in m
    
    if cost_level == 'low_cost':        
        rho_pipe = 995               # density of HDPE pipe in kg/m3
        
    elif cost_level == 'high_cost':
        rho_pipe = 1016              # density of FRP sandwich pipe in kg/m3
    else:
        raise ValueError('Invalid cost level. Valid inputs are "low_cost" and "high_cost"')
    
    pipe_material = [rho_pipe,roughness_pipe]
        
    min_depth = -600   # minimum depth in m
    max_depth = -3000   # maximum depth in m (restricted by technical mooring limitations)
    
    threshold_AC_DC = 50    # threshold in km at which DC cables are chosen over AC cables
    
    ## Temperatures and deltas
    
    T_pinch_WW = 1      # pinch-point temperature difference evaporator in degree Celsius
    T_pinch_CW = 1      # pinch-point temperature difference condenser in degree Celsius
 
    # the following parameters have to be multiplied by factor 10 because python cannot loop with floats
 
    del_T_WW_min = 2*10    # minimum temperature difference between warm seawater inlet and outlet 
    del_T_CW_min = 2*10    # minimum temperature difference between cold seawater inlet and outlet
    del_T_WW_max = 5*10   # maximum temperature difference between warm seawater inlet and outlet 
    del_T_CW_max = 5*10    # maximum temperature difference between cold seawater inlet and outlet
    
    interval_WW = int(0.5*10)    # interval used to loop between minimum and maximum warm seawater temperature differences
    interval_CW = int(0.5*10)    # interval used to loop between minimum and maximum cold seawater temperature differences
    
    del_T_for_looping = [del_T_WW_min,
                         del_T_CW_min,
                         del_T_WW_max,
                         del_T_CW_max,
                         interval_WW,
                         interval_CW]
    
    temperatures = [T_pinch_WW,
                    T_pinch_CW,
                    del_T_for_looping]
    
    ## Heat exchange coefficients
    
    U_evap = 4.5        # nominal overall heat tranfer coefficient evaporator in kW/m2K
    U_cond = 3.5        # nominal overall heat tranfer coefficient condenser in kW/m2K
    
    U = [U_evap,U_cond]
    
    ## Seawater pipes
    
    length_WW_inlet = 21.598819732666016    # warm seawater inlet pipe length in m, according to Copernicus dataset depth
    length_WW_outlet = 60   # warm seawater outlet pipe length in m
    length_WW = length_WW_inlet + length_WW_outlet      # total length of warm seawater pipe pair 
    length_CW_inlet = 1062.43994140625  # cold seawater inlet pipe length in m, according to Copernicus dataset depth
    # [643.5667724609375,763.3331298828125,902.3392944335938,1062.43994140625]
    length_CW_outlet = 60  # cold seawater outlet pipe length in m
    length_CW = length_CW_inlet + length_CW_outlet      # total length of cold seawater pipe pair 
    thickness = 0.09        # pipe thickness in m 
    K_L = 100               # pressure drop coefficient for both evaporator and condenser (unitless)
    u_pipes = 2.1          # nominal flow velocity in seawater pipes in m/s
    u_HX = u_pipes/2     # nominal flow velocity in heat exchangers in m/s
    pressure_drop_nom = 100     # maximum pressure in 
    max_d = 8               # maximum inner seawater pipe diameter in m
    max_p = 100             # maximum pressure drop in kPa
    
    pipe_properties = [length_WW,
                       length_CW,
                       thickness,
                       K_L,
                       u_pipes,
                       u_HX,
                       pressure_drop_nom,
                       max_d,
                       max_p]
    
    ## Efficiencies (excluding seawater pumps)
    
    eff_isen_turb = 0.82        # isentropic turbine efficiency
    eff_isen_pump = 0.8         # isentropic ammonia pump efficiency
    
    eff_pump_NH3_mech = 0.95    # mechanical ammonia pump efficiency
    
    eff_turb_el = 0.95          # electric turbine efficiency
    eff_turb_mech = 0.95        # mechanical turbine efficiency
    
    eff_trans = 0               # dummy value and is updated in function "data_processing"                         
    
    eff_hyd = 0.8           # hydraulic efficiency of seawater pumps
    eff_el = 0.95           # electric efficiency of seawater pumps
    
    efficiencies = [eff_isen_turb,
                    eff_isen_pump,
                    eff_pump_NH3_mech,
                    eff_turb_el,
                    eff_turb_mech,
                    eff_trans,
                    eff_hyd,
                    eff_el]
    
    ## Economic assumptions
    
    lifetime = 30
    discount_rate = 0.1
    crf = discount_rate*(1+discount_rate)**lifetime/((1+discount_rate)**lifetime-1) 
    
    availability_factor = 8000/8760 
    
    economic_inputs = [lifetime,
                       crf,
                       discount_rate,
                       availability_factor]
       
    return locals()