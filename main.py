from astropy.table import Table
import multiprocessing, psutil
from sklearn.neighbors import BallTree
import numpy as np
import io
from io import StringIO
import pandas as pd
import multiprocessing, psutil
import math 
from scipy import special
import joblib


from funciones import fetch_table_element, find_y_in_x, duplicates_msk, unique_value_msk, get_distance_arcsec, get_delta_mu_and_sigma, procesar_csv


columnas = ['source_id', 'ra', 'dec', 'phot_g_mean_mag']
archivo_csv = input("Ingrese el nombre del archivo CSV: ")
tab, estrellas = procesar_csv(archivo_csv, columnas)

size_max_pc = 5 # max projected separation out to which to search
dispersion_max_kms = 5 # max velocity difference in kms
ra, dec, pmra, pmdec, parallax, parallax_error, pmra_error, pmdec_error, G = fetch_table_element(['ra', 'dec', 'pmra', 'pmdec', 'parallax', 'parallax_error', 'pmra_error', 'pmdec_error', 'phot_g_mean_mag'], tab )

s_max_cluster = 206265*size_max_pc
theta_max_radians = s_max_cluster/(1000/parallax)/3600 * np.pi/180
coords = np.vstack([dec*np.pi/180, ra*np.pi/180,]).T
tree = BallTree(coords[G < 18], leaf_size = 10, metric = 'haversine') # build tree of all stars brighter than 18

# data for stars brighter than G = 18
ra_b, dec_b, pmra_b, pmdec_b, parallax_b, parallax_error_b, pmra_error_b, pmdec_error_b, G_b = ra[G < 18], dec[G < 18], pmra[G < 18], pmdec[G < 18], parallax[G < 18], parallax_error[G < 18], pmra_error[G < 18], pmdec_error[G < 18], G[G < 18]

Nblock = 20000 # how many stars to process at once per core
Nmax = len(coords)//Nblock + 1 
sigma_cut = 2 # how many sigma tolerance 

def query_this_j1(j):
    
    # see how far along we are and make sure we aren't running out of memory.
    print(j, j*Nblock/len(coords),  psutil.virtual_memory().percent)

    # find the stars in this block
    start_idx = j*Nblock
    end_idx = min((j+1)*Nblock, len(coords))
    msk = np.arange(len(coords))[start_idx:end_idx]
    
    if len(msk) == 0: # check if msk is empty
        return np.zeros(Nblock)
    
    # find their companions and angular distances
    these_inds, these_dists = tree.query_radius(coords[msk], r = theta_max_radians[msk], return_distance = True)      
    
    # copy astrometry of stars in this block  
    parallax_, parallax_error_, pmra_, pmra_error_, pmdec_, pmdec_error_ = parallax[msk], parallax_error[msk], pmra[msk], pmra_error[msk], pmdec[msk], pmdec_error[msk] 

    # for each star, see how many of the companions within 5 pc (projected) have consistent parallax and similar proper motion 
    N_neighbors = np.zeros(len(parallax_))
    for i, idxs in enumerate(these_inds):
        thetas_arcsec = these_dists[i]*180/np.pi*3600
        d_par_over_sigma = np.abs(parallax_[i] - parallax_b[idxs])/np.sqrt(parallax_error_[i]**2 + parallax_error_b[idxs]**2)
        delta_mu, sigma_delta_mu = get_delta_mu_and_sigma(pmra1 = pmra_[i], pmdec1 = pmdec_[i], 
            pmra2 = pmra_b[idxs], pmdec2 = pmdec_b[idxs], pmra_error1 = pmra_error_[i], 
            pmdec_error1 = pmdec_error_[i], pmra_error2 = pmra_error_b[idxs], 
            pmdec_error2 = pmdec_error_b[idxs])
            
        mu_max = 0.21095*dispersion_max_kms*parallax_[i]            
        neighbors = (delta_mu < mu_max + sigma_cut*sigma_delta_mu) & (d_par_over_sigma < sigma_cut) & (thetas_arcsec > 1e-3) # theta > 1e-3 arcsec to make sure you don't count yourself as a neighbor
        N_neighbors[i] = np.sum(neighbors) 
    return N_neighbors

all_result = []
for j in range(Nmax):
    result = query_this_j1(j)
    all_result.append(result)

N_neighbors = np.concatenate(all_result)

N_neighbors = N_neighbors[:len(coords)]

