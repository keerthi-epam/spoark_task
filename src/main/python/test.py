from pyspark.sql import SparkSession
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
AZURE_STORAGE_KEY = os.getenv("AZURE_STORAGE_KEY")

if not AZURE_STORAGE_KEY:
    raise ValueError("Azure Storage Key is missing. Check your .env file.")

# Initialize Spark Session
spark = SparkSession.builder \
    .appName("AzureStorageTest") \
    .config("spark.jars.packages", "org.apache.hadoop:hadoop-azure:3.3.1,com.microsoft.azure:azure-storage:8.6.6") \
    .getOrCreate()

# Configure Azure Storage access
storage_account_name = "stdevwesteurope3vzr"
container_name = "data"

spark.conf.set(f"fs.azure.account.auth.type.{storage_account_name}.dfs.core.windows.net", "SharedKey")
spark.conf.set(f"fs.azure.account.key.{storage_account_name}.dfs.core.windows.net", AZURE_STORAGE_KEY)

# Define test path
test_blob_path = f"abfss://{container_name}@{storage_account_name}.dfs.core.windows.net/m06sparkbasics/m06sparkbasics/hotels/*.csv.gz"

# Try reading a sample file from Azure Storage
try:
    df_test = spark.read.option("header", "true").csv(test_blob_path)
    print("Azure Storage Connection Successful! Sample Data:")
    df_test.show(5)
except Exception as e:
    print("Error connecting to Azure Storage:", e)
