# -*- coding: utf-8 -*-
"""
Created on Fri Mar  3 16:08:37 2023

@author: jkalanger
"""

import requests
import getpass
import netCDF4
import xarray as xr
import pandas as pd
import numpy as np
import datetime
import os
import time

## We use seawater temperature data from CMEMS for our OTEC analysis. If the data does not exist in the work folder yet, then it is downloaded with the function
## below. Essentially, we contact CMEMS's servers via an url created from input data like desired year, water depth, coordinates, etc, and download the data
## after the connection to the server has been established successfully.

def download_data(cost_level,inputs,studied_region,new_path):
    
    ## The csv file below stores all countries and territories that have OTEC resources, their coordinates, and electricity demand in 2019.
    
    credentials = list(pd.read_csv('credentials.txt',delimiter=','))
    user = credentials[0]
    password = credentials[1] #getpass.getpass("Enter your password: ")
    
    regions = pd.read_csv('download_ranges_per_region.csv',delimiter=';',encoding='latin-1')  
        
    if np.any(regions['region'] == studied_region):
        
        parts = regions['region'].value_counts()[studied_region]
        
        ## OTEC uses warm surface seawater to evaporate a work fluid, while cold deep-sea water is used to condense said work fluid. We download
        ## seawater temperature data from depths representing warm water (WW) and cold water (CW). 
        
        depth_WW = inputs['length_WW_inlet']
        depth_CW = inputs['length_CW_inlet']
        
        ## Due to download limitations, we only download one year of data. We chose the year 2011, but any year between 1994 and 2012 could also work.
        
        date_start = inputs['date_start']
        date_end = inputs['date_end']
        
        ## We store the filenames and their paths, so that the seawater temperature data can be accessed by pyOTEC later.
        
        files = []
        
        for depth in [depth_WW,depth_CW]:
            for part in range(0,parts):
                                
                ## The coordinates for the download are pulled from the csv file. Alternatively, the user could define the coordinates themselves.
            
                north = float(regions[regions['region']==studied_region]['north'].iloc[part])
                south = float(regions[regions['region']==studied_region]['south'].iloc[part])
                west = float(regions[regions['region']==studied_region]['west'].iloc[part])
                east = float(regions[regions['region']==studied_region]['east'].iloc[part])
                                             
                start_time = time.time()
                filename = f'T_{round(depth,0)}m_{date_start[0:4]}_{studied_region}_{part+1}.nc'.replace(" ","_")
                filepath = os.path.join(new_path, filename)
                files.append(filepath)
                
                if os.path.isfile(filepath):           
                    print('File already exists. No download necessary.')
                    continue
                else:  
                    
                    ## here we construct the URL with which we request the data from CMEMS's servers.
                    
                    motu_request = ('python -m motuclient --motu https://my.cmems-du.eu/motu-web/Motu --service-id GLOBAL_MULTIYEAR_PHY_001_030-TDS --product-id cmems_mod_glo_phy_my_0.083_P1D-m --' +
                                    f'longitude-min {west} --longitude-max {east} --latitude-min {south} --latitude-max {north} --date-min {date_start} --date-max {date_end} ' +
                                    f'--depth-min {depth} --depth-max {depth} --variable thetao --out-dir "{studied_region.replace(" ","_")}" --out-name {filename} --user "{credentials[0]}" --pwd "{credentials[1]}"')
                    
                    os.system(motu_request)
          
                    end_time = time.time()
                    print(f'{filename} saved. Time for download: ' + str(round((end_time-start_time)/60,2)) + ' minutes.')
        
        return files    
        
    else:
        raise ValueError('Entered region not valid. Please check for typos and whether the region is included in "download_ranges_per_region.csv"')


