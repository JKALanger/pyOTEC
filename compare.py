# -*- coding: utf-8 -*-
"""
Created on 12102023

@author: lucasvati

File containing various functions to compare simulations :
- at different locations
- for different power gross
"""

import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit


# Function to find files with a specific pattern
def find_files(directory, pattern):
    file_list=[]
    for root, _, files in os.walk(directory):
        for filename in files:
            if pattern in filename:
                file_list.append(os.path.join(root, filename))
    return file_list

def selection_sort_with_indexes(arr_ini):
    """sort the arr_ini by ascending order"""
    n = len(arr_ini)
    arr = arr_ini.copy()
    indexes = list(range(n))

    for i in range(n):
        # Find the minimum element in the unsorted part of the list
        min_idx = i
        for j in range(i + 1, n):
            if arr[j] < arr[min_idx]:
                min_idx = j

        # Swap the minimum element with the current element in the original list and index list
        arr[i], arr[min_idx] = arr[min_idx], arr[i]
        indexes[i], indexes[min_idx] = indexes[min_idx], indexes[i]

    return arr, indexes

def extract_variable_path(path,string_left,string_right):
    """Extract a variable a bath between string_left and string_right"""
    # Find the index of "2020_"
    start_index = path.find(string_left)
    n=len(string_left)

    if start_index != -1:
        # Start searching for "MW" after the "2020_" index
        end_index = path.find(string_right, start_index)

        if end_index != -1:
            # Extract the number
            extracted_number = float(path[start_index + n:end_index])
    #     else:
    #         print("No '_MW' found after '2020_'.")
    # else:
    #     print("No '2020_' found in the string.")
    return extracted_number   

def func_powerlaw(x, m, c, c0):
    """hyperbolic funtion for fitting the results"""
    return c0 + 1/(x**m) * c



def compare_economics_locations(locations):
    """Compare the results at the locations specified in the list 'locations'"""
    all_pgross=[]
    all_pnet=[]
    all_pipe_capex=[]
    all_lcoe=[]
    all_fit=[]
    
    for location in locations :
        pattern_eco = "eco_details"
        pattern_net = "net_power_profiles_per_location_"


        folder_name = "Comparison/" + location

        # Check if the folder exists, and if not, create it
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
            print(f"The '{folder_name}' folder has been created.")
        else:
            print(f"The '{folder_name}' folder already exists.")

        # Find and list files of economic results and power
        eco_details_files = find_files("Data_Results/"+location, pattern_eco)
        pnet_files = find_files("Data_Results/"+location, pattern_net)


        # folders = []
        # for file in eco_details_files : 
        #     position = file.find("/eco")
        #     if position != -1:
        #         # Remove everything after "/eco"
        #         folders.append(file[:position+1])  # +1 to include "/" in the result
                

        list_pipe_CAPEX=[]
        list_LCOE=[]
        list_pgross=[]
        list_best_LCOE_position=[]
        for file in eco_details_files:
            df=pd.read_csv(file,sep=';')
            list_LCOE.append(df['LCOE'].to_numpy())
            list_pipe_CAPEX.append(df['pipes_CAPEX'].to_numpy())
            list_pgross.append(extract_variable_path(file,"2020_","_MW"))
            list_best_LCOE_position.append(int(extract_variable_path(file,"_pos_","_index_")))
            
        list_pnet=[]
        for i,file in enumerate(pnet_files):
            pnet_df=pd.read_csv(file,sep=';')
            pnet_list=pnet_df['p_net'].to_numpy()
            list_pnet.append(-pnet_list[list_best_LCOE_position[i]]/1000)


        med_LCOE = []
        med_pipe_CAPEX = []
        for i,sublist in enumerate(list_LCOE):
            med_pipe_CAPEX.append(list_pipe_CAPEX[i][4])
            med_LCOE.append(sublist[4])


        sorted_pgross, indexes = selection_sort_with_indexes(list_pgross)
        sorted_LCOE = [med_LCOE[i] for i in indexes]
        sorted_pnet = [list_pnet[i] for i in indexes]
        sorted_pipe_CAPEX = [med_pipe_CAPEX[i]/1e6 for i in indexes]

        all_pgross.append(sorted_pgross)
        all_pnet.append(sorted_pnet)
        all_pipe_capex.append(sorted_pipe_CAPEX)
        all_lcoe.append(sorted_LCOE)
        

        def analyse_gross_net_power(string):
            if string =="gross":
                x_list = sorted_pgross
                x_label = "Gross"
            elif string=="net":
                x_list = sorted_pnet
                x_label = "Net"

            sol2, divers = curve_fit(func_powerlaw, x_list, sorted_LCOE, p0 = np.asarray([0.5,100,20]))

            # sol2 contains the estimated parameters m,c and c0.
            m_fit, c_fit, c0_fit = sol2
            
            
            x_fit = np.linspace(min(x_list), max(x_list), 100)
            y2 = func_powerlaw(x_fit,m_fit, c_fit, c0_fit)


            plt.figure()
            plt.scatter(x_list, sorted_LCOE, label='pyOTEC',s=10)
            plt.plot(x_fit,y2,label='$f(x) = \\frac{%.2f}{x^{%.2f}} %+.2f$' % (c_fit, m_fit, c0_fit), color='green')
            plt.xlabel(x_label +' Power(MW)')
            plt.ylabel('LCOE(ct\$/kWh)')
            plt.legend()
            plt.savefig(folder_name+'/' + x_label + '_LCOE_fit.png',
                            dpi=200, bbox_inches='tight')
            plt.close()

            m,b = np.polyfit(x_list, sorted_pipe_CAPEX, 1)
            pipe_fit = [m*x + b for x in x_fit]
            
            plt.figure()
            plt.scatter(x_list, sorted_pipe_CAPEX, label='pyOTEC',s=10)
            plt.plot(x_fit,pipe_fit,label='$f(x) = {%.2f}x %+.2f$' % (m,b), color='green')
            plt.xlabel(x_label +' Power(MW)')
            plt.ylabel('Pipe CAPEX(M\$)')
            plt.legend()
            plt.savefig(folder_name+'/' + x_label + 'pipe_CAPEX_fit.png',
                            dpi=200, bbox_inches='tight')
            plt.close()
            
            return sol2,m,b

        analyse_gross_net_power("gross")
        sol2,m,b = analyse_gross_net_power("net")
        
        all_fit.append([sol2,m,b])
    return all_pgross,all_pnet,all_pipe_capex,all_lcoe,all_fit



