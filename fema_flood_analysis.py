import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
gdf=gpd.read_file(r'/home/admin/Downloads/denver/denver/S_FLD_HAZ_AR.shp')
print (gdf.shape)
print (gdf.head())
gdf.plot(cmap='jet')
plt.show()