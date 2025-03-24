import pytest
import requests
import geohash2
import os
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import FloatType, StructType, StructField, StringType

# Ensure Hadoop is properly configured
os.environ["HADOOP_HOME"] = "C:\\hadoop"
os.environ["HADOOP_OPTS"] = "-Djava.library.path=C:\\hadoop\\bin"

# Initialize SparkSession
@pytest.fixture(scope="session")
def spark():
    return (
        SparkSession.builder.master("local[*]")
        .appName("TestWeatherHotels")
        .config("spark.hadoop.io.nativeio.NativeIO", "false")  # Disable NativeIO on Windows
        .getOrCreate()
    )

# Sample geolocation function with improved error handling
def get_lat_lon_from_address(address):
    API_KEY = "dummy_api_key"
    BASE_URL = "https://api.opencagedata.com/geocode/v1/json"

    try:
        params = {"q": address, "key": API_KEY}
        response = requests.get(BASE_URL, params=params)
        data = response.json()
        if "results" in data and data["results"]:
            return data["results"][0]["geometry"]["lat"], data["results"][0]["geometry"]["lng"]
        return None, None
    except requests.exceptions.RequestException:
        return None, None

# UDF for Geohash Generation (handles None values safely)
def generate_geohash(lat, lon):
    if lat is None or lon is None:
        return None
    return geohash2.encode(lat, lon, precision=4)

# 1️⃣ **Test: Read Hotels Data**
def test_read_hotels(spark):
    hotels_schema = StructType(
        [
            StructField("HotelID", StringType(), True),
            StructField("Name", StringType(), True),
            StructField("Address", StringType(), True),
            StructField("Latitude", FloatType(), True),
            StructField("Longitude", FloatType(), True),
        ]
    )

    test_data = [
        ("H001", "Hotel A", "New York, USA", 40.7128, -74.0060),
        ("H002", "Hotel B", "London, UK", None, None),
    ]
    df_hotels = spark.createDataFrame(test_data, schema=hotels_schema)

    assert df_hotels.count() == 2
    assert df_hotels.filter(df_hotels.Latitude.isNull()).count() == 1  # 1 invalid entry

# 2️⃣ **Test: API Geocoding Function**
def test_get_lat_lon_from_address():
    lat, lon = get_lat_lon_from_address("1600 Amphitheatre Parkway, Mountain View, CA")
    assert isinstance(lat, (float, type(None))) and isinstance(lon, (float, type(None))), "Should return float values or None"

    lat, lon = get_lat_lon_from_address("Invalid Address 12345")
    assert lat is None and lon is None, "Should return None for invalid addresses"

# 3️⃣ **Test: Generate Geohash**
def test_generate_geohash():
    lat, lon = 40.7128, -74.0060
    geohash = generate_geohash(lat, lon)

    assert geohash is not None, "Geohash should not be None"
    assert len(geohash) == 4, "Geohash should have 4-character precision"

# 4️⃣ **Test: Extract Date Components**
def test_extract_date_components(spark):
    weather_schema = StructType([StructField("wthr_date", StringType(), True)])

    test_data = [("2023-07-15",), ("2024-01-02",)]
    df_weather = spark.createDataFrame(test_data, schema=weather_schema)

    df_weather = (
        df_weather.withColumn("wthr_year", F.year(F.to_date("wthr_date")).cast("string"))
        .withColumn("wthr_month", F.lpad(F.month(F.to_date("wthr_date")).cast("string"), 2, "0"))
        .withColumn("wthr_day", F.lpad(F.dayofmonth(F.to_date("wthr_date")).cast("string"), 2, "0"))
    )

    assert df_weather.collect()[0]["wthr_year"] == "2023"
    assert df_weather.collect()[1]["wthr_month"] == "01"
    assert df_weather.collect()[0]["wthr_day"] == "15"

# 5️⃣ **Test: Join Hotels & Weather Data**
def test_join_hotels_weather(spark):
    hotels_schema = StructType(
        [
            StructField("HotelID", StringType(), True),
            StructField("Name", StringType(), True),
            StructField("Geohash", StringType(), True),
        ]
    )

    weather_schema = StructType(
        [
            StructField("wthr_date", StringType(), True),
            StructField("Geohash", StringType(), True),
            StructField("temperature", FloatType(), True),
        ]
    )

    hotels_data = [("H001", "Hotel A", "abcd"), ("H002", "Hotel B", "efgh")]
    weather_data = [("2023-07-15", "abcd", 30.5), ("2023-07-16", "ijkl", 25.0)]

    df_hotels = spark.createDataFrame(hotels_data, schema=hotels_schema)
    df_weather = spark.createDataFrame(weather_data, schema=weather_schema)

    df_joined = df_weather.join(df_hotels, on="Geohash", how="left")

    assert df_joined.count() == 2
    assert df_joined.filter(df_joined.Name.isNotNull()).count() == 1  # Only 1 match

