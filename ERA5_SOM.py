"""
This python code reads in ERA5 data and passes it to the "blossom" program to train a SOM. 
After SOM training, composites are calculated, plotted, and saved.
To change SOM hyperparameters, the "blossom_settings.json5" file must be edited
Written by Lauren Getker, adapted from codes written by Maria Molina, Gary Lackmann, and Trevor Campbell
"""
#Package imports
import xarray as xr
import numpy as np
import pandas as pd
import matplotlib.pylab as plt
from time import time
from sys import stdout
import os
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.feature import NaturalEarthFeature
import metpy
import metpy.calc as mpcalc
from metpy.units import units
import glob
from blossom import blossom
"""
Data user settings
"""
# Grab desired ERA5 files using glob.glob*: here, I am getting DJF dates from the years 2000 - 2009
# *ERA5 is formatted with one file for each variable for each day. Outputs are hourly
# *make sure to use the sorted() function!!
files = sorted(glob.glob("/glade/collections/rda/data/ds633.0/e5.oper.an.pl/200*12/e5.oper.an.pl.128_129_z.ll025sc.*.nc")) \
        + sorted(glob.glob("/glade/collections/rda/data/ds633.0/e5.oper.an.pl/200*01/e5.oper.an.pl.128_129_z.ll025sc.*.nc")) \
        + sorted(glob.glob("/glade/collections/rda/data/ds633.0/e5.oper.an.pl/200*02/e5.oper.an.pl.128_129_z.ll025sc.*.nc"))
print(len(files))

#Select a pressure level in hPa
p_level = 500

#Variable name
var_name = 'Z'

#Westernmost longitude for subsetting. Choose -180 to 180
wlon = -130

#Easternmost latitude for subsetting. Choose -180 to 180
elon = -60

#Southernmost latitude for subsetting. Choose -90 to 90
slat = 20

#Northernmost latitude for subsetting.Choose -90 to 90
nlat = 55

#The map projection you would like to use. You may need to change the central longitude depending on domain
projection=ccrs.Mercator(central_longitude = 0)

#SOM rows
rows = 4

#SOM columns
cols = 4

"""
Constants
"""
#acceleration of gravity for geopotential conversion
g0 = 9.80665

#for converting longitudes
l0 = 360 

#Error message
coord_error = "Coordinates out of bounds."

"""
Error checking
"""
#Converting longitudes from (-180, 180) to (0, 360)
if elon < 0:
    elon = elon + 360
if wlon < 0:
    wlon = wlon + 360

#Are coordinates within bounds?
if (wlon > 360 or wlon < 0):
    sys.exit(coord_error)
if (elon > 360 or elon < 0):
    sys.exit(coord_error)
if (slat > 90 or slat < -90):
    sys.exit(coord_error)
if (nlat > 90 or nlat < -90):
    sys.exit(coord_error)
if (slat > nlat or wlon > elon):
    sys.exit(coord_error)
    
"""
End user settings
"""

dates = []
for i in range(len(files)): #Loop through each file
    print(str(i) + "/" + str(len(files)))
    ncfile = files[i]
    ds = xr.open_dataset(ncfile)
    times = ds['time'].values
    dates.append(times[0])
    ds_sub = ds.sel(level=p_level, time = times[0]) #subset by time and level
    lats = ds_sub['latitude'].values
    lons = ds_sub['longitude'].values
    variable = ds_sub[var_name].values / g0  #Convert geopotential to geopotential height
    dsnew = xr.DataArray(variable, coords=[lats, lons], dims=['lat', 'lon'])
    if i == 0: 
        dscatold = dsnew
    else:
        dscatold = xr.concat([dscatold,dsnew], dim='time')

if len(dates) == 0:
    sys.exit("Hmmm, it looks like there's no data. Are you sure you entered the file names correctly?")

da = xr.DataArray(dscatold[:, :, :], coords=[dates, lats, lons], dims=['time', 'lat', 'lon'])
da.attrs['standard_name'] = str(p_level) + " " + var_name

#Subset the data.
da_sub = da.where((da['lat']<nlat) & (da['lat']>slat) &  (da['lon']>wlon) & (da['lon']<elon), drop = True)
#redefine lats and lons after subsetting.
lats = da_sub['lat'].values
lons = da_sub['lon'].values
"""
SOM dimension sensitivity testing
"""
"""
count = 0
q = np.zeros([6])
t = np.zeros([6])
rows_arr = np.arange(1,5,1)
cols_arr = np.arange(1,5,1)
for i in rows_arr:
    SOM = blossom(da_sub, i, i)
    SOM.make_SOM()
    q[count] = SOM.q_err
    t[count] = SOM.t_err
    count += 1
    
fig, ax1 = plt.subplots()
ax2 = ax1.twinx()
ax1.plot(np.arange(1,5,1), q, color = 'blue', label = "Quantization error")
ax2.plot(np.arange(1,5,1), t, color = 'red', label = "Topographic error")
ax1.set_xlabel("SOM Dimension (square)")
ax1.set_ylabel("Quantization error")
ax2.set_ylabel("Topographic error")
ax1.legend(loc=0)
ax2.legend(loc=0)
plt.savefig("mpas_data_dims_test.png", bbox_inches = 'tight')
"""

"""
Train SOM
"""
SOM = blossom(da_sub, rows, cols) #create blossom object
SOM.train_SOM() #train SOM
SOM.save_SOM() #save composites as netCDF
"""
Visualization. You'll want to change some things here, such as plot titles, contour levels, and map extent!
"""
fig, axs = plt.subplots(SOM.rows, SOM.cols, subplot_kw={'projection': projection}, figsize=(24,12))  #Fig size may need to be changed to look nice.
mapnum = 0 
#Loop through each SOM node
for x in range(0,SOM.rows):
    for y in range(0,SOM.cols):
        data = som_data[x][y]
        axs[x,y].set_extent([elon,wlon,slat,nlat],crs=ccrs.PlateCarree())  #subset to a specific region
        axs[x,y].add_feature(cfeature.STATES, edgecolor='black')  #Add US states
        axs[x,y].add_feature(cfeature.COASTLINE, edgecolor='black')  #Add coastlines
        gl = axs[x,y].gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False)
        gl.top_labels=False   # suppress top grid labels
        gl.right_labels=False # suppress right grid labels
        axs[x,y].set_title(f"Cases: {len(SOM.get_cases(x,y))}")  #set title
        cs = axs[x,y].contourf(lons, lats, data, cmap = 'jet', transform=ccrs.PlateCarree(), levels = 30)#np.arange(5300, 6000, 30))
        mapnum = mapnum + 1

fig.suptitle("DJF geopotential height patterns", fontsize = 24)
cbar = plt.colorbar(cs,ax=fig.get_axes(), pad=0.04)
cbar.set_label(str(p_level) + " " + var_name, fontsize = 16)

plt.savefig("500_ht_alldates.png", bbox_inches = 'tight')
