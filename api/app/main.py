import time
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

# AWS S3 Configuration
S3_BUCKET = "s3://exampleapidata"
S3_PREFIX = "weather_data/"  # Adjust as needed

# Function to load a Zarr dataset from S3
def load_zarr_dataset(model: str, model_run: str):
    s3_path = f"s3://{S3_BUCKET}/{model}/{model_run}.zarr"

    try:
        # Load the Zarr dataset from S3 using xarray
        return xr.open_zarr(s3_path)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Error loading dataset from S3: {str(e)}")


# Function to extract data for a single location
def extract_data_for_location(lat: float, lon: float, zarr_data: xr.Dataset):
    try:
        # Determine correct latitude and longitude coordinate names
        lat_dim = "lat" if "lat" in zarr_data.coords else "latitude"
        lon_dim = "lon" if "lon" in zarr_data.coords else "longitude"
        time_dim = "valid_time" if "valid_time" in zarr_data.coords else "time"

        # Check if the lat, lon is within the dataset bounds
        if lat < zarr_data.coords[lat_dim].min() or lat > zarr_data.coords[lat_dim].max():
            return {"lat": lat, "lon": lon, "message": "Latitude out of bounds"}
        if lon < zarr_data.coords[lon_dim].min() or lon > zarr_data.coords[lon_dim].max():
            return {"lat": lat, "lon": lon, "message": "Longitude out of bounds"}

        # Extract the nearest data point
        data_point = zarr_data.sel({lat_dim: lat, lon_dim: lon}, method="nearest")

        # Ensure we get the correct valid time
        valid_time = list(zarr_data.valid_time.to_pandas().unique().strftime("%Y-%m-%d %H:%M:%S"))

        # Convert data to a serializable format
        data_dict = {
            var: float(data_point[var].values) if np.isscalar(data_point[var]) else data_point[var].values.tolist()
            for var in data_point.data_vars
        }
        data_dict.update({"valid_time": valid_time})  # Add valid_time to the data dict
        return {
            "lat": lat,
            "lon": lon,
            "data": data_dict
        }

    except Exception as e:
        return {"lat": lat, "lon": lon, "message": f"Error: {str(e)}"}

# Function to process a batch of locations in parallel
def extract_data_parallel(locations: List[Tuple[float, float]], zarr_data: xr.DataArray):
    tasks = [delayed(extract_data_for_location)(lat, lon, zarr_data) for lat, lon in locations]
    return compute(*tasks)  # Compute all tasks in parallel

# Endpoint to process batch requests
@app.post("/extract/")
async def extract_data(request: LocationRequest):
    start_time = time.time()

    # Load the Zarr dataset from S3
    zarr_data = load_zarr_dataset(request.model, request.model_run)
    zarr_data = zarr_data.sortby('valid_time')

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
    

@app.get("/")
async def root():
    print("in root method")
    return {"message": "Hello, weather api"}



#handler = Mangum(app, lifespan="off")

#if __name__ == "__main__":
#    uvicorn.run(app, host="0.0.0.0", port=5000)