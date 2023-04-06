# -*- coding: utf-8 -*-
"""
Created on Wed Feb 22 11:57:49 2023

@author: jkalanger
"""

import numpy as np

def pressure_drop(T_water_ts,u_water_ts,d_pipes,rho_water,roughness_pipe,length,K_L,u_HX):
    
    dyn_visc = 0.000000344285714*T_water_ts**2-0.000047107142857*T_water_ts+0.001766642857143        
    Re = u_water_ts*rho_water*d_pipes/dyn_visc                     
    f = 0.25/(np.log10((roughness_pipe/d_pipes)/3.7+5.74/(Re**0.9))**2)        
   
    p_drop = ((f*rho_water*length/d_pipes*0.5*u_water_ts**2)+(K_L*rho_water*0.5*u_HX**2))/1000
    
    return p_drop

def saturation_pressures_and_temperatures(T_WW_in,T_CW_in,del_T_WW,del_T_CW,inputs):

    T_evap = np.round(T_WW_in - del_T_WW - inputs['T_pinch_WW'],1)
    T_cond = np.round(T_CW_in + del_T_CW + inputs['T_pinch_CW'],1)
    
    infeasible_T = np.where(T_evap <= T_cond,1,0)
    
    T_cond[infeasible_T==1] = np.nan
    T_evap[infeasible_T==1] = np.nan
    
    p_evap = 0.00002196*T_evap**3+0.00193103*T_evap**2+0.1695763*T_evap+4.25739601
    p_cond = 0.00002196*T_cond**3+0.00193103*T_cond**2+0.1695763*T_cond+4.25739601
    
    return T_evap,T_cond,p_evap,p_cond

def enthalpies_entropies(p_evap,p_cond,inputs):
      
    eff_isen_turb = inputs['eff_isen_turb']
    
    # Enthalpy and Entropy at Inlet (Evaporator Outlet, 100% Steam Quality, using approximation functions from Excel)
    h_3 = 28.276*np.log(p_evap)+1418.1
    s_3 = -0.352*np.log(p_evap)+6.1284
    
    # Enthalpy and Entropy at Outlet, using approximation functions from Excel
       
    s_4_liq = 0.3947*np.log(p_cond)+0.4644
    s_4_vap = -0.352*np.log(p_cond)+6.1284
    
    # Enthalpies of Liquid and Vapour Phase (Enthalpy at Liquid Phase equals Enthalpy and NH3 Pump Inlet)
    
    h_4_liq = -0.0235*p_cond**4+0.9083*p_cond**3-12.93*p_cond**2+97.316*p_cond-39.559
    h_4_vap = 28.276*np.log(p_cond)+1418.1
    
    x_4_isen = (s_3-s_4_liq)/(s_4_vap-s_4_liq)
    h_4_isen = h_4_vap*x_4_isen+h_4_liq*(1-x_4_isen)
    h_4 = (h_4_isen-h_3)*eff_isen_turb+h_3
    
    x_4 = (h_4-h_4_liq)/(h_4_vap-h_4_liq)
    s_4 = s_4_vap*x_4+s_4_liq*(1-x_4)
      
    h_1 = h_4_liq # inlet enthalpy
    h_2 = 1/inputs['rho_NH3']*(p_evap-p_cond)*100000/1000/inputs['eff_isen_pump']+h_1 # outlet enthalpy

    enthalpies = {
        'h_1': h_1,
        'h_2': h_2,
        'h_3': h_3,
        'h_4': h_4,
        }
    
    return enthalpies