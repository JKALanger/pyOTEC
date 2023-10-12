# -*- coding: utf-8 -*-
"""
Created on 14092023

@author: lucasvati

File containing various functions producing graphs for results visualization
"""

import numpy as np
import matplotlib.pyplot as plt
import os
import cartopy.crs as ccrs

import cost_analysis as ca




def plot_capex_opex(new_path, capex_opex_comparison, sites, p_gross,studied_region):
    """Function that plots the analysis of capex costs"""
    opex_coef = 0.03
    # approx_P_net = round(-p_gross*2/3000,1)
    labels, array_plot_cost, T_WW, T_CW, cost_dict, best_LCOE_location_index = ca.prepare_plot_capex_opex(
        new_path, capex_opex_comparison, sites,studied_region)

    # print(sites.iloc[best_LCOE_location_index]['latitude'])
    best_latitude = sites.iloc[best_LCOE_location_index]['latitude']
    best_longitude = sites.iloc[best_LCOE_location_index]['longitude']

    keys, array_CAPEX_percentage, total_CAPEX = ca.extract_percentage(
        capex_opex_comparison, opex_coef)

    if os.path.isdir(new_path+'/Details'):
        pass
    else:
        os.makedirs(new_path+'/Details')
    
    bar_plot(new_path,cost_dict,array_CAPEX_percentage,T_WW,T_CW,p_gross)



def bar_plot(new_path,cost_dict,array_CAPEX_percentage,T_WW,T_CW,p_gross):
    """Plot the median costs and percentages on a bar plot"""

    categories = ['Thermodynamics', 'Pipes', 'Structure', 'Other']
    components = [['turbine_CAPEX', 'evap_CAPEX', 'cond_CAPEX', 'pump_CAPEX'],
                    ['pipes_CAPEX'],
                    ['platform_CAPEX', 'mooring_CAPEX'],
                    ['cable_CAPEX', 'deploy_CAPEX', 'man_CAPEX', 'extra_CAPEX']]

    #colors are done by hand, when black is selected, the color isn't displayed because the corresponding bar height is nul (value is 0)
    #colors are written in rbga, with the 4th parameter being the opacity. will need a function in the future
    color_array = [[(0.580, 0.404, 0.741,1),    'grey', (0.051, 0.467, 0.706, 1.0),(0.8,0,0, 1)],
                   [(0.580, 0.404, 0.741,0.65), 'black',(0.051, 0.467, 0.706, 0.5),(0.8,0,0, 0.65)],
                   [(0.580, 0.404, 0.741,0.40), 'black','black'                   ,(0.8,0,0, 0.4)],
                   [(0.580, 0.404, 0.741,0.15), 'black','black'                   ,(0.8,0,0, 0.15)]]


    modified_components = [
        [item.replace('_CAPEX', '') for item in sublist] for sublist in components]

    # Find the maximum length of sublists
    max_length = max(len(sublist) for sublist in modified_components)

    # Create an empty NumPy array filled with NaN
    component_array = np.empty((len(components), max_length), dtype=object)
    component_array[:] = np.nan

    # Fill the array with the modified values
    for i, sublist in enumerate(modified_components):
        component_array[i, :len(sublist)] = sublist

    bar_width = 0.85
    x = np.arange(len(categories))

    cost_sorted = np.zeros((4, 4))
    percentage_sorted = np.zeros((4, 4))

    index = 0
    # Create a bar plot for each category
    for i, category_data in enumerate(categories):
        for j, component_names in enumerate(components[i]):

            cost_sorted[i][j] = cost_dict[component_names][4]/1e6
            percentage_sorted[i][j] = array_CAPEX_percentage[4][index]
            index = index+1

    num_color = 0

    fig, ax1 = plt.subplots(figsize=(8, 6))
    ax1.set_ylabel('CAPEX Cost [M\$]')
    ax1.set_xticks(x, categories)
    ax2 = ax1.twinx()

    cost_t = np.transpose(cost_sorted)
    bottom_values_cost = np.zeros((4, 4))
    bottom_values_percentage = np.zeros((4, 4))

    percentage_t = np.zeros((4, 4))
    total_cost = np.sum(cost_t)

    for i in range(len(cost_t)):
        for j in range(len(cost_t[0])):
            percentage_t[i][j] = cost_t[i][j]/total_cost*100

    alpha=1
    for i in range(len(cost_t)):
        for j in range(i):
            bottom_values_cost[i] += cost_t[j]
            bottom_values_percentage[i] += percentage_t[j]

        ax1.bar(x, cost_t[i], bottom=bottom_values_cost[i],
                width=bar_width, color=color_array[i],zorder=1) #color_array[i]
        ax2.bar(x, percentage_t[i], bottom=bottom_values_percentage[i],
                width=bar_width, color=color_array[i],zorder=0)
        alpha=alpha-0.2

        for j, value in enumerate(percentage_t[i]):
            if value > 0:
                num_color += 1
                
                ax2.text(x[j], bottom_values_percentage[i][j] + value / 2, component_array[j][i] +
                         ' ' + str(round(cost_t[i][j], 1)) + 'M\$', ha='center', va='center', zorder=10)

    ax2.set_ylabel('Percentage of Total CAPEX (%)')

    plt.title(f'Warm water at {T_WW[1]}$^\circ$C and Cold water at {T_CW[1]}$^\circ$C'+"\n" + f"Gross power = {p_gross/-1000}MW" +
              "\n" + f"Total CAPEX={round(total_cost,0)}M\$  LCOE={round(cost_dict['LCOE'][4],2)} ct/kWh")
    # {round(total_CAPEX[4]/1e6,0)}
    plt.savefig(new_path+f'med_bar_{-p_gross}kW.png', dpi=200, bbox_inches='tight')
    plt.close()
    

