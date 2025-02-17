# **FastAPI Weather Extraction API**

## **Overview**
This FastAPI application extracts **weather data** for given latitude and longitude coordinates from **Xarray datasets** stored in **Zarr format**. The API is deployed on **AWS Lambda** and secured using **IAM authentication**.

## **API Endpoint**
- **Base URL:** `https://**********.execute-api.ap-southeast-2.amazonaws.com/`
- **Extract Weather Data:** `POST /extract/`

## **Authentication**
The API uses **IAM-based authentication**, so requests must be signed with **AWS Signature Version 4 (SigV4)**.

## **Running Locally for Testing**
### **1. Clone the Repository**
```sh
git clone https://github.com/your-repo/weather-api.git
cd weather-api
```

### **2. Install Dependencies**
```sh
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt
```
### **3. Run FastAPI Locally**
```sh
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
The API will now be available at:
127.0.0.1:8000/docs


