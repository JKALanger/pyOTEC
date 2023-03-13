# -*- coding: utf-8 -*-
"""
Created on Fri Mar  3 16:08:37 2023

@author: jkalanger
"""

import requests
import netCDF4
import pandas as pd
import numpy as np
import datetime
import os
import time

## We use seawater temperature data from HYCOM for our OTEC analysis. If the data does not exist in the work folder yet, then it is downloaded with the function
## below. Essentially, we contact HYCOM's servers via an url created from input data like desired year, water depth, coordinates, etc, and download the data
## after the connection to the server has been established successfully.

## NOTE: In this version of pyOTEC, we use NCSS to download the data, which is mainly designed to download small sets of data, but not entire years
## or countries worth of data. Therefore, the download may not be successful if the queries are too big or HYCOM's servers are too busy. We will try to improve
## the download setup, but for now the best remedy is to re-try the download until it works...

def get_HYCOM_data(cost_level,inputs,studied_region,new_path):
    
    ## The csv file below stores all countries and territories that have OTEC resources, their coordinates, and electricity demand in 2019.
    
    regions = pd.read_csv('HYCOM_download_ranges_per_region.csv',delimiter=';',encoding='latin-1')  
        
    if np.any(regions['region'] == studied_region):
        
        parts = regions['region'].value_counts()[studied_region]
        
        ## OTEC uses warm surface seawater to evaporate a work fluid, while cold deep-sea water is used to condense said work fluid. From HYCOM, we download
        ## seawater temperature data from depths representing warm water (WW) and cold water (CW). Our default values are 20m and 1000m, respectively, but
        ## the user can choose other depths if desired. Note though, that the chosen depths must be covered by HYCOM's dataset, so the user cannot choose
        ## any arbitrary depth.
        
        depth_WW = inputs['length_WW_inlet']
        depth_CW = inputs['length_CW_inlet']
        
        ## Due to download limitations, we only download one year of data. We chose the year 2011, but any year between 1994 and 2012 could also work.
        
        year = inputs['date_start'][0:4]
        
        ## We store the filenames and their paths, so that the seawater temperature data can be accessed by pyOTEC later.
        
        files = []
        
        for depth in [depth_WW,depth_CW]:
            for part in range(0,parts):
                
                ## The coordinates for the download are pulled from the csv file. Alternatively, the user could define the coordinates themselves.
            
                north = float(regions[regions['region']==studied_region]['north'].iloc[part])
                south = float(regions[regions['region']==studied_region]['south'].iloc[part])
                west = float(regions[regions['region']==studied_region]['west'].iloc[part])
                east = float(regions[regions['region']==studied_region]['east'].iloc[part])
                             
                start_hycom = time.time()
                filename = os.path.join(new_path, f'T_{depth}m_{year}_{studied_region}_{part+1}.nc'.replace(" ","_"))
                files.append(filename)
                
                if os.path.isfile(filename):           
                    print('File already exists. No download necessary.')
                    continue
                else:  
                    
                    ## here we construct the URL with which we request the data from HYCOM's servers.
                    
                    url = ('http://ncss.hycom.org/thredds/ncss/GLBu0.08/reanalysis/3hrly?var=water_temp&north=' +
                           str(north) + '&west=' + str(west) + '&east=' + str(east) + '&south=' + str(south) + 
                           '&disableProjSubset=on&horizStride=' + str(inputs['horizontal_stride']) +
                           '&time_start=' + str(inputs['date_start'][0:10]) + 'T' + str(inputs['date_start'][11:13]) +
                           '%3A' + str(inputs['date_start'][14:16]) + '%3A' + str(inputs['date_start'][17:19]) +
                           'Z&time_end=' + str(inputs['date_end'][0:10]) + 'T' + str(inputs['date_end'][11:13]) +
                           '%3A' + str(inputs['date_end'][14:16]) + '%3A' + str(inputs['date_end'][17:19]) + 
                           'Z&timeStride=' + str(inputs['time_stride']) + '&vertCoord=' + str(depth) +
                           '&addLatLon=true&accept=netcdf')
                    
                    print(f'\nRequesting T_{depth}m from {year} across {studied_region} ({part+1}/{parts})')
                    
                    r = requests.get(url,timeout=3600) # Timeout = 3600 means that we attempt to connect to the server for up to one hour until we cancel the request
                    open(filename,'wb').write(r.content) # Here, we save the seawater temperature data as a nc file
                    
                    end_hycom = time.time()
                    print('nc file saved. Time for download: ' + str(round((end_hycom-start_hycom)/60,2)) + ' minutes.')
        
        return files    
        
    else:
        raise ValueError('Entered region not valid. Please check for typos and whether the region is included in "HYCOM_download_ranges_per_region.csv"')


