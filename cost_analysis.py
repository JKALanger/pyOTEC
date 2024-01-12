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
    """Extract the COPEX and OPEX costs at the location where the lowest LCOE is calculated.
        For exemple, around Reunion Island, this would be the 36th point of data calculated"""
    LCOE=extract_LCOE(capex_opex_comparison)
    best_LCOE_location_index=np.argmin(average_LCOE_location(LCOE))
    
    keys=capex_opex_comparison[0][0].keys()
    best_LCOE_dict={key: [] for key in keys}
    
    for i in range(len(capex_opex_comparison)):
        dict = capex_opex_comparison[i][0]
        for key in keys:
            best_LCOE_dict[key].append(dict[key][best_LCOE_location_index])
        
    return best_LCOE_location_index,best_LCOE_dict
    

def extract_costs_at_user_study_location(sites,capex_opex_comparison,user_lon=55.25,user_lat=-20.833):
    """Similar function as extract_costs_at_best_LCOE_location but at a user defined location
        The user_lon and user_lat infos aren't used there, it is in the to do list"""
    filtered_sites = sites[(sites['longitude'] == user_lon) & (sites['latitude'] == user_lat)]
    # 2033171;55.25;-20.833;Reunion;-1543;9.5
    
    # Create a boolean mask to filter rows that match the desired coordinates : not used now
    mask = (sites['longitude'] == user_lon) & (sites['latitude'] == user_lat)

    # Find the row number(s) where the mask is True
    matching_rows = sites.index[mask]
    # print(matching_rows)
    
    #Number of 61 found manually, should be done automatically in future
    row_study_location=61

    keys=capex_opex_comparison[0][0].keys()
    best_LCOE_dict={key: [] for key in keys}
    
    for i in range(len(capex_opex_comparison)):
        dict = capex_opex_comparison[i][0]
        for key in keys:
            best_LCOE_dict[key].append(dict[key][row_study_location])
        
    return row_study_location,best_LCOE_dict



def prepare_plot_capex_opex(new_path,capex_opex_comparison,sites,studied_region):
    """Prepare the x and y axis for the plot of capex and opex"""
    if studied_region=="Reunion":
        "in Reunion Island, DEEPRUN works on a project for offshore OTEC at the coordinates 55.25;-20.833 "
        best_LCOE_location_index,cost_dict = extract_costs_at_user_study_location(sites,capex_opex_comparison,user_lon=55.25,user_lat=-20.833)

    else :
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
    
    return labels, array_plot_cost,T_WW,T_CW,cost_dict,best_LCOE_location_index

 

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
            
    # print('Total median CAPEX :',total_CAPEX[4])
    
    return keys,CAPEX_percentage,total_CAPEX
