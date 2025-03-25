import os
import requests
import geohash2
from dotenv import load_dotenv
from pyspark.sql import functions as F
from pyspark.sql.functions import udf
from pyspark.sql.types import FloatType, StructType, StructField, StringType
from pyspark.sql import SparkSession

# Load environment variables from .env file
load_dotenv()

# Retrieve Azure Storage Account Name and Key from environment variables
AZURE_STORAGE_ACCOUNT_NAME = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
AZURE_STORAGE_KEY = os.getenv("AZURE_STORAGE_KEY")

if not AZURE_STORAGE_ACCOUNT_NAME or not AZURE_STORAGE_KEY:
    raise ValueError("Azure Storage Account Name or Key is not set. Ensure they are in the .env file.")

# Initialize Spark Session
spark = SparkSession.builder \
    .appName("WeatherHotelsJoin") \
    .config("spark.jars.packages", "org.apache.hadoop:hadoop-azure:3.3.1,com.microsoft.azure:azure-storage:8.6.6") \
    .getOrCreate()

# Azure Storage details
container_name = "data"

# Set Azure storage key dynamically
spark.conf.set(f"fs.azure.account.auth.type.{AZURE_STORAGE_ACCOUNT_NAME}.dfs.core.windows.net", "SharedKey")
spark.conf.set(f"fs.azure.account.key.{AZURE_STORAGE_ACCOUNT_NAME}.dfs.core.windows.net", AZURE_STORAGE_KEY)

# OpenCage API details
API_KEY = os.getenv("OPENCAGE_API_KEY")
BASE_URL = "https://api.opencagedata.com/geocode/v1/json"

def get_lat_lon_from_address(address):
    try:
        params = {
            'q': address,
            'key': API_KEY
        }
        response = requests.get(BASE_URL, params=params)
        data = response.json()

        if data['results']:
            latitude = data['results'][0]['geometry']['lat']
            longitude = data['results'][0]['geometry']['lng']
            return latitude, longitude
        else:
            return None, None
    except Exception as e:
        print(f"Error fetching data for address {address}: {e}")
        return None, None

def get_lat_lon_udf(address):
    lat, lon = get_lat_lon_from_address(address)
    return (lat, lon)

# Define a StructType for the UDF return type
lat_lon_schema = StructType([
    StructField("Latitude", FloatType(), True),
    StructField("Longitude", FloatType(), True)
])

# Register the UDF with StructType as the return type
get_lat_lon = udf(get_lat_lon_udf, lat_lon_schema)

def generate_geohash(lat, lon):
    if lat is not None and lon is not None:
        return geohash2.encode(lat, lon, precision=4)  # 4-character geohash
    else:
        return None

geohash_udf = udf(generate_geohash, StringType())

# Define Azure Storage folder paths
hotels_folder_path = "m06sparkbasics/m06sparkbasics/hotels"
weather_folder_path = "m06sparkbasics/m06sparkbasics/weather"

# Construct the Blob URL for hotels data
blob_url_hotels = f"wasbs://{container_name}@{AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net/{hotels_folder_path}/*.csv.gz"

# Read the Hotels dataset
df_hotels = spark.read \
    .option("header", "true") \
    .option("inferSchema", "true") \
    .csv(blob_url_hotels)

# Filter rows where 'Latitude' or 'Longitude' are NULL
df_invalid_hotels = df_hotels.filter((df_hotels.Latitude.isNull()) | (df_hotels.Longitude.isNull()))

# Apply the UDF to update the latitude and longitude using the Address field
df_hotels_updated = df_invalid_hotels.withColumn("Latitude", get_lat_lon(F.col("Address"))["Latitude"]) \
    .withColumn("Longitude", get_lat_lon(F.col("Address"))["Longitude"])

# Generate geohash based on latitude and longitude
df_hotels_updated = df_hotels_updated.withColumn("Geohash", geohash_udf(F.col("Latitude"), F.col("Longitude")))

# Construct the Blob URL for weather data
blob_url_weather = f"wasbs://{container_name}@{AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net/{weather_folder_path}/year=*/month=*/day=*/*.parquet"

# Read the Weather dataset
df_weather = spark.read.parquet(blob_url_weather)

# Extract year, month, and day from the 'wthr_date' column
df_weather = df_weather.withColumn(
    "wthr_year", F.year(F.col("wthr_date")).cast("string")
).withColumn(
    "wthr_month", F.lpad(F.month(F.col("wthr_date")).cast("string"), 2, "0")
).withColumn(
    "wthr_day", F.lpad(F.dayofmonth(F.col("wthr_date")).cast("string"), 2, "0")
)

# Generate geohash for the weather data using the lat and lng columns
df_weather = df_weather.withColumn("Geohash", geohash_udf(F.col("lat"), F.col("lng")))

# Perform left join on geohash between Weather and Hotels data
df_joined = df_weather.join(df_hotels_updated, on="Geohash", how="left")

# Show 20 rows to verify the join
df_joined.show(20, truncate=False)

# Define Azure Blob Storage output path
output_path = f"abfss://{container_name}@{AZURE_STORAGE_ACCOUNT_NAME}.dfs.core.windows.net/output1"

# Write the joined DataFrame in Parquet format
df_joined.write \
    .mode("overwrite") \
    .partitionBy("wthr_year", "wthr_month", "wthr_day") \
    .parquet(output_path)

print(f"Joined DataFrame written to Azure Storage: {output_path}")
