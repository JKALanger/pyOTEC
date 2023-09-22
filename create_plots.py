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

def plot_capex_opex(new_path,capex_opex_comparison,sites,p_gross):
    """Function that plots the analysis of capex costs"""
    opex_coef = 0.03
    # approx_P_net = round(-p_gross*2/3000,1)
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
            

    """Same plots but with the configurations 1, 5 and 9 (best, median and worst) to compare them"""
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
    

    plt.figure()

    # Sample data
    categories = ['Thermodynamics', 'Pipes', 'Structure', 'Other']
    components = [['turbine_CAPEX','evap_CAPEX','cond_CAPEX','pump_CAPEX'],
                  ['pipes_CAPEX'],
                  ['platform_CAPEX','mooring_CAPEX'],
                  ['cable_CAPEX','deploy_CAPEX','man_CAPEX','extra_CAPEX']]

    modified_components = [[item.replace('_CAPEX', '') for item in sublist] for sublist in components]

    # Find the maximum length of sublists
    max_length = max(len(sublist) for sublist in modified_components)

    # Create an empty NumPy array filled with NaN
    component_array = np.empty((len(components), max_length), dtype=object)
    component_array[:] = np.nan

    # Fill the array with the modified values
    for i, sublist in enumerate(modified_components):
        component_array[i, :len(sublist)] = sublist
    
    print(component_array)
    
    bar_width = 0.85
    x = np.arange(len(categories))
    
    test=np.zeros((4,4))

    all_component_values=[]
    # Create a bar plot for each category
    for i, category_data in enumerate(categories):
        component_values=[]
        for j,component_names in enumerate(components[i]):
            test[i][j] = cost_dict[component_names][4]/1e6
            # component_values.append(cost_dict[component_names][4])
        
        
            # plt.bar(x + i * bar_width, test, width=bar_width, label=category_data)
        
        # Add component names as x-axis labels for each bar
        # plt.xticks(x + bar_width * (len(data) / 2), component_names, rotation=45, ha='right')
        # all_component_values.append(component_values)
        # plt.bar()
    
    test_t = np.transpose(test)
    bottom_values=np.zeros((4,4))
    for i in range(len(test_t)):
        for j in range(i):
            bottom_values[i]+=test_t[j]
        
        plt.bar(x, test_t[i],bottom=bottom_values[i], width=bar_width)
        for j, value in enumerate(test_t[i]):
            if value > 0 :
                # print(i,j,x[j],bottom_values[i][j],value,component_array[j][i])
                plt.text(x[j], bottom_values[i][j] + value / 2, component_array[j][i] +' '+ str(round(value,1)), ha='center', va='center')
                # plt.text(x[j], bottom_values[j] + value / 2, components[i][j] + ' : ' + str(value), ha='center', va='center')

    
    # plt.bar(x, test_t[0],bottom=bottom_values[0], width=bar_width)
    # plt.bar(x, test_t[1],bottom=bottom_values[1], width=bar_width)
    # plt.bar(x, test_t[2],bottom=bottom_values[2], width=bar_width)
    # plt.bar(x, test_t[3],bottom=bottom_values[3], width=bar_width)
    # for i in range(len(test_t)):
    #     plt.bar(x, test_t[i],bottom=test_t[i-1], width=bar_width, label=categories[i])
    
    # Add a legend
    plt.ylabel('CAPEX Cost [M\$]')
    plt.xticks(x, categories)
    plt.title(f'Warm water at {T_WW[1]}$^\circ$C and Cold water at {T_CW[1]}$^\circ$C'+"\n"+ f"Gross power = {p_gross/-1000}MW" + "\n"+ f"LCOE={round(cost_dict['LCOE'][4],2)} ct/kWh")
    plt.savefig(new_path+'med_resume.png',dpi=200, bbox_inches='tight')
    plt.close()


    return cost_dict





# def compare_percentage_power(location,powers):
    