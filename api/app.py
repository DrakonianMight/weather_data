import time
import os
import json
import xarray as xr
import numpy as np
import dask.array as da
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Tuple
from dask import delayed, compute

# Initialize FastAPI
app = FastAPI()

# Define the input model for locations and model info
class LocationRequest(BaseModel):
    locations: List[Tuple[float, float]]  # List of lat, lon tuples
    model: str  # Source model (e.g., ECMWF)
    model_run: str  # Model run (e.g., 12022025_00)

# Function to load a Zarr dataset based on model and model run
def load_zarr_dataset(model: str, model_run: str):
    # Define the path to the model's Zarr file
    zarr_directory = f"../data/{model}"

    if not os.path.exists(zarr_directory):
        raise HTTPException(status_code=404, detail="Model not available")

    # Construct the file name based on model run (e.g., 12022025_00.zarr)
    zarr_file = os.path.join(zarr_directory, f"{model_run}.zarr")

    if not os.path.exists(zarr_file):
        raise HTTPException(status_code=404, detail="Model run not found")

    # Load the Zarr dataset using xarray
    return xr.open_zarr(zarr_file)

# Function to extract data for a single location
def extract_data_for_location(lat: float, lon: float, zarr_data: xr.DataArray):
    try:
        # Check if the lat, lon is within the dataset bounds
        if lat < zarr_data.coords["latitude"].min() or lat > zarr_data.coords["latitude"].max():
            return {"lat": lat, "lon": lon, "message": "Latitude out of bounds"}
        if lon < zarr_data.coords["longitude"].min() or lon > zarr_data.coords["longitude"].max():
            return {"lat": lat, "lon": lon, "message": "Longitude out of bounds"}

        # Find the nearest indices for latitude and longitude
        lat_idx = np.abs(zarr_data.coords["latitude"] - lat).argmin()
        lon_idx = np.abs(zarr_data.coords["longitude"] - lon).argmin()

        # Extract the value (assuming the data is numeric, adjust for your dataset structure)
        data_value = zarr_data[lat_idx, lon_idx].compute()  # Use compute() for Dask arrays
        return {"lat": lat, "lon": lon, "data": data_value.tolist()}
    except Exception as e:
        return {"lat": lat, "lon": lon, "message": f"Error: {str(e)}"}

# Function to process a batch of locations in parallel
def extract_data_parallel(locations: List[Tuple[float, float]], zarr_data: xr.DataArray):
    results = []
    # Use Dask's delayed function to parallelize the extraction of data for each location
    tasks = [delayed(extract_data_for_location)(lat, lon, zarr_data) for lat, lon in locations]
    results = compute(*tasks)  # Compute all tasks in parallel
    return results

# Endpoint to process batch requests
@app.post("/extract/")
async def extract_data(request: LocationRequest):
    start_time = time.time()

    # Load the Zarr dataset based on model and model run
    zarr_data = load_zarr_dataset(request.model, request.model_run)

    # Batch size configuration
    batch_size = 50
    all_results = []

    # Process locations in batches
    for i in range(0, len(request.locations), batch_size):
        batch = request.locations[i:i + batch_size]
        batch_results = extract_data_parallel(batch, zarr_data)
        all_results.extend(batch_results)

    end_time = time.time()
    elapsed_time = end_time - start_time

    # Return results along with performance metrics
    return {
        "results": all_results,
        "performance_metrics": {
            "elapsed_time_seconds": elapsed_time,
            "num_batches": len(request.locations) // batch_size + (1 if len(request.locations) % batch_size > 0 else 0)
        }
    }
