import pandas as pd
import numpy as np
from astropy.table import Table
import multiprocessing, psutil
from sklearn.neighbors import BallTree




def fetch_table_element(colname, table):
    '''
    avoid table['col'].data vs table['col'].data.data problems with masked arrays in astropy tables 
    '''
    if type(colname) == str:
        if type(table[colname].data.data) == memoryview:
            dat_ = table[colname].data
        else:
            dat_ = table[colname].data.data
    elif type(colname) == list:
        dat_ = []
        for col in colname:
            dat_.append(fetch_table_element(col, table))
    return dat_

def find_y_in_x(x, y):
    '''
    x and y are arrays. find the indices in x where the array is equal to values in y. 
    '''
    index = np.argsort(x)
    sorted_x = x[index]
    sorted_index = np.searchsorted(sorted_x, y)
    yindex = np.take(index, sorted_index, mode = "clip")
    mask = x[yindex] == y
    return yindex[mask]

def duplicates_msk(Array):
    '''
    Finds duplicate values of an array.
    Uses masking. Here Array should be a numpy array of ints. Behavior is undefined if array is of 
    lists, sets, etc. 
    '''
    Array = np.array(Array)
    m = np.zeros_like(Array, dtype=bool)
    m[np.unique(Array, return_index=True)[1]] = True
    return ~m
         
def unique_value_msk(x):
    '''
    returns true only if that value appears only once in the array
    '''
    uniq, counts = np.unique(x, return_counts=True)  
    unique_vals = uniq[counts == 1]
    w = find_y_in_x(x, unique_vals)
    is_unique = np.zeros(len(x), dtype = bool)
    is_unique[w] = True
    return is_unique

                    
def get_distance_arcsec(ra1, dec1, ra2, dec2):
    '''
    angular separations. coords are assumed to be in degrees
    '''
    ra_rad1, dec_rad1 = ra1*np.pi/180, dec1 * np.pi/180



    ra_rad2 = ra2*np.pi/180
    
    
    
    dec_rad2 = dec2 * np.pi/180
    d_ra, d_dec = ra_rad1 - ra_rad2, dec_rad1 - dec_rad2
    
    d_theta = 2*np.arcsin(np.sqrt(np.sin(0.5*d_dec)**2 + np.cos(dec_rad1)*np.cos(dec_rad2)*np.sin(0.5*d_ra)**2))
    d_theta_deg = 180/np.pi*d_theta
    d_theta_arcsec = d_theta_deg * 3600
    return d_theta_arcsec
    
     
def get_delta_mu_and_sigma(pmra1, pmdec1, pmra2, pmdec2, pmra_error1, 
    pmdec_error1, pmra_error2, pmdec_error2):
    '''
    Uses standard uncertainty propagation 
    Equations 4-5 of the paper. 

    assume that "1" is a float and "2" is an array
    '''
    delt_alpha, delt_delta = (pmra1 - pmra2)**2, (pmdec1 - pmdec2)**2
    delta_mu2 = delt_alpha + delt_delta
    
    try:
        lenn = len(pmra2) # checks whether pmra2 is an array 
        m = delta_mu2 == 0
        sigma2_delta_mu = np.zeros(len(pmra2))
        if np.sum(m):
            sigma2_delta_mu[m] = (pmra_error1**2 + pmra_error2[m]**2) + (pmdec_error1**2 + pmdec_error2[m]**2)
        if np.sum(~m):
            sigma2_delta_mu[~m] = ((pmra_error1**2 + pmra_error2[~m]**2) * (delt_alpha[~m]) + \
                (pmdec_error1**2 + pmdec_error2[~m]**2)*delt_delta[~m])/delta_mu2[~m]
    except: # pmra2 is a float 
        if delta_mu2 == 0:
            sigma2_delta_mu = pmra_error1**2 + pmra_error2**2 + pmdec_error1**2 + pmdec_error2**2
        else:
            sigma2_delta_mu = ((pmra_error1**2 + pmra_error2**2) * (delt_alpha) + \
                (pmdec_error1**2 + pmdec_error2**2)*delt_delta)/delta_mu2

    return np.sqrt(delta_mu2), np.sqrt(sigma2_delta_mu)

def procesar_csv(csv_file, columnas):
    estrellas = pd.read_csv(csv_file, usecols=columnas)
    tab = Table.read(csv_file)
    
    return tab, estrellas


