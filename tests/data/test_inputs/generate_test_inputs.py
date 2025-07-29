import xarray

ds = xarray.tutorial.load_dataset("air_temperature")
ds_1x1 = ds.isel(lat=[0], lon=[0])
ds_1x1.to_netcdf("point_dataset.nc")