buffer = io.BytesIO()

np.savez(buffer, source_id=fetch_table_element('source_id', tab), N_neighbors=N_neighbors)

buffer.seek(0)

tmp = np.load(buffer)


parallax_sigma_limit = 3 # only accept pair with parallaxes within 3 sigma of each other
theta_arcsec_min = 4 # limit below which we'll accept parallaxes within 6 sigma of each other. 

crowded = np.in1d(fetch_table_element('source_id', tab),  tmp['source_id'][tmp['N_neighbors'] > 30]); tmp.close()
tab = tab[~crowded] # 57889221 stars survive 


source_id, ra, dec, G, parallax, parallax_error, pmra, pmdec, pmra_error, pmdec_error  = fetch_table_element(['source_id', 'ra', 'dec', 'phot_g_mean_mag', 'parallax', 'parallax_error', 'pmra', 'pmdec', 'pmra_error', 'pmdec_error'], tab)

s_max_au = 3600*180/np.pi # 206265 au = 1 pc
theta_max_radians = s_max_au/(1000/parallax)/3600 * np.pi/180 # angular separation corresponding to s = 1 pc
coords = np.vstack([ dec*np.pi/180, ra*np.pi/180]).T
tree = BallTree(coords, leaf_size = 20, metric = 'haversine')
print('built tree') 


Nblock = 200000 # how many stars to process at once
Nmax = (len(coords)-1)//Nblock + 1 # how many blocks total
all_indices = np.arange(len(coords))

def query_this_j2(j):
    '''
    function to deal with Nblock stars. 
    '''
    # see how far along we are and make sure we aren't running out of memory.
    print(j, j*Nblock/len(coords),  psutil.virtual_memory().percent) 
    
    # find the stars in this block
    msk = (all_indices >= int(j*Nblock)) & (all_indices < int((j+1)*Nblock))
    these_nums = all_indices[msk]
    
    # find possible companions and their angular separations. 
    these_inds, these_dists = tree.query_radius(coords[msk], r = theta_max_radians[msk], return_distance = True)

    # astrometry for stars in this block 
    parallax_block, parallax_error_block, pmra_block, pmra_error_block, pmdec_block, pmdec_error_block, G_block = parallax[msk], parallax_error[msk], pmra[msk], pmra_error[msk], pmdec[msk], pmdec_error[msk], G[msk]
    
    # to hold indices of pairs that do pass cuts. 
    these_star1s, these_star2s = [], [] 
    
    # loop through possible companions and see if they pass parallax and proper motion cuts. 
    for i, idxs in enumerate(these_inds):
        thetas_arcsec = these_dists[i]*180/np.pi*3600
        brighter_parallax = np.copy(parallax[idxs]) 
        brighter_parallax[G[idxs] > G_block[i]] = parallax_block[i] # parallax of the brighter component 
    
        d_par_over_sigma = np.abs(parallax_block[i] - parallax[idxs])/np.sqrt(parallax_error_block[i]**2 + parallax_error[idxs]**2)
        delta_mu, sigma_delta_mu = get_delta_mu_and_sigma(pmra1 = pmra_block[i], pmdec1 = pmdec_block[i], 
            pmra2 = pmra[idxs], pmdec2 = pmdec[idxs], pmra_error1 = pmra_error_block[i], 
            pmdec_error1 = pmdec_error_block[i], pmra_error2 = pmra_error[idxs], pmdec_error2 = pmdec_error[idxs])
        
        # avoid divided-by-zero warnings when calculating delta_mu_orbit for theta = 0 (pairing star with itself)
        delta_mu_orbit = np.zeros(len(thetas_arcsec))
        mm = thetas_arcsec == 0
        delta_mu_orbit[mm] = 1e9
        delta_mu_orbit[~mm] = 0.44428*brighter_parallax[~mm]**(3/2)*thetas_arcsec[~mm]**(-1/2)
        sep_AU = 1000/brighter_parallax * thetas_arcsec
        
        # b = 3 at theta > 4 arcsec; b = 6 at theta < 4 arcsec
        max_parallax_diff = np.ones(len(thetas_arcsec))*parallax_sigma_limit
        max_parallax_diff[thetas_arcsec < theta_arcsec_min] = 2*parallax_sigma_limit
        
        # Enforce the parllax and proper motion cuts. Theta > 0 means: don't get paired with yourself
        m = (d_par_over_sigma < max_parallax_diff) & (delta_mu < delta_mu_orbit + 2*sigma_delta_mu) & (thetas_arcsec > 0.001) & (sep_AU < s_max_au) 
        if np.sum(m):
            for k in range(np.sum(m)):
                these_star1s.append(these_nums[i])
                these_star2s.append(idxs[m][k])
    return these_star1s, these_star2s

