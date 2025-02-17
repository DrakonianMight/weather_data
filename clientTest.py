import time
import requests
import random

# Function to generate random latitude and longitude
def generate_random_locations(num_locations):
    locations = []
    for _ in range(num_locations):
        lat = random.uniform(-90, 90)   # Latitude between -90 and 90
        lon = random.uniform(-180, 180) # Longitude between -180 and 180
        locations.append((lat, lon))
    return locations

# Generate 300 random locations
random_locations = generate_random_locations(2)

# Define the API URL
API_URL = "https://81gt1ca89k.execute-api.ap-southeast-2.amazonaws.com/extract/"

# Prepare the request payload
payload = {
    "locations": random_locations, # Use the list of 300 random locations
    "model":'ECMWF',
    "model_run": '20250213_00' 
}

# Measure the time taken to send the request and receive the response
start_time = time.time()

# Send the POST request to the API
response = requests.post(API_URL, json=payload)

# Measure the time taken for the request
end_time = time.time()
elapsed_time = end_time - start_time

# Output performance metrics
print(f"Request sent to {API_URL}")
print(f"Elapsed time for the request: {elapsed_time:.4f} seconds")

if response.status_code == 200:
    data = response.json()
    print("Response received successfully!")
    print(f"Number of locations processed: {len(data['results'])}")
    # Optionally print out a subset of the results
    for i, location_data in enumerate(data['results'][:5]):  # Print first 5 results
        print(f"Location {i+1}: ({location_data['lat']}, {location_data['lon']})")
        if 'message' in location_data:
            print(f"  Message: {location_data['message']}")
        else:
            print(f"  Data: {location_data['data']}")
else:
    print(f"Error {response.status_code}: {response.text}")