locations=["Comores","Reunion"]
label_locations = ""
for location in locations:
    label_locations += "_"+ location
all_pgross,all_pnet,all_pipe_capex,all_lcoe,all_fit = compare_economics_locations(locations)

string ="net"

# def compare_locations(locations):
"""Plots the LCOE comparison"""
plt.figure()
for i,location in enumerate(locations) : 
    if string =="gross":
        x_list = all_pgross[i]
        x_label = "Gross"
    elif string=="net":
        x_list = all_pnet[i]
        x_label = "Net"
    [sol2,m,b] = all_fit [i]
    m_fit, c_fit, c0_fit = sol2
    x_fit = np.linspace(min(x_list), max(x_list), 100)
    pipe_fit = [m*x + b for x in x_fit]

    y2 = func_powerlaw(x_fit,m_fit, c_fit, c0_fit)
    
    plt.scatter(x_list, all_lcoe[i], label=location,s=10)
    plt.plot(x_fit,y2,label='$f(x) = \\frac{%.2f}{x^{%.2f}} %+.2f$' % (c_fit, m_fit, c0_fit))
plt.xlabel(x_label +' Power(MW)')
plt.ylabel('LCOE(ct\$/kWh)')
plt.legend()
plt.savefig("Comparison/LCOE_" + x_label + label_locations+ '.png',
                dpi=200, bbox_inches='tight')
plt.close()


"""Plots the pipe CAPEX comparison"""
plt.figure()
for i,location in enumerate(locations) : 
    if string =="gross":
        x_list = all_pgross[i]
        x_label = "Gross"
    elif string=="net":
        x_list = all_pnet[i]
        x_label = "Net"
    sol2,m,b = all_fit [i]
    m_fit, c_fit, c0_fit = sol2
    x_fit = np.linspace(min(x_list), max(x_list), 100)
    pipe_fit = [m*x + b for x in x_fit]

    y2 = func_powerlaw(x_fit,m_fit, c_fit, c0_fit)

    plt.scatter(x_list, all_pipe_capex[i], label=location,s=10)
    plt.plot(x_fit,pipe_fit,label='$f(x) = {%.2f}x %+.2f$' % (m,b))
plt.xlabel(x_label +' Power(MW)')
plt.ylabel('Pipe CAPEX(M\$)')
plt.legend()
plt.savefig("Comparison/pipe_CAPEX_" + x_label + label_locations + '.png',
                dpi=200, bbox_inches='tight')
plt.close()


#Rajouter ligne horizontale pour le LCOE d'autres énergies à la Réunion

        