all_result = []
for j in range(Nmax):
    result = query_this_j2(j)
    all_result.append(result)

star1s, star2s = np.concatenate(np.array(all_result).T[0]),  np.concatenate(np.array(all_result).T[1])
print(f'total length of catalog is {len(star1s)}')

# make a new table. each row corresponds to a different pair.
from astropy.table import Table
new_cat = Table()    
for col in tab.colnames:
    new_cat[col+'1'] = tab[col][star1s]
    new_cat[col+'2'] = tab[col][star2s]

# remove duplicates (pairs where star 1 and star 2 are switched)
sid1, sid2 = fetch_table_element(['source_id1', 'source_id2'], new_cat)
joint_ids = np.vstack([sid1, sid2]).T
sorted_joint = np.sort(joint_ids, axis=1)
joint_1d = np.core.defchararray.add( sorted_joint.T[0].astype(str),  sorted_joint.T[1].astype(str)  )
dups = duplicates_msk(joint_1d)   
new_cat = new_cat[~dups]
print(f'after finding {np.sum(dups)} exact duplicates, the new length is {len(new_cat)}')

# make the brighter star the star "1" and the fainter star "2"
G1, G2 = fetch_table_element(['phot_g_mean_mag1', 'phot_g_mean_mag2'], new_cat)
switch = G1 > G2
colnames =  [ c[:-1] for c in new_cat.colnames if c[-1]=='1'] 
for col in colnames:
    new_cat[col+'1'][switch], new_cat[col+'2'][switch] = new_cat[col+'2'][switch], new_cat[col+'1'][switch]


# calculate angular and physical separations. 
ra1, dec1, ra2, dec2, parallax1, id1, id2 = fetch_table_element(['ra1', 'dec1', 'ra2', 'dec2', 'parallax1', 'source_id1', 'source_id2'], new_cat)
theta_arcsec = get_distance_arcsec(ra1 = ra1, dec1 = dec1, ra2 = ra2, dec2 = dec2)
new_cat['pairdistance'] = theta_arcsec/3600
new_cat['sep_AU'] = 1000/parallax1 * theta_arcsec


# remove triples. first get rid of cases where id1 or id2 have duplicates; i.e. one star with two companions 
new_cat = new_cat[unique_value_msk(id1) & unique_value_msk(id2)]

# now get cases where elements of id1 are in id2 or vice versa.
id1, id2 = fetch_table_element(['source_id1', 'source_id2'], new_cat )
new_cat = new_cat[~ (np.in1d(id1, id2) | np.in1d(id2, id1) )]
print(f'after removing triples, there are {len(new_cat)} pairs')

# remove clusters
size_max_pc = 5 # count as a neighbor if projected separation within 5 pc
sigma_cut = 2 # count as a neighbor if parallax consistent within 2 sigma
dispersion_max_kms = 5 # count as a neighbor if plane-of-sky velocity is within 5 km/s

ra, dec, pmra, pmdec, parallax, parallax_error, pmra_error, pmdec_error = fetch_table_element(['ra1', 'dec1', 'pmra1', 'pmdec1', 'parallax1', 'parallax_error1', 'pmra_error1', 'pmdec_error1'], new_cat )

theta_max_radians_bin = size_max_pc*parallax/1000


# use the same approach we used to find binary candidates. Now look for neighboring binaries. 
coords_bin = np.vstack([dec*np.pi/180, ra*np.pi/180,]).T
tree_bin = BallTree(coords_bin, leaf_size = 10, metric = 'haversine')

Nblock = 20000
Nmax = (len(coords_bin)-1)//Nblock + 1
indices = np.arange(len(coords_bin))


