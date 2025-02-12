import xarray as xr

# Define input and output file paths
GRIB_FILE = "../data/example.grib2"  # Replace with your actual GRIB2 file
ZARR_FILE = "../data/example.zarr"  # Desired Zarr output directory

# Open the GRIB2 file using cfgrib
ds = xr.open_dataset(GRIB_FILE, engine="cfgrib")

# Save as Zarr format
ds.to_zarr(ZARR_FILE, mode="w")

print(f"Conversion successful! Zarr dataset saved at: {ZARR_FILE}")

