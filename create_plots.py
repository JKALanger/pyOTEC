# -*- coding: utf-8 -*-
"""
Created on 14092023

@author: lucasvati

File containing various functions producing graphs for results visualization
"""

import numpy as np
import matplotlib.pyplot as plt
import os

import cost_analysis as ca

def plot_capex_opex(new_path,capex_opex_comparison,sites):
    """Function that plots the analysis of capex costs"""
    opex_coef = 0.03
    labels, array_plot_cost,T_WW,T_CW,cost_dict = ca.prepare_plot_capex_opex(new_path,capex_opex_comparison,sites)
    
    keys,array_CAPEX_percentage,total_CAPEX = ca.extract_percentage(capex_opex_comparison,opex_coef)
    
    if os.path.isdir(new_path+'/Details'):
        pass
    else:
        os.makedirs(new_path+'/Details')

    
    index=0
    for i,t_ww in enumerate(T_WW):
        for j,t_cw in enumerate(T_CW):
            
            """Plot the raw costs in dollars"""
            plt.figure()
            plt.ylabel('Cost [\$]')
            plt.title(f'Warm water at {t_ww}$^\circ$C and Cold water at {t_cw}$^\circ$C'+"\n"+f"LCOE={round(cost_dict['LCOE'][index],2)} ct/kWh")
            plt.bar(labels,array_plot_cost[index])
            plt.xticks(rotation=30, ha='right')
            plt.savefig(new_path+'/Details/'+f'costs_{i}_{j}.png',dpi=200, bbox_inches='tight')
            plt.close()
            
            """Plot the percentage of total capex"""
            plt.figure()
            plt.ylabel('Percentage of total capex [%]')
            plt.title(f'Warm water at {t_ww}$^\circ$C and Cold water at {t_cw}$^\circ$C'+"\n"+f"LCOE={round(cost_dict['LCOE'][index],2)} ct/kWh")
            plt.bar(keys,array_CAPEX_percentage[index])
            plt.xticks(rotation=30, ha='right')
            plt.savefig(new_path+'/Details/'+f'capex_percentage{i}_{j}.png',dpi=200, bbox_inches='tight')
            plt.close()

            index +=1
            

    """Same plots but with the configurations 1, 5 and 9 to compare them"""
    X=np.arange(len(labels))
    plt.figure()
    plt.ylabel('Cost [\$]')
    plt.bar(X,array_plot_cost[0], width = 0.25,label='Low $\Delta$T '+ f"LCOE={round(cost_dict['LCOE'][0],2)} ct/kWh")
    plt.bar(X+0.25,array_plot_cost[4], width = 0.25,label='Median $\Delta$T '+ f"LCOE={round(cost_dict['LCOE'][4],2)} ct/kWh")
    plt.bar(X+0.5,array_plot_cost[-1], width = 0.25,label='High $\Delta$T '+ f"LCOE={round(cost_dict['LCOE'][-1],2)} ct/kWh")
    plt.xticks(X + 0.25, labels,rotation=30, ha='right')
    plt.legend()
    plt.savefig(new_path+f'costs_min_max_med.png',dpi=200, bbox_inches='tight')
    plt.close()
    
    X_percentage=np.arange(len(keys))
    plt.figure()
    plt.ylabel('Percentage of total capex [%]')
    plt.bar(X_percentage,array_CAPEX_percentage[0], width = 0.25,label='Low $\Delta$T '+ f"LCOE={round(cost_dict['LCOE'][0],2)} ct/kWh")
    plt.bar(X_percentage+0.25,array_CAPEX_percentage[4], width = 0.25,label='Median $\Delta$T '+ f"LCOE={round(cost_dict['LCOE'][4],2)} ct/kWh")
    plt.bar(X_percentage+0.5,array_CAPEX_percentage[-1], width = 0.25,label='High $\Delta$T '+ f"LCOE={round(cost_dict['LCOE'][-1],2)} ct/kWh")
    plt.xticks(X_percentage + 0.25, keys,rotation=30, ha='right')
    plt.legend()
    plt.savefig(new_path+f'percentage_min_max_med.png',dpi=200, bbox_inches='tight')
    plt.close()

    return cost_dict





# def compare_percentage_power(location,powers):
    