def query_this_j3(j):
    print(j, j*Nblock/len(coords_bin),  psutil.virtual_memory().percent)

    msk = (indices >= int(j*Nblock)) & (indices < int((j+1)*Nblock))
    these_inds, these_dists = tree_bin.query_radius(coords_bin[msk], r = theta_max_radians_bin[msk], 
        return_distance = True)        
    parallax_block, parallax_error_block, pmra_block, pmra_error_block, pmdec_block, pmdec_error_block = parallax[msk], parallax_error[msk], pmra[msk], pmra_error[msk], pmdec[msk], pmdec_error[msk] 

    N_neighbors = np.zeros(len(parallax_block))
    for i, idxs in enumerate(these_inds):
        thetas_arcsec = these_dists[i]*180/np.pi*3600
        d_par_over_sigma = np.abs(parallax_block[i] - parallax[idxs])/np.sqrt(parallax_error_block[i]**2 + parallax_error[idxs]**2)
        delta_mu, sigma_delta_mu = get_delta_mu_and_sigma(pmra1 = pmra_block[i], pmdec1 = pmdec_block[i], 
            pmra2 = pmra[idxs], pmdec2 = pmdec[idxs], pmra_error1 = pmra_error_block[i], 
            pmdec_error1 = pmdec_error_block[i], pmra_error2 = pmra_error[idxs], pmdec_error2 = pmdec_error[idxs])
            
        mu_max = 0.21095*dispersion_max_kms*parallax_block[i]                
        neighbors = (delta_mu < mu_max + sigma_cut*sigma_delta_mu) & (d_par_over_sigma < sigma_cut) & (thetas_arcsec > 1e-3)
        N_neighbors[i] = np.sum(neighbors) 
    return N_neighbors


all_result = []
for j in range(Nmax):
    result = query_this_j3(j)
    all_result.append(result)
N_neighbors = np.concatenate(all_result)

clean_cat = new_cat[N_neighbors < 2]


csv_data = StringIO()


clean_cat.write(csv_data, format='csv')

csv_data.seek(0)

df = pd.read_csv(csv_data)

loaded_model = joblib.load('knn_model.joblib')

df_copy_para_KNR = df[["ra1", "dec1"]].copy()

predictions = loaded_model.predict(df_copy_para_KNR)


df['sigma18'] = predictions

df1=df

df1['angularsepscaled']= np.log10(df['pairdistance']*3600)
df1['parallax']=4/df['parallax1']
df1['parallax_diff_error']=4*np.sqrt(pow(df['parallax_error1'],2)+ pow(df['parallax_error2'],2))

df1['g18_local_source_den']=4*np.log10(df['sigma18'])


pm1 = np.sqrt(df['pmra1']**2 + df['pmdec1']**2) # calcula el valor del proper motion
df['pm1'] = pm1
df1['tang_vel']=abs(df['pm1']*np.pi/180/60/60/1000/31536000*1/df['parallax1']*1000*3.086e13)/50
df1['norm_parallax_diff']=abs(df['parallax1']-df['parallax2'])/np.sqrt(pow(df['parallax_error1'],2)+ pow(df['parallax_error2'],2))

lammu=np.sqrt(pow(df['pmra1']-df['pmra2'],2)    +   pow(df['pmdec1']-df['pmdec2'],2))
muorbit=0.44*pow(df['parallax1'],3/2)*pow(df['pairdistance']*3600,-0.5)
parentesis=(pow(df['pmra_error1'],2)+pow(df['pmra_error2'],2))*pow(df['pmra1']-df['pmra2'],2) + (pow(df['pmdec_error1'],2)+pow(df['pmdec_error2'],2))*pow(df['pmdec1']-df['pmdec2'],2)
sigmalammu=1/lammu
sigmalammuf=sigmalammu*np.sqrt(parentesis)
propermotion=(lammu-muorbit)/sigmalammuf
df1['scaled_pm_diff']=2*special.erf(propermotion)

df2 =df1[['angularsepscaled','parallax','parallax_diff_error','g18_local_source_den','tang_vel','norm_parallax_diff','scaled_pm_diff']]

reglog_loaded = joblib.load('modelo_reglog.joblib')

y_pred_test = reglog_loaded.predict(df2)

# imprimir las predicciones
print("Predicciones:", y_pred_test)

df1['Predicciones'] = y_pred_test
df5 = df1[df1['Predicciones'] == 1]
df5 = df5.drop('Predicciones', axis=1)

df6= df1[df1['Predicciones'] == 0]
df6 = df6.drop('Predicciones', axis=1)


df5.to_csv('real_binary_catalog.csv', index=False)
df6.to_csv('fake_binary_catalog.csv', index=False)
