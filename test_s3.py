import xarray as xr
#import s3fs

#fs = s3fs.S3FileSystem(anon=False)
zarr_path = 's'

# Open dataset in read-only mode
dataset = xr.open_zarr(zarr_path)