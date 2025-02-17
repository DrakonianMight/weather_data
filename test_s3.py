import xarray as xr
import s3fs

fs = s3fs.S3FileSystem(anon=False)
zarr_path = 's3://arn:aws:s3:::exampleapidata/ECMWF/20250213_00.zarr'

# Open dataset in read-only mode
dataset = xr.open_zarr(
        store=s3fs.S3Map(
            root=zarr_path, s3=fs, check=False
        )
    )