def data_processing(files,sites_df,inputs,studied_region,new_path,water,nan_columns = None):
    
    ## Here we convert the pandas Dataframe storing site-specific data into a numpy array
    
    sites = np.vstack((sites_df['longitude'],sites_df['latitude'],sites_df['dist_shore'])).T
    
    ## The "for file in files" was made for countries and territories that stretch across the East/West border, like Fiji and New Zealand.
    ## These regions are split into two parts that cover the regions' Eastern and Western side, respectively.

    for file in files:
        ## It can happen that a corruped nc file is downloaded with 1 kB size. In that case, reading the file would raise an error. So, we try to read the file,
        ## and if it does not work, it means that the file is corrupted and needs to be downloaded again.
        try:
            T_water_nc = netCDF4.Dataset(file,'r')       
        except:
            raise Warning(f'{file} was not downloaded successfully. Please try downloading the file later.')
    
    ## HYCOM's data is timed by hours passed since 01-01-2000 00:00. Here, we convert the timestamp to year-month-day hour:minute:second    
    
    time = T_water_nc.variables['time'][:]
    time_origin = datetime.datetime.strptime(inputs['time_origin'], '%Y-%m-%d %H:%M:%S') 
    timestamp = [time_origin + datetime.timedelta(hours=step) for idx,step in enumerate(time)]  
    
    ## Earlier, we downloaded the HYCOM data across a rectangular field defined by the input coordinates. However, not every HYCOM data point is suitable
    ## for OTEC (e.g. points on land, too shallow/ deep water, inside marine protection areas, etc). In this loop, we check which downloaded data points
    ## could be occupied by OTEC plants, and store their coordinates and temperature profiles in a numpy array
    
    T_water_profiles = np.zeros((time.shape[0],0),dtype=np.float64)
    coordinates = np.zeros((0,2),dtype=np.float64)
    dist_shore = np.zeros((1,0),dtype=np.float64)
    
    for file in files:
        T_water_nc = netCDF4.Dataset(file,'r')             
        latitude = T_water_nc.variables['lat'][:]
        longitude = T_water_nc.variables['lon'][:]
        depth = int(T_water_nc.variables['depth'][:])
        T_water = T_water_nc.variables['water_temp'][:]
        
        hycom_points = np.round([(idx_lon,idx_lat,lon,lat) for idx_lon,lon in enumerate(longitude) for idx_lat,lat in enumerate(latitude)],2)
        
        for index,point in enumerate(hycom_points):
            match = np.array(np.where((point[2]==sites[:,0]) & (point[3]==sites[:,1])))
            if match.size != 0:
                if T_water_profiles.shape[1] == 0:
                    coordinates = [point[2],point[3]]
                    dist_shore = sites[match,2]
                    T_water_profiles = (np.array(T_water[:,:,int(point[1]),int(point[0])],dtype=np.float64))
                else:
                    coordinates = np.vstack((coordinates, [point[2],point[3]]))
                    dist_shore = np.hstack((dist_shore, sites[match,2]))
                    T_water_profiles = np.hstack((T_water_profiles,(np.array(T_water[:,:,int(point[1]),int(point[0])],dtype=np.float64))))
            else:
                pass
    
    ## After obtaining the relevant HYCOM points, we calculate power transmission losses from OTEC plant offshore to the public grid onshore in kilometres.
    
    eff_trans = np.empty(np.shape(dist_shore),dtype=np.float64)
    # AC cables for distances below or equal to 50 km, source: Fragoso Rodrigues (2016) 
    eff_trans[dist_shore <= inputs['threshold_AC_DC']] = 0.979-1*10**-6*dist_shore[dist_shore <= 50]**2-9*10**-5*dist_shore[dist_shore <= 50]  
    # DC cables for distances beyond 50 km, source: Fragoso Rodrigues (2016) 
    eff_trans[dist_shore > inputs['threshold_AC_DC']] = 0.964-8*10**-5*dist_shore[dist_shore > 50]  

    ## Some of HYCOM's data is either missing (no timestamp) or faulty (e.g. T = -30000)
    ## First, we remove the faulty values
    T_water_profiles[T_water_profiles < 0] = np.nan
    ## For the cold water dataset, we remove any values above 10 degrees at a depth of 1000m
    if depth == inputs['length_CW_inlet']:
        T_water_profiles[T_water_profiles > 10] = np.nan
    
    ## Although HYCOM's dataset comes in 3-hourly resolution, many timestamps are completely missing. Here, we resample the dataset to show all timestamps
    ## and to fill previously missing steps with NaN, which are then filled via linear interpolation
    T_water_profiles_df = pd.DataFrame(T_water_profiles)   
    T_water_profiles_df.columns = [str(val[0]) + '_' + str(val[1]) for idx,val in enumerate(coordinates)]
    T_water_profiles_df['time'] = timestamp
    T_water_profiles_df = T_water_profiles_df.set_index('time').asfreq('3H')       
    T_water_profiles_df = T_water_profiles_df.interpolate(method='linear')
    
    # Calculating interquartiles. With a factor 3, we are less strict with outliers than the convention of 1.5
    # With this, we want to account for extreme seawater temperature conditions that would otherwise be removed from the dataset
    r = T_water_profiles_df.rolling(window=56)
    mps = (r.quantile(0.75) - r.quantile(0.25))*3 
    np.where(T_water_profiles>15)
    T_water_profiles_df[(T_water_profiles_df < T_water_profiles_df.quantile(0.25) - mps) |
                        (T_water_profiles_df > T_water_profiles_df.quantile(0.75) + mps)] = np.nan
    
    T_water_profiles_df = T_water_profiles_df.interpolate(method='linear')
    
    ## In some case, some HYCOM points don't have any data at all. We think this is due to the discrepancy of bathymetric data between HYCOM and GEBCO data
    ## If there are profiles solely consisting of NaN, they are removed from the dataset
    
    if nan_columns is None:
        nan_columns = np.where(T_water_profiles_df.isna())
    else:
        pass
    
    T_water_profiles_df = T_water_profiles_df.drop(T_water_profiles_df.iloc[:,nan_columns[1]],axis=1)
    T_water_profiles = np.array(T_water_profiles_df,dtype=np.float64)
    
    ## To assess OTEC's economic and technical performance under off-design conditions, we design the plants for different warm and cold seawater temperatures
    ## Using combinations of minimum, median, and maximum temperature, we assess a total of nine configurations. For example, the most conservative configuration is
    ## configuration 1 using minimum warm seawater temperature and maximum cold deep-seawater temperature.
    
    ## Here, we calculate the design temperatures from the cleaned datasets    
    
    if water == 'CW':       
        T_water_design = np.round(np.array([np.max(T_water_profiles_df,axis=0),
                       np.median(T_water_profiles_df,axis=0),
                       np.min(T_water_profiles_df,axis=0)]),1)
    elif water == 'WW':
        T_water_design = np.round(np.array([np.min(T_water_profiles_df,axis=0),
                       np.median(T_water_profiles_df,axis=0),
                       np.max(T_water_profiles_df,axis=0)]),1) 
    else:
        raise ValueError('Invalid input for seawater. Please select "CW" for cold deep seawater or "WW" for warm surface seawater.')
            
    
    coordinates = np.delete(coordinates,nan_columns[1],axis=0)
    dist_shore = np.delete(dist_shore,nan_columns[1],axis=1)
    inputs['dist_shore'] = dist_shore
    eff_trans = np.delete(eff_trans,nan_columns[1],axis=1)
    inputs['eff_trans'] = eff_trans
    
    ## Here we store the cleaned datasets as h5 files so that it does not have to recalculated later.
    
    filename = f'T_{depth}m_2011_{studied_region}.h5'.replace(" ","_")   
    T_water_profiles_df.to_hdf(new_path + filename,key='T_water_profiles',mode='w')
    pd.DataFrame(T_water_design).to_hdf(new_path + filename,key='T_water_design')
    pd.DataFrame(dist_shore).to_hdf(new_path + filename,key='dist_shore')
    pd.DataFrame(eff_trans).to_hdf(new_path + filename,key='eff_trans')
    pd.DataFrame(coordinates).to_hdf(new_path + filename,key='coordinates')
    pd.DataFrame(nan_columns[1]).to_hdf(new_path + filename,key='nan_columns')
               
    print(f'Processing {filename} successful. h5 temperature profiles exported.\n')
            
    return T_water_profiles, T_water_design, coordinates, T_water_profiles_df.index, inputs, nan_columns
        
def load_temperatures(file,inputs):
    
    # If the h5 files for the cleaned seawater temperature data already exists, it is merely loaded with this function
    
    T_water_profiles_df = pd.read_hdf(file,key='T_water_profiles')
    timestamp = T_water_profiles_df.index
    T_water_profiles = np.array(T_water_profiles_df,dtype=np.float64)      
    T_water_design = np.array(pd.read_hdf(file,key='T_water_design'),dtype=np.float64)  
    
    inputs['dist_shore'] = np.array(pd.read_hdf(file,key='dist_shore'),dtype=np.float64)   
    inputs['eff_trans'] = np.array(pd.read_hdf(file,key='eff_trans'),dtype=np.float64)
    
    coordinates = np.array(pd.read_hdf(file,key='coordinates'),dtype=np.float64)
    nan_columns = np.array(pd.read_hdf(file,key='nan_columns'),dtype=np.float64)
     
    return T_water_profiles, T_water_design, coordinates, timestamp, inputs, nan_columns