def data_processing(files,sites_df,inputs,studied_region,new_path,water,nan_columns = None):
    
    ## Here we convert the pandas Dataframe storing site-specific data into a numpy array
    
    sites = np.vstack((sites_df['longitude'],sites_df['latitude'],sites_df['dist_shore'],sites_df['id'])).T
    
    ## The "for file in files" was made for countries and territories that stretch across the East/West border, like Fiji and New Zealand.
    ## These regions are split into two parts that cover the regions' Eastern and Western side, respectively.

    for file in files:
        ## It can happen that a corruped nc file is downloaded with 1 kB size. In that case, reading the file would raise an error. So, we try to read the file,
        ## and if it does not work, it means that the file is corrupted and needs to be downloaded again.
        try:
            T_water_nc = netCDF4.Dataset(file,'r')       
        except:
            raise Warning(f'{file} was not downloaded successfully. Please try downloading the file later.')
    
    ## Here, we convert the timestamp to year-month-day hour:minute:second    
    
    time = T_water_nc.variables['time'][:]
    time_origin = datetime.datetime.strptime(inputs['time_origin'], '%Y-%m-%d %H:%M:%S') 
    timestamp = [time_origin + datetime.timedelta(hours=step) for idx,step in enumerate(time)]  
    
    ## Earlier, we downloaded the data across a rectangular field defined by the input coordinates. However, not every data point is suitable
    ## for OTEC (e.g. points on land, too shallow/ deep water, inside marine protection areas, etc). In this loop, we check which downloaded data points
    ## could be occupied by OTEC plants, and store their coordinates and temperature profiles in a numpy array
    
    T_water_profiles = np.zeros((time.shape[0],0),dtype=np.float64)
    coordinates = np.zeros((0,2),dtype=np.float64)
    dist_shore = np.zeros((1,0),dtype=np.float64)
    id_sites = np.zeros((1,0),dtype=np.float64)
    
    for file in files:
        T_water_nc = netCDF4.Dataset(file,'r')             
        latitude = T_water_nc.variables['latitude'][:]
        longitude = T_water_nc.variables['longitude'][:]
        depth = int(T_water_nc.variables['depth'][:])
        T_water = T_water_nc.variables['thetao'][:]
        
        data_points = np.round([(idx_lon,idx_lat,lon,lat) for idx_lon,lon in enumerate(longitude) for idx_lat,lat in enumerate(latitude)],3)
        
        for index,point in enumerate(data_points):
            match = np.array(np.where((point[2]==sites[:,0]) & (point[3]==sites[:,1])))
            if match.size != 0:
                if T_water_profiles.shape[1] == 0:
                    coordinates = [point[2],point[3]]
                    dist_shore = sites[match,2]
                    id_sites = sites[match,3]
                    T_water_profiles = (np.array(T_water[:,:,int(point[1]),int(point[0])],dtype=np.float64))
                else:
                    coordinates = np.vstack((coordinates, [point[2],point[3]]))
                    dist_shore = np.hstack((dist_shore, sites[match,2]))
                    id_sites = np.hstack((id_sites, sites[match,3]))
                    T_water_profiles = np.hstack((T_water_profiles,(np.array(T_water[:,:,int(point[1]),int(point[0])],dtype=np.float64))))
            else:
                pass
    
    ## After obtaining the relevant CMEMS points, we calculate power transmission losses from OTEC plant offshore to the public grid onshore in kilometres.
    
    eff_trans = np.empty(np.shape(dist_shore),dtype=np.float64)
    # AC cables for distances below or equal to 50 km, source: Fragoso Rodrigues (2016) 
    eff_trans[dist_shore <= inputs['threshold_AC_DC']] = 0.979-1*10**-6*dist_shore[dist_shore <= 50]**2-9*10**-5*dist_shore[dist_shore <= 50]  
    # DC cables for distances beyond 50 km, source: Fragoso Rodrigues (2016) 
    eff_trans[dist_shore > inputs['threshold_AC_DC']] = 0.964-8*10**-5*dist_shore[dist_shore > 50]  

    ## Some data might either be missing (no timestamp) or faulty (e.g. T = -30000)
    ## First, we remove the faulty values

    T_water_profiles[T_water_profiles < 0] = np.nan
    
    ## Here, we resample the dataset to the temporal resolution given in the parameters_and_constants file
    ## and to fill previously missing steps with NaN, which are then filled via linear interpolation
    T_water_profiles_df = pd.DataFrame(T_water_profiles)
    if T_water_profiles_df.shape[1] == 1:
        T_water_profiles_df.columns = [str(coordinates[0]) + '_' + str(coordinates[1])]
    else:
        T_water_profiles_df.columns = [str(val[0]) + '_' + str(val[1]) for idx,val in enumerate(coordinates)]
    T_water_profiles_df['time'] = timestamp
    T_water_profiles_df = T_water_profiles_df.set_index('time').asfreq(f'{inputs["t_resolution"]}')       
    T_water_profiles_df = T_water_profiles_df.interpolate(method='linear')
    
    # Calculating interquartiles. With a factor 3, we are less strict with outliers than the convention of 1.5
    # With this, we want to account for extreme seawater temperature conditions that would otherwise be removed from the dataset
    r = T_water_profiles_df.rolling(window=30)
    mps = (r.quantile(0.75) - r.quantile(0.25))*3 

    T_water_profiles_df[(T_water_profiles_df < T_water_profiles_df.quantile(0.25) - mps) |
                        (T_water_profiles_df > T_water_profiles_df.quantile(0.75) + mps)] = np.nan
    
    T_water_profiles_df = T_water_profiles_df.interpolate(method='linear')
    
    ## In some case, points don't have any data at all. If there are profiles solely consisting of NaN, they are removed from the dataset
    
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
    id_sites = np.delete(id_sites,nan_columns[1],axis=1)
    
    ## Here we store the cleaned datasets as h5 files so that it does not have to recalculated later.
    
    year = inputs['date_start'][0:4]
    
    filename = f'T_{round(depth,0)}m_{year}_{studied_region}.h5'.replace(" ","_")   
    T_water_profiles_df.to_hdf(new_path + filename,key='T_water_profiles',mode='w')
    pd.DataFrame(T_water_design).to_hdf(new_path + filename,key='T_water_design')
    pd.DataFrame(dist_shore).to_hdf(new_path + filename,key='dist_shore')
    pd.DataFrame(eff_trans).to_hdf(new_path + filename,key='eff_trans')
    pd.DataFrame(coordinates).to_hdf(new_path + filename,key='coordinates')
    pd.DataFrame(nan_columns[1]).to_hdf(new_path + filename,key='nan_columns')
    pd.DataFrame(id_sites).to_hdf(new_path + filename,key='id_sites')
               
    print(f'Processing {filename} successful. h5 temperature profiles exported.\n')
            
    return T_water_profiles, T_water_design, coordinates, id_sites, T_water_profiles_df.index, inputs, nan_columns
        
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
    
    id_sites = np.array(pd.read_hdf(file,key='id_sites'),dtype=np.float64)
     
    return T_water_profiles, T_water_design, coordinates, id_sites, timestamp, inputs, nan_columns