## Spark ETL Job on Kubernetes with Azure

## Project Description
This project implements a Spark ETL pipeline that processes hotel and weather data stored in cloud storage (Azure). The job reads raw data, cleans incorrect latitude and longitude values using OpenCage Geocoding API, generates a geohash, and then joins the datasets based on the geohash. The enriched data is stored in a provisioned storage account in Parquet format. The Spark job is deployed on Kubernetes using Terraform scripts.

## Prerequisites

Before proceeding, ensure you have the following installed:
•	Rancher Desktop – Required for running Kubernetes locally (alternatively you can use Docker Desktop to run Kubernetes).
•	Python3 – Needed for running Python-based applications and scripts.
•	Azure CLI (az) – Used to interact with Azure services and manage resources.
•	Terraform – Infrastructure as Code (IaC) tool for provisioning resources.

## 1.Setting Up Environment (Azure Storage for Terraform State):
Terraform requires a remote backend to store its state file, ensuring consistency, collaboration, and recovery in case of failures. Using Azure Storage for Terraform state allows multiple users to work on the same infrastructure while maintaining a single source of truth for the state file. This setup prevents conflicts and ensures secure storage of infrastructure changes.

I.	 Log in to Azure Portal

II.	Navigate to Resource Groups and click Create

III.	Enter a Resource Group Name, select a Region (WestEurope), and click Review + Create.

IV.	Once the Resource Group is created, go to Storage Accounts and click Create.

V.	Fill in the required details: 
o	Storage Account Name(stdevwesteurope3vzr)
o	Resource Group (Select the one you just created) (MyResourceGroup)
o	Region (Choose your preferred region) (WestEurope)
o	Performance: Standard
o	Redundancy: Locally Redundant Storage (LRS)

VI.	Click Review + Create and then Create.

VII.	Once created, go to the Storage Account → Data Storage → Containers → Click + Container.

VIII.	Name it tfstate (as example) and set Access Level to Private.

IX.	To get <STORAGE_ACCOUNT_KEY>: Navigate to your Storage Account →Security & Networking → Access Keys. Press show button on key1

