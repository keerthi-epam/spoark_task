# SparkBasics [python]

## Prerequisites

Before proceeding, ensure you have the following tools installed:

- Rancher Desktop – Required for running Kubernetes locally (alternative to Docker Desktop). Please keep it running.
- Python 3 – Needed for running Python-based applications and scripts.
- Azure CLI (az) – Used to interact with Azure services and manage resources.
- Terraform – Infrastructure as Code (IaC) tool for provisioning Azure resources.

## 1. Create a Storage Account in Azure for Terraform State

Terraform requires a remote backend to store its state file. Follow these steps:

### **Option 1: Using Azure CLI [Recommended]**

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

This is only used for storing Terraform state files. Terraform will create the necessary resource groups later.
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

### **Option 2: Using Azure Portal (Web UI)**
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
7. Once created, go to the **Storage Account** → **Data Storage** → **Containers** → Click **+ Container**.
8. Name it `tfstate`  (as example) and set **Access Level** to Private.
9. To get `<STORAGE_ACCOUNT_KEY>`: Navigate to your **Storage Account** →**Security & Networking** → **Access Keys**. Press `show` button on `key1`

## 2. Get Your Azure Subscription ID

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

## 3. Update Terraform Configuration

Modify `main.tf` and replace placeholders with your actual values.

- Get a Storage Account Key (`<STORAGE_ACCOUNT_KEY>`):

```bash
az storage account keys list --resource-group <RESOURCE_GROUP_NAME> --account-name <STORAGE_ACCOUNT_NAME> --query "[0].value"
```

- **Edit the backend block in `main.tf`:**

```hcl
  terraform {
    backend "azurerm" {
      resource_group_name  = "<RESOURCE_GROUP_NAME>"
      storage_account_name = "<STORAGE_ACCOUNT_NAME>"
      container_name       = "<CONTAINER_NAME>"
      key                  = "<STORAGE_ACCOUNT_KEY>"
    }
  }
  provider "azurerm" {
    features {}
    subscription_id = "<SUBSCRIPTION_ID>"
  }
```

## 4. Deploy Infrastructure with Terraform

Run the following Terraform commands:

```bash
terraform init
```  

```bash
terraform plan -out terraform.plan
```  

```bash
terraform apply terraform.plan
```  

To see the `<RESOURCE_GROUP_NAME_CREATED_BY_TERRAFORM>` (resource group that was created by terraform), run the command:

```bash
terraform output resource_group_name
```

## 5. Verify Resource Deployment in Azure

After Terraform completes, verify that resources were created:

1. **Go to the [Azure Portal](https://portal.azure.com/)**
2. Navigate to **Resource Groups** → **Find `<RESOURCE_GROUP_NAME_CREATED_BY_TERRAFORM>`**
3. Check that the resources (Storage Account, Databricks, etc.) are created.

Alternatively, check via CLI:

```bash
az resource list --resource-group <RESOURCE_GROUP_NAME_CREATED_BY_TERRAFORM> --output table
```

## 6. Configure and Use Azure Container Registry (ACR)

Azure Container Registry (ACR) is used to store container images before deploying them to AKS.

1. Get the `<ACR_NAME>` run the following command:

```bash
terraform output acr_login_server
```

2. Authenticate with ACR.

Change the `<ACR_NAME>` with the output from the step `6.1`

```bash
az acr login --name <ACR_NAME>
```  

## 7. Upload the data files into Azure Conatainers

1. Log in to [Azure Portal](https://portal.azure.com/)
2. Go to your STORAGE account => Data Storage => Containers

- to get actual STORAGE account name, you can run a command from the `terraform` folder:

```bash
terraform output storage_account_name
```

3. Choose the conatiner `data`
4. You should see the upload button
5. Upload the files here.

## 8. Setup local project

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
5. Add and Run UnitTests into folder `src/tests/`
6. Package your artifacts:

```bash
python3 setup.py bdist_egg
```

7. ⚠️  To build the Docker image, choose the correct command based on your CPU architecture:

    <details>
    <summary><code>Linux</code>, <code>Windows</code>, <code>&lt;Intel-based macOS&gt;</code> (<i>click to expand</i>)</summary>

    ```bash
    docker build -t <ACR_NAME>/park-python-06:latest -f docker/Dockerfile docker/ --build-context extra-source=./
    ```

    </details>
    <details>
    <summary><code>macOS</code> with <code>M1/M2/M3</code> <code>&lt;ARM-based&gt;</code>  (<i>click to expand</i>)</summary>

    ```bash
    docker build --platform linux/amd64 -t <ACR_NAME>/spark-python-06:latest -f docker/Dockerfile docker/ --build-context extra-source=./
    ```

    </details>

8. Local testing (Optional)
- Setup local project before push image to ACR, to make sure if everything goes well:

```bash
docker run --rm -it <ACR_NAME>/spark-python-06:latest spark-submit --master "local[*]" --py-files PATH_TO_YUR_EGG_FILE.egg /PATH/TO/YOUR/Python.py
```

Warning! (Do not forget to clean output folder, created by spark job after local testing)!

9. Push Docker Image to ACR:

```bash
docker push <ACR_NAME>/spark-python-06:latest
```  

9. Verify Image in ACR:

```bash
az acr repository list --name <ACR_NAME> --output table
```  

## 8. Retrieve kubeconfig.yaml and Set It as Default

1. Extract `kubeconfig.yaml` from the directory `/terraform`:

```bash
terraform output -raw aks_kubeconfig > kubeconfig.yaml
```  

2. Set `kubeconfig.yaml` as Default for kubectl in Current Terminal Session:

```bash
export KUBECONFIG=$(pwd)/kubeconfig.yaml
```

3. Verify Kubernetes Cluster Connectivity:

```bash
kubectl get nodes
```

You should able to see list of AKS nodes. Now you're able to communicate with AKS from commandline.

## 9. Launch Spark app in cluster mode on AKS

- To retrive `https://<k8s-apiserver-host>:<k8s-apiserver-port>` run the foolowing command in the `terraform/` folder:

```bash
terraform output aks_api_server_url
```

- Then procceed with `spark-submit` configuration (before execute this command, update the placeholders):

```bash
spark-submit \
    --master k8s://https://<k8s-apiserver-host>:<k8s-apiserver-port> \
    --deploy-mode cluster \
    --name sparkbasics \
    --conf spark.kubernetes.container.image=<ACR_NAME>:spark-python-06:latest \
    --conf spark.kubernetes.driver.request.cores=500m \
    --conf spark.kubernetes.driver.request.memory=500m \
    --conf spark.kubernetes.executor.request.memory=500m \
    --conf spark.kubernetes.executor.request.cores=500m \
    --conf spark.kubernetes.namespace=default \
    --conf spark.kubernetes.authenticate.driver.serviceAccountName=spark \
    --conf spark.kubernetes.driver.pod.name=spark-driver \
    --conf spark.kubernetes.executor.instances=1 \
    --conf spark.pyspark.python=python3 \
    --conf spark.pyspark.driver.python=python3 \
    --py-files local:///opt/<YOUR_PYTHON_EGG_FILE_NAME> \
    local:///opt/src/main/python/<YOUR_PYTHON_PROJECT_FILE_PY>
```

- once jobs finished, you can verify the output from the spark job:

```bash
kubectl logs spark-driver
```

## 10. Destroy Infrastructure (Optional)

To remove all deployed resources, run:

```bash
terraform destroy
```
