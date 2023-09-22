# -*- coding: utf-8 -*-
"""
Created on 15092023

@author: lucasvati

File containing various functions to analyze the cost and compare the costs calculated
"""

import numpy as np

def extract_LCOE(capex_opex_comparison):
    """Extracts the LCOE from the dictionnary containing all the costs"""
    all_LCOE=[]
    for i in range(len(capex_opex_comparison)):
        LCOE_i=[]
        for j in range(len(capex_opex_comparison[0][0]['LCOE'])):
            LCOE_i.append(capex_opex_comparison[i][0]['LCOE'][j])
        all_LCOE.append(LCOE_i)
    return np.array(all_LCOE)

def average_LCOE_location(LCOE):
    """Calculates the average LCOE for each location"""
    t_LCOE = np.transpose(LCOE)
    all_average_LCOE=[]
    for LCOE_location in t_LCOE :
        all_average_LCOE.append(np.average(LCOE_location))
    return all_average_LCOE

def extract_costs_at_best_LCOE_location(capex_opex_comparison):
    """Extract the COPEX and OPEX costs at the location of interest (ie the best in the location chosen)
        For exemple, around Reunion Island, this is the 36th point of data calculated"""
    LCOE=extract_LCOE(capex_opex_comparison)
    best_LCOE_location_index=np.argmin(average_LCOE_location(LCOE))
    
    keys=capex_opex_comparison[0][0].keys()
    best_LCOE_dict={key: [] for key in keys}
    
    for i in range(len(capex_opex_comparison)):
        dict = capex_opex_comparison[i][0]
        for key in keys:
            best_LCOE_dict[key].append(dict[key][best_LCOE_location_index])
        
    return best_LCOE_location_index,best_LCOE_dict
    

def prepare_plot_capex_opex(new_path,capex_opex_comparison,sites):
    """Prepare the x and y axis for the plot of capex and opex"""
    best_LCOE_location_index,cost_dict = extract_costs_at_best_LCOE_location(capex_opex_comparison)

    T_WW=[sites['T_WW_min'].iloc[best_LCOE_location_index] ,sites['T_WW_med'].iloc[best_LCOE_location_index] ,sites['T_WW_max'].iloc[best_LCOE_location_index] ]
    T_CW=[sites['T_CW_max'].iloc[best_LCOE_location_index] ,sites['T_CW_med'].iloc[best_LCOE_location_index] ,sites['T_CW_min'].iloc[best_LCOE_location_index] ]
    
    labels=[]
    data=[]
    for key in cost_dict.keys() :
        if key != 'LCOE' and key !='OPEX' :
            labels.append(key.replace("_"," "))
            data.append(cost_dict[key])
    
    array_plot_cost=np.transpose(np.array(data))
    
    return labels, array_plot_cost,T_WW,T_CW,cost_dict

 

def extract_percentage(capex_opex_comparison,opex_coef):
    best_LCOE_location_index,best_LCOE_dict= extract_costs_at_best_LCOE_location(capex_opex_comparison)
    total_CAPEX=[]
    keys=[]
    for key in best_LCOE_dict.keys():
        if key != 'LCOE' and key != 'OPEX':
             keys.append(key)
    
    CAPEX_percentage=np.zeros((len(best_LCOE_dict['OPEX']),len(keys)))#{key: [] for key in keys }
    for i in range(len(best_LCOE_dict['OPEX'])):
        total_CAPEX_i=best_LCOE_dict['OPEX'][i]/opex_coef
        total_CAPEX.append(total_CAPEX_i)
        for j,key in enumerate(keys):
            CAPEX_percentage[i][j]=best_LCOE_dict[key][i]/total_CAPEX_i*100
            
    print(total_CAPEX[4])
    
    return keys,CAPEX_percentage,total_CAPEX