Screeshot:
![image](https://github.com/user-attachments/assets/fb053eed-9ac9-4903-939a-7e9178bd1b9e)

## 2.Get Your Subscription Id:
The Azure Subscription ID is a crucial identifier that allows Terraform to deploy and manage resources within a specific subscription. It is necessary for authentication, ensuring that all infrastructure provisioning occurs within the correct Azure account. By specifying the subscription ID in Terraform, you prevent accidental deployments in unintended environments, which is especially important in organizations managing multiple subscriptions. Additionally, it helps track resource usage, manage costs, and enforce access control policies effectively.
Navigate to Azure Portal → Subscriptions and copy your Subscription ID.
![image](https://github.com/user-attachments/assets/6f118670-2b8f-4584-82d4-8c72d15f5504)


 
## 3.Configure Terraform Backend:
Since the provided remote repository is shared among multiple users, modifying it directly is not feasible. To accommodate customization, the repository was cloned to a local environment, allowing changes to be made without affecting other users' configurations.

I.	Clone the remote repository:
```bash
git clone git@git.epam.com:epmcbdcc/trainings/bd201/m06_sparkbasics_python_azure.git
```
```bash
cd git@git.epam.com:epmcbdcc/trainings/bd201/m06_sparkbasics_python_azure.git
```
II.	Get the storage account key:
```bash
az storage account keys list --resource-group MyGroupResource --account-name sparkbasics123 --query "[0].value"
```
![image](https://github.com/user-attachments/assets/a6e72a64-bcb8-4f48-a74f-73e1c22c22e4)

 
III.	Edit the main.tf file:
terraform {
  backend "azurerm" {
    resource_group_name  = "MyResourceGroup"
    storage_account_name = " tdevwesteurope3vzr"
    container_name       = "data"
    key                  = "STORAGE_ACCOUNT_KEY"
  }
}
provider "azurerm" {
  features {}
  subscription_id = " 627b2fbd-dfd4-47c4-a964-3246ce1072d7
}
IV.	Add changes to the repository

V.	Commit the changes that had made in the file

## 4. Deploy Infrastructure with Terraform
Deploying infrastructure with Terraform is a crucial step in automating the provisioning of cloud resources. Terraform is an Infrastructure as Code (IaC) tool that allows users to define, manage, and deploy infrastructure using declarative configuration files. By using Terraform, organizations can ensure consistency, version control, and repeatability in their cloud deployments.

I.	Initialize Terraform:
This sets up the working directory, downloads necessary provider plugins, and configures the backend for storing the Terraform state.
```bash
terraform init
```
![image](https://github.com/user-attachments/assets/4ec92fdc-447d-4397-a335-768be7965fe7)

 
II.	Create an execution plan:
This command generates a preview of the changes Terraform will make to the infrastructure, helping users validate configurations before applying them.
```bash
terraform plan -out terraform.plan
```
![image](https://github.com/user-attachments/assets/e0e8ed97-5727-4591-a521-ceac0b8f3053)

 
III.	Apply the plan:
This step provisions the defined infrastructure by interacting with the cloud provider’s API.
```bash
terraform apply terraform.plan
```
IV.	Verify deployment:
Users can check the deployed resources and their attributes to confirm successful deployment.
```bash
Terraform output MyGroupResource
```

## 5.Verify Azure Resource Deployment
Verifying Azure resource deployment ensures that all infrastructure components have been successfully created as per the Terraform configuration. This step helps confirm that the necessary resources, such as storage accounts and resource groups, exist and are correctly configured.
Via Azure Portal: Navigate to Resource Groups and locate <RESOURCE_GROUP_NAME_CREATED_BY_TERRAFORM>.
<MyGroupResource>

## 6. Configure and Use Azure Container Registry (ACR)
Azure Container Registry (ACR) is used to store container images before deploying them to AKS.
Get the <ACR_NAME> run the following command:
```bash
terraform output acr_login_server
```
Authenticate with ACR.
Change the <ACR_NAME> with the output from the step 6.1
```bash
az acr login --name <ACR_NAME>
```

## 7. Unzipping the Dataset  
The given dataset was provided in a compressed ZIP format. To extract it, we used the following command:  
unzip m06sparkbasics.zip -d /path/to/destination
 
After extraction, the dataset was structured as follows:
 
m06sparkbasics/ <br/>
├── hotels.csv <br/>
├── weather/ <br/>
│   ├── year=2017/ <br/>
│   │   ├── month=01/ <br/>
│   │   │   ├── day=01/ <br/>
│   │   │   │   ├── part-00000.parquet <br/>
│   │   │   │   ├── .part-00000.parquet.crc <br/>
│   │   ├── month=02/ <br/>
│   │   │   ├── day=01/ <br/>
│   │   │   │   ├── part-00000.parquet <br/>
│   │   │   │   ├── .part-00000.parquet.crc <br/>
│   ├── year=2016/ <br/>
│   │   ├── month=12/ <br/>
│   │   │   ├── day=31/ <br/>
│   │   │   │   ├── part-00000.parquet <br/>
│   │   │   │   ├── .part-00000.parquet.crc

## 8.Upload Data Files to Azure Storage
Uploading data files to Azure Storage ensures that the necessary datasets are available for processing in the Spark ETL pipeline. The files stored in Azure Blob Storage serve as input for data transformation and enrichment operations.

I.	Retrieve the storage account name:
```bash
terraform output storage_account_name
```

II.	Upload files to the data container via Azure Portal.

III.	Verify Azure Resource Deployment
Azure Portal: Navigate to Resource Groups and locate <RESOURCE_GROUP_NAME_CREATED_BY_TERRAFORM>.

## 9.Set Up Local Development Environment
Setting up a local development environment is essential for developing, testing, and   debugging Spark ETL jobs before deploying them to Kubernetes. It provides a controlled space to install dependencies, configure the project structure, and validate code functionality. This setup ensures consistency across development and production environments, reducing errors and improving deployment efficiency.

I.	Create a Python Virtual Environment
•	The command python3 -m venv venv creates an isolated Python environment named venv.
•	Activating it with source venv/bin/activate ensures that all dependencies are installed in the virtual environment rather than system-wide.

II.	Activate python env
```bash
source venv/bin/activate
```

III.	Install Dependencies
•	pip install -r requirements.txt installs all required Python packages listed in requirements.txt.
•	This step ensures that all necessary libraries are available for running the ETL process.

IV.	Organize Source Code and Tests
•	Adding source code to src/main/ maintains a structured and modular project, making it easier to manage, test, and debug.

Folder Structure:
•	-src/
•	-main/  # Contains the main source code of the project
•	-tests/   #contains the unit tests for the project
•	-Readme.md   # Documentation for the project

Workflow Explanation:

Spark Session Initialization
•	The Spark session is configured with necessary Azure storage dependencies.
•	Authentication for Azure Blob Storage is established.

Reading Hotel Data
•	The hotel dataset is read from Azure Blob Storage (*.csv.gz format).
•	Rows with missing Latitude or Longitude are filtered.

Geolocation Data Enrichment
•	The OpenCage API is used to fetch latitude and longitude for missing values.
•	A UDF (get_lat_lon_udf) is applied to retrieve geolocation data.

Generating Geohash
•	A geohash (4-character) is generated from latitude and longitude to enable spatial joins.

Reading Weather Data
•	The weather dataset is read from Azure Blob Storage (*.parquet format).
•	The date (wthr_date) is split into year, month, and day columns for partitioning.
•	Geohash is generated for weather data using latitude and longitude.

Joining Weather and Hotels Data
•	The joined dataset is saved locally in Parquet format.
•	The final dataset is written to Azure Blob Storage with partitioning by year, month, and day.

Output Details
Local Output Path: output/joined_data_left.parquet
Azure Blob Storage Output Path: abfss://data@stdevwesteurope3vzr.dfs.core.windows.net/output1
The dataset is partitioned by wthr_year, wthr_month, wthr_day for efficient querying.

 ![image](https://github.com/user-attachments/assets/03538bdc-5d69-4ace-b46e-878d8f227c04)

 ![image](https://github.com/user-attachments/assets/7b70bebd-073e-48fa-973e-9d0cf6ed6a1a)

 ![image](https://github.com/user-attachments/assets/6d75539d-62dd-4801-82c8-11eda994b32d)



V.	Organise unit test cases code and Run UnitTests into folder src/tests/ 
Adding  unit test cases source code to src/tests/ maintains a structured and modular project, making it easier to manage, test, and debug.
Test cases :
![image](https://github.com/user-attachments/assets/b4106011-eb97-4e40-8af1-e1e1220b3859)

 
VI.	Package Artifacts
```bash
python3 setup.py bdist_egg
```
Creates a distributable .egg package of the project, which can be deployed or reused in other environments.
This step ensures that the ETL job can be packaged and executed efficiently within Kubernetes or other environments.
Output:
![image](https://github.com/user-attachments/assets/f6eab805-de19-4109-b09e-1432a053000d)

 
VII.	Building the Docker Image on Windows
Building Docker images ensures consistency, portability, and scalability of applications across environments. It encapsulates dependencies, making deployments reliable. Docker images enable efficient resource utilization, version control, and seamless scaling in Kubernetes or cloud platforms. This ensures smooth execution of your Spark ETL application across different systems.

```bash
docker build -t <ACR_NAME>/spark-python-06:latest -fdocker/Dockerfile docker/ --build-context extra-source=./(Replace the ACR_NAME with your actual value).
```
This command ensures the image is built using the AMD64 (x86_64) architecture, which is compatible with cloud-based Kubernetes clusters.
The --build-context extra-source=./ argument ensures all necessary files are included in the build process.
Update the docker file with your actual directory locations.
![image](https://github.com/user-attachments/assets/ab568840-b700-4aad-99a2-1568152abead)

 
VIII.	Push Docker Image to ACR:
Pushing a Docker image to Azure Container Registry (ACR) is essential for deploying containerized applications on Azure services like AKS, ACI, or App Service. It provides a secure, scalable, and centralized storage for managing and versioning images.

•	Build the Docker Image
Navigate to the directory where your Dockerfile is located and run the following command to build the image:
```bash
docker build -t acrdevwesteurope3vzr/park-python-06:latest -f docker/Dockerfile .
```
This command builds the image and tags it as park-python-06:latest
![image](https://github.com/user-attachments/assets/27cc2f23-25a2-4edd-95ba-c13b3d265c9f)

 
•	Verify the Built Image
Check if the image is built successfully by listing all Docker images:
```bash
docker images
```
Ensure the repository name and tag are correct.
![image](https://github.com/user-attachments/assets/b506d65f-fcdb-4dfa-9a6d-a67a6d09fa34)

 
•	Login to Azure Container Registry (ACR)
Before pushing the image, you need to authenticate with ACR:
```bash
docker login acrdevwesteurope3vzr.azurecr.io
```
When prompted, enter the username and password for ACR authentication
![image](https://github.com/user-attachments/assets/01df8659-3040-4f76-b088-eb5ef1456526)

 
•	Tag the Image for ACR
Docker needs the image tag to match the ACR repository format. Tag the built image correctly:
```bash
docker tag acrdevwesteurope3vzr/park-python-06:latest acrdevwesteurope3vzr.azurecr.io/park-python-06:latest
```
This renames the image with the ACR domain prefix.

•	Push the Image to ACR
Now, push the tagged image to Azure Container Registry:
```bash
docker push acrdevwesteurope3vzr.azurecr.io/park-python-06:latest
```
This uploads the image to ACR, making it accessible for deployments.
![image](https://github.com/user-attachments/assets/456dc169-75d7-4f6f-8791-2ef9011db639)

 
IX.	Verify the Image in ACR
Check if the image is successfully pushed by listing repositories in ACR:
```bash
az acr repository list --name acrdevwesteurope3vzr --output table
```
You should see park-python-06 in the list. 
![image](https://github.com/user-attachments/assets/37004592-96f5-40b6-93a4-40ccb4cd12c0)


## 10: Retrieve kubeconfig.yaml and Set It as Default
Once your Azure Kubernetes Service (AKS) cluster is created, you need to configure kubectl to communicate with the cluster. Follow the steps below to retrieve and set up the kubeconfig.yaml file.

I.	Initialize Terraform
Before deploying AKS, Terraform needs to be initialized. This downloads the required providers and modules.
```bash
terraform init
```
```bash
terraform init -migrate-state
```
![image](https://github.com/user-attachments/assets/f5de679b-26d7-4538-b2c5-cdf71f6d67e5)

 
II.	2: Apply Terraform Configuration
Now, apply the Terraform configuration to provision resources in Azure.
```bash
terraform apply -auto-approve
```
Terraform will create the AKS cluster and required resources.
![image](https://github.com/user-attachments/assets/4e03ca79-8b56-4087-a9e3-49bf61c94392)

 
III.	Retrieve kubeconfig.yaml
After the cluster is successfully provisioned, extract the kubeconfig.yaml file to authenticate with AKS.
Terraform stores the AKS cluster credentials in its output. Run the following command to extract the kubeconfig.yaml file:
```bash
terraform output -raw aks_kubeconfig > kubeconfig.yaml
```
This command retrieves the AKS cluster's kubeconfig and saves it in the current directory as kubeconfig.yaml.

IV.	Set kubeconfig.yaml as Default for kubectl
To use kubectl with your newly created AKS cluster, set the kubeconfig file as the default for the current session.
```bash
$env:KUBECONFIG = "$(Get-Location)\kubeconfig.yaml"
```
This tells kubectl to use this specific kubeconfig file instead of the default one

V.	Verify Kubernetes Cluster Connectivity
Now, check if the Kubernetes nodes are up and running.
```bash
kubectl get nodes
```
![image](https://github.com/user-attachments/assets/c8754fea-c022-41a5-b758-f51763a9c222)

 
VI.	List Running Pods (Optional)
To ensure that all Kubernetes system pods are running properly, execute:
```bash
kubectl get pods -A
```
This command lists all pods across namespaces, including system pods required for AKS.   
![image](https://github.com/user-attachments/assets/a1ce6cdf-715a-4503-86f2-31dad6aca222)





## 11. Launch Spark app in cluster mode on AKS

I.	 Retrieve AKS API Server URL
To connect Spark to AKS, you need the Kubernetes API Server URL. Run the following command inside your Terraform project directory (terraform/):
```bash
terraform output aks_api_server_url
```
![image](https://github.com/user-attachments/assets/ca1e91cd-f26d-4e38-9b98-8f0096ed487d)
 
This Command Fetches the Kubernetes API Server URL, which is required to submit Spark jobs to AKS.

II.	Configure and Submit Spark Job
Now, update the placeholders in the spark-submit command and run it.
![image](https://github.com/user-attachments/assets/dfbe0b50-fe11-4f85-b8c1-340a5c1fee36)

III.Verify the spark job
```bash
kubectl logs spark-driver-4522
```
![image](https://github.com/user-attachments/assets/03538bdc-5d69-4ace-b46e-878d8f227c04)


            



