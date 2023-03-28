# -*- coding: utf-8 -*-
"""
Created on Wed Feb 22 10:56:12 2023

@author: jkalanger
"""

import numpy as np

def capex_opex_lcoe(otec_plant_nom,inputs,cost_level='low_cost'):
    
    ## Unpack results from otec_steady_state
    
    p_gross = otec_plant_nom['p_gross_nom']
    p_pump_total = otec_plant_nom['p_pump_total_nom']
    p_net = otec_plant_nom['p_net_nom']
    
    A_evap = otec_plant_nom['A_evap']
    A_cond = otec_plant_nom['A_cond']
    
    m_pipes_WW = otec_plant_nom['m_pipes_WW']
    m_pipes_CW = otec_plant_nom['m_pipes_CW']
    
    dist_shore = inputs['dist_shore']
     
    if cost_level == 'low_cost':   
        capex_turbine = 328*(136000/-p_gross)**0.16
        capex_HX = 226*(80000/-p_gross)**0.16
        capex_pump = 1674*(5600/p_pump_total)**0.38
        capex_pipes = 9       
        capex_structure = 4465*(28100/-p_gross)**0.35
        capex_deploy = 650
        capex_controls = 3113*(3960/-p_gross)**0.70  
        capex_extra = 0.05    
        opex = 0.03          
    elif cost_level == 'high_cost':        
        capex_turbine = 512*(136000/-p_gross)**0.16
        capex_HX = 916*(4400/-p_gross)**0.093
        capex_pump = 2480*(5600/p_pump_total)**0.38
        capex_pipes = 30.1
        capex_structure = 7442*(28100/-p_gross)**0.35
        capex_deploy = 667
        capex_controls = 6085*(4400/-p_gross)**0.70 
        capex_extra = 0.2
        opex = 0.05
    else:
        raise ValueError('Invalid cost level. Valid inputs are "low_cost" and "high_cost"')
    
    capex_cable = np.empty(np.shape(dist_shore),dtype=np.float64)
    # AC cables for distances below or equal to 50 km, source: Bosch et al. (2019), costs converted from US$(2016) to US$(2021) with conversion factor 1.10411) 
    capex_cable[dist_shore <= 50] = (8.5*dist_shore[dist_shore <= 50]+56.8)*1.10411   
    # DC cables for distances beyond 50 km, source: Bosch et al. (2019), costs converted from US$(2016) to US$(2021) with conversion factor 1.10411)
    capex_cable[dist_shore > 50] = (2.2*dist_shore[dist_shore > 50]+387.8)*1.10411   
       
    (0.0085*1.11*1.09*inputs['dist_shore']+0.0568*1.11*1.09)
    
    CAPEX_turbine = capex_turbine*-p_gross
    CAPEX_evap = capex_HX*A_evap
    CAPEX_cond = capex_HX*A_cond
    CAPEX_pump = capex_pump*p_pump_total
    CAPEX_pipes = capex_pipes*(m_pipes_WW+m_pipes_CW)
    CAPEX_cable = capex_cable*-p_gross
    CAPEX_structure = capex_structure*(-p_gross)
    CAPEX_deploy = capex_deploy*(-p_gross)
    CAPEX_man = capex_controls*(-p_gross)
    
    CAPEX_wo_extra = CAPEX_turbine + CAPEX_evap + CAPEX_cond + CAPEX_pump + CAPEX_pipes + CAPEX_cable + CAPEX_structure + CAPEX_deploy + CAPEX_man
    CAPEX_extra = CAPEX_wo_extra*capex_extra
    
    CAPEX_total = CAPEX_wo_extra+CAPEX_extra
    
    OPEX = CAPEX_total*opex       
        
    LCOE_nom = (CAPEX_total*inputs['crf']+OPEX)*100/(-p_net*inputs['availability_factor']*8760) # LCOE in ct/kWh
       
    if np.any(LCOE_nom <= 0):
        raise ValueError('Invalid LCOE found, please check inputs.')
    else:
        pass
    
    return CAPEX_total,OPEX,LCOE_nom

def lcoe_time_series(otec_plant_nom,inputs,p_net_ts):
    
    p_net_mean = np.mean(p_net_ts,axis=0)
    e_mean_annual = -p_net_mean*8760
    
    lcoe_ts = (otec_plant_nom['CAPEX']*inputs['crf']+otec_plant_nom['OPEX'])*100/(e_mean_annual*inputs['availability_factor'])
    
    return lcoe_ts