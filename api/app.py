from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import xarray as xr
import numpy as np
import os

# Define the Zarr dataset path
ZARR_PATH = "../data/example.zarr"

if not os.path.exists(ZARR_PATH):
    raise RuntimeError(f"Zarr dataset not found at {ZARR_PATH}")

# Open the dataset with Dask enabled
ds = xr.open_zarr(ZARR_PATH, chunks={})

# Detect latitude and longitude variable names
lat_var = next((var for var in ["lat", "latitude"] if var in ds), None)
lon_var = next((var for var in ["lon", "longitude"] if var in ds), None)

if not lat_var or not lon_var:
    raise RuntimeError("Could not detect latitude and longitude dimensions in the Zarr dataset.")

# Get dataset bounds
lat_min, lat_max = ds[lat_var].min().item(), ds[lat_var].max().item()
lon_min, lon_max = ds[lon_var].min().item(), ds[lon_var].max().item()

# Initialize FastAPI app
app = FastAPI()

class LocationRequest(BaseModel):
    locations: list[tuple[float, float]]  # List of (latitude, longitude) tuples

def replace_nan_with_none(data):
    """Recursively replace NaN with None for JSON serialization."""
    if isinstance(data, dict):
        return {key: replace_nan_with_none(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [replace_nan_with_none(item) for item in data]
    elif isinstance(data, float) and np.isnan(data):
        return None
    elif isinstance(data, float) and np.isinf(data):
        return None  # Alternatively, return a string 'Inf' if preferred
    return data

@app.post("/extract/")
def extract_data(request: LocationRequest):
    lat_vals, lon_vals = zip(*request.locations)

    # Ensure all requested points are within bounds
    for lat, lon in zip(lat_vals, lon_vals):
        if not (lat_min <= lat <= lat_max and lon_min <= lon <= lon_max):
            raise HTTPException(status_code=400, detail=f"Coordinates ({lat}, {lon}) are out of bounds.")

    try:
        # Parallelized lookup using vectorized selection
        nearest = ds.sel({lat_var: list(lat_vals), lon_var: list(lon_vals)}, method="nearest")

        # Convert results to a dictionary
        results = []
        for i, (lat, lon) in enumerate(zip(lat_vals, lon_vals)):
            data = {}
            
            for var in ds.data_vars:
                var_data = nearest[var].values[i]  # This could be an array or a scalar

                # Check if the variable data is scalar or array
                if np.isscalar(var_data):  
                    data[var] = var_data.item()
                elif var_data.ndim == 1:  # Handle 1D arrays (e.g., time series)
                    data[var] = var_data.tolist()
                else:
                    data[var] = var_data.tolist()  # General case for multi-dimensional arrays

            # Handle NaN cases (e.g., for ocean models or locations with missing data)
            # Replace NaN values with None for JSON serialization
            data = replace_nan_with_none(data)

            # If all values are NaN (i.e., no data available), append a message
            if all(value is None for value in data.values()):
                results.append({"lat": lat, "lon": lon, "message": "No data available for this location (likely not in the ocean)."})
            else:
                results.append({"lat": lat, "lon": lon, "data": data})

        return {"results": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