def plot_average_LCOE_on_map(capex_opex_comparison, sites):
    """Not working yet, the structure of the data should be :
        latitude and longitude : 1D
        average LCOE : 2D with row corresponding to latitude and column to longitude
        with masked values when there is land or when the water depth is too low.
        We can maybe consider going back to the initial latitude and longitude data to put a mask
    """
    LCOE = ca.extract_LCOE(capex_opex_comparison)
    average_LCOE = ca.average_LCOE_location(LCOE)
    # id=sites.index.values
    lat = sites['latitude'].to_numpy()
    lon = sites['longitude'].to_numpy()
    lat_step = lat[1]-lat[0]
    lon_step = lon[1]-lat[0]
    all_lat = np.arange(np.min(lat), np.max(lat), step=lat_step)
    all_lon = np.arange(np.min(lon), np.max(lon), step=lon_step)

    fig = plt.figure()
    ax = plt.axes(projection=ccrs.PlateCarree())

    # Create a GeoAxes in the tile's projection.
    x, y = np.meshgrid(lon, lat)

    # Limit the extent of the map to a small longitude/latitude range.
    ax.set_extent([np.min(lon), np.max(lon), np.min(
        lat), np.max(lat)], crs=ccrs.Geodetic())
    ax.coastlines(resolution='10m', color='black', linewidth=1)
    # ax.scatter(x,y,transform=ccrs.Geodetic(),c=average_LCOE)

    plt.show()

def plot_details(new_path,T_WW,T_CW,labels,array_plot_cost,cost_dict,keys,array_CAPEX_percentage):
    """Creates 9 plots for each of the 9 configuration of cold and warm water considered
        with the cost in dollars and the percentage in total capex"""
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



def plot_config_159(new_path,labels,array_plot_cost,cost_dict,best_longitude,best_latitude):
    """Same plots but with the configurations 1, 5 and 9 (best, median and worst) to compare them"""
    X = np.arange(len(labels))
    plt.figure()
    plt.ylabel('Cost [\$]')
    plt.bar(X, array_plot_cost[0], width=0.25, label='Low $\Delta$T ' +
            f"LCOE={round(cost_dict['LCOE'][0],2)} ct/kWh")
    plt.bar(X+0.25, array_plot_cost[4], width=0.25, label='Median $\Delta$T ' +
            f"LCOE={round(cost_dict['LCOE'][4],2)} ct/kWh")
    plt.bar(X+0.5, array_plot_cost[-1], width=0.25, label='High $\Delta$T ' +
            f"LCOE={round(cost_dict['LCOE'][-1],2)} ct/kWh")
    plt.xticks(X + 0.25, labels, rotation=30, ha='right')
    plt.legend()
    plt.title(
        f'Costs at best location : Longitude {best_longitude} / Latitude {best_latitude}')
    plt.savefig(new_path+f'costs_min_max_med.png',
                dpi=200, bbox_inches='tight')
    plt.close()
    
    
    
