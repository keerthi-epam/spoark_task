## Prerequisites:
Before proceeding, ensure you have the following tools installed:
  - Rancher Desktop – Required for running Kubernetes locally (alternative to Docker Desktop).
  - Python 3 – Needed for running Python-based applications and scripts.
  - Azure CLI (az) – Used to interact with Azure services and manage resources.
  - Terraform – Infrastructure as Code (IaC) tool for provisioning Azure resources.

## 1. Setup local project:
1. Setup python env by command:
```bash
python3 -m venv venv
```
2. activate python env
```bash
source venv/bin/activate
```
3. Setup needed requirements into your env:
```bash
pip install -r requirements.txt
```
4. Add your code in `src/main/`
5. Test your code with `src/tests/`
6. Package your artifacts:
```bash
python3 setup.py bdist_egg
```
7. Go into folder `docker/`, modify the `Dockerfile` if needed.
8. To build the Docker image, choose the correct command based on your CPU architecture: 
For most users (`Linux,` `Windows`, `Intel-based macOS`):
```bash
docker build -t spark-python-06 .
```
For `macOS` users with `M1`/`M2`/`M3` (ARM-based) chips:
Important: You must specify the target platform to ensure compatibility:
```bash
docker build --platform linux/amd64 -t spark-python-06 .
 ```

## 2. Create a Storage Account in Azure for Terraform State
Terraform requires a remote backend to store its state file. Follow these steps:

### **Option 1: Using Azure Portal (Web UI)**
1. **Log in to [Azure Portal](https://portal.azure.com/)**
2. Navigate to **Resource Groups** and click **Create**.
3. Enter a **Resource Group Name**, select a **Region**, and click **Review + Create**.
4. Once the Resource Group is created, go to **Storage Accounts** and click **Create**.
5. Fill in the required details:
   - **Storage Account Name**
   - **Resource Group** (Select the one you just created)
   - **Region** (Choose your preferred region)
   - **Performance**: Standard
   - **Redundancy**: Locally Redundant Storage (LRS)
6. Click **Review + Create** and then **Create**.
7. Once created, go to the **Storage Account** → **Containers** → Click **+ Container**.
8. Name it `tfstate`  (as example) and set **Access Level** to Private.

### **Option 2: Using Azure CLI**
1. **Log in to Azure:**
   ```bash
   az login
   ```
   This will open a browser for authentication.
2. **Select Your Azure Subscription (if multiple exist):**
   ```bash
   az account set --subscription "<YOUR_SUBSCRIPTION_ID>"
   ```
3. **Create a Resource Group:**
   ```bash
   az group create --name <RESOURCE_GROUP_NAME> --location <AZURE_REGION>
   ```
4. **Create a Storage Account:**
   ```bash
   az storage account create --name <STORAGE_ACCOUNT_NAME> --resource-group <RESOURCE_GROUP_NAME> --location <AZURE_REGION> --sku Standard_LRS
   ```
5. **Create a Storage Container:**
   ```bash
   az storage container create --name <CONTAINER_NAME> --account-name <STORAGE_ACCOUNT_NAME>
   ```

## 3. Get Your Azure Subscription ID

### **Option 1: Using Azure Portal (Web UI)**
1. **Go to [Azure Portal](https://portal.azure.com/)**
2. Click on **Subscriptions** in the left-hand menu.
3. You will see a list of your subscriptions.
4. Choose the subscription you want to use and copy the **Subscription ID**.

### **Option 2: Using Azure CLI**
Retrieve it using Azure CLI:
```bash
az account show --query id --output tsv
```

## 4. Update Terraform Configuration
Modify `main.tf` and replace placeholders with your actual values.

- **Edit the backend block in `main.tf`:**
  ```hcl
  terraform {
    backend "azurerm" {
      resource_group_name  = "<RESOURCE_GROUP_NAME>"
      storage_account_name = "<STORAGE_ACCOUNT_NAME>"
      container_name       = "<CONTAINER_NAME>"
      key                  = "terraform.tfstate"
    }
  }
  provider "azurerm" {
    features {}
    subscription_id = "<SUBSCRIPTION_ID>"
  }
  ```

## 5. Deploy Infrastructure with Terraform
Run the following Terraform commands:

```bash
terraform init
terraform plan -out terraform.plan
terraform apply terraform.plan
```

## 6. Verify Resource Deployment in Azure
After Terraform completes, verify that resources were created:

1. **Go to the [Azure Portal](https://portal.azure.com/)**
2. Navigate to **Resource Groups** → **Find `<RESOURCE_GROUP_NAME>`**
3. Check that the resources (Storage Account, Databricks, etc.) are created.

Alternatively, check via CLI:
```bash
az resource list --output table
az resource list --resource-group <RESOURCE_GROUP_NAME> --output table
```

## 7. Configure and Use Azure Container Registry (ACR)
Azure Container Registry (ACR) is used to store container images before deploying them to AKS.

1. Get the `<ACR_NAME>` run the following command:
```bash
terraform output acr_login_server
```
2. Authenticate with ACR.
Change the `<ACR_NAME>` with the output from the step `1`
```bash
az acr login --name <ACR_NAME>
```  
3. Push Docker Image to ACR:
```bash
docker tag spark-python-06 <ACR_NAME>/spark-python-06:latest
docker push <ACR_NAME>/spark-python-06:latest
```  
4. Verify Image in ACR:
```bash
az acr repository list --name <ACR_NAME> --output table
```  

## 8. Retrieve kubeconfig.yaml and Set It as Default
After Terraform applies the infrastructure, retrieve the Kubernetes configuration file:
1. Extract kubeconfig.yaml:
```bash
terraform output -raw aks_kubeconfig > kubeconfig.yaml
```  
2. Set kubeconfig.yaml as Default for kubectl in Current Terminal Session:
```bash
export KUBECONFIG=$(pwd)/kubeconfig.yaml
```
3. Verify Kubernetes Cluster Connectivity:
```bash
kubectl get nodes
```
You should able to see list of AKS nodes. Now you're able to communicate with AKS from commandline.

## 9. Launch Spark app in cluster mode on AKS
To retrive `https://<k8s-apiserver-host>:<k8s-apiserver-port>` run the foolowing command in the `terraform/` folder:
```bash
terraform output aks_api_server_url
```
Then procceed with `spark-submit` configuration:
```
spark-submit \
    --master k8s://https://<k8s-apiserver-host>:<k8s-apiserver-port> \
    --deploy-mode cluster \
    --name sparkbasics \
    --conf spark.kubernetes.container.image=<ACR_NAME>:spark-python-06 \
    ...
```

## 10. Destroy Infrastructure (Optional)
To remove all deployed resources, run:
```bash
terraform destroy
```