def plot_percentage_159(keys,array_CAPEX_percentage,cost_dict,new_path):
    """Plots percentages with the configurations 1, 5 and 9 (best, median and worst) to compare them"""
    X_percentage = np.arange(len(keys))
    plt.figure()
    plt.ylabel('Percentage of total capex [%]')
    plt.bar(X_percentage, array_CAPEX_percentage[0], width=0.25,
            label='Low $\Delta$T ' + f"LCOE={round(cost_dict['LCOE'][0],2)} ct/kWh")
    plt.bar(X_percentage+0.25, array_CAPEX_percentage[4], width=0.25,
            label='Median $\Delta$T ' + f"LCOE={round(cost_dict['LCOE'][4],2)} ct/kWh")
    plt.bar(X_percentage+0.5, array_CAPEX_percentage[-1], width=0.25,
            label='High $\Delta$T ' + f"LCOE={round(cost_dict['LCOE'][-1],2)} ct/kWh")
    plt.xticks(X_percentage + 0.25, keys, rotation=30, ha='right')
    plt.legend()
    plt.savefig(new_path+f'percentage_min_max_med.png',
                dpi=200, bbox_inches='tight')
    plt.close()
    
    
    
# def camembert_plot(new_path,cost_t,cost_sorted,labels,array_plot_cost,T_WW,T_CW,p_gross,cost_dict):
#     size=4
#     # normalizing data to 2 pi
#     norm = cost_t / np.sum(cost_t)*2 * np.pi
    
#     print(cost_sorted)
#     total_cost = np.sum(cost_t)

#     blue_colormap = create_custom_colormap_rgba((0.12156862745098039, 0.4666666666666667, 0.7058823529411765), 4)
#     orange_colormap = create_custom_colormap_rgba((1.0, 0.4980392156862745, 0.054901960784313725), 1)
#     green_colormap = create_custom_colormap_rgba((0.17254901960784313, 0.6274509803921569, 0.17254901960784313),2)
#     purple_colormap = create_custom_colormap_rgba((0.5803921568627451, 0.403921568627451, 0.7411764705882353),4)

#     color_list = blue_colormap + orange_colormap + green_colormap + purple_colormap
#     # color_list = ['blue', 'red', 'cyan', 'lightpink', 'green',
#     #               'black', 'orange', 'darkseagreen', 'grey', 'purple', 'brown']

#     wp = { 'linewidth' : 1, 'edgecolor' : "white" }
    
#     all_labels = []
#     for label in labels:
#         all_labels.append(label.replace(" CAPEX", ""))
#     # Create a function to format the labels with costs

#     def func(pct, allvals):
#         absolute = int(pct/100.*sum(allvals))
#         return f"{pct:.1f}%\n${absolute/1e6:.1f}M"

    
#     category_sums = [sum(cost_sorted[i]) for i in range(len(categories))]
    
#     # outer_pie = ax.pie(category_sums, labels=categories, autopct='%1.1f%%', startangle=90, pctdistance=0.85)
    
    
#     plt.figure()
#     # plt.ylabel('Cost [\$]')
#     # plt.title(f'Warm water at {t_ww}$^\circ$C and Cold water at {t_cw}$^\circ$C'+"\n"+f"LCOE={round(cost_dict['LCOE'][index],2)} ct/kWh")
#     plt.pie(array_plot_cost[4], labels=all_labels, labeldistance=1, pctdistance=0.7,wedgeprops = wp,explode=[
#             0, 0, 0, 0, 0.1, 0, 0, 0, 0, 0, 0], colors=color_list, autopct=lambda pct: func(pct, array_plot_cost[4]),startangle=0)
#     # plt.xticks(rotation=30, ha='right')

#     plt.subplots_adjust(top=1.5)
#     plt.title(f'Warm water at {T_WW[1]}$^\circ$C and Cold water at {T_CW[1]}$^\circ$C'+"\n" + f"Gross power = {p_gross/-1000}MW" +
#               "\n" + f"Total CAPEX={round(total_cost,0)}M\$  LCOE={round(cost_dict['LCOE'][4],2)} ct/kWh")
#     # {round(total_CAPEX[4]/1e6,0)}
#     plt.savefig(new_path+'camembert.png', dpi=200, bbox_inches='tight')
#     plt.close()
    

    # return cost_dict