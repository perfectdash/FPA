# FP&A Real-Time Financial Operations Platform

This repository houses the code, stream processing pipelines, and configurations for **Project 1: Web-Scale Financial Data Pipeline & Planning Engine**. The application ingests corporate transactions, processes them via a streaming analytics engine, validates spend thresholds against dynamic budgets, and exposes metrics on a glassmorphism React console dashboard.

---

## 1. System Architecture

```
                                      ┌──────────────┐
                                      │ GitHub CI/CD │
                                      └──────┬───────┘
                                             │ (Auth via WIF Pool)
                                             ▼
                                     [ad-github-deployer]
                                             │
                                    ┌────────┴────────┐
                                    ▼                 ▼
 ┌──────────────┐     ┌───────────┐           ┌───────────────┐
 │ ERP / Client │ ──> │ Ingestion │ ────────> │  Pub/Sub raw  │
 │ Webhook POST │     │ Cloud Run │           │  transactions │
 └──────────────┘     └───────────┘           └───────┬───────┘
                                                      │
                                                      ▼
 ┌──────────────┐                             ┌───────────────┐
 │  Cloud SQL   │ ──────────────────────────> │ Cloud Dataflow│
 │  PostgreSQL  │ (Budget rules side-input)  │ (Apache Beam) │
 └──────────────┘                             └───────┬───────┘
                                                      │
                            ┌─────────────────────────┴────────────────────────┐
                            ▼                                                  ▼
                 ┌──────────────────────┐                           ┌────────────────────┐
                 │  BigQuery Analytics  │                           │   Pub/Sub Alerts   │
                 │   `transactions_raw` │                           │  `budget-breaches` │
                 └──────────┬───────────┘                           └──────────┬─────────┘
                            │                                                  │
                            ▼                                                  ▼
                 ┌──────────────────────┐                           ┌────────────────────┐
                 │    Reporting API     │ <──────────────────────── │   Alert Consumer   │
                 │      Cloud Run       │                           │    (microservice)  │
                 └──────────┬───────────┘                           └────────────────────┘
                            │   ▲
                            ▼   │
                         ┌─────────┐
                         │  Redis  │ (Variance report cache)
                         └─────────┘
                            │   ▲
                            ▼   │
                 ┌──────────────────────┐
                 │ React Dashboard UI   │
                 │    (Vite Console)    │
                 └──────────────────────┘
```

---

## 2. Component Structure

The codebase is organized into modular services:

*   **`ingestion/`**: FastAPI service that validates incoming events using Pydantic and publishes them to Google Cloud Pub/Sub. Bypasses core-thread blocking using thread-pool executors for Pub/Sub publish calls.
*   **`pipeline/`**: Apache Beam pipeline running on Google Cloud Dataflow. Ingests stream elements, writes raw transaction auditing details to a date-partitioned BigQuery table, applies sliding event-time tumbling windows (1 hour), and runs compliance check thresholds.
*   **`reporting/`**: FastAPI analytical endpoint querying BigQuery. Employs a Redis cache-aside design pattern (5-minute TTL) to shield BigQuery from costly query scans.
*   **`frontend/`**: React Single Page Application utilizing Recharts for variance visualizations, displaying burn rate trackers, and providing a built-in event loading simulator.
*   **`terraform/`**: Infrastructure as Code configs to provision GCP service accounts, Pub/Sub channels, partitioned BigQuery datasets, and PostgreSQL databases.

---

## 3. Local Development (Offline Mock Mode)

All microservices are equipped with automatic local fallbacks, allowing you to run and verify the entire system offline on your laptop without GCP credentials or databases.

### Step 1: Set Up Python Virtual Environment
Navigate to the root and create a virtual environment:
```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

### Step 2: Install Service Dependencies
Install dependencies for each Python component:
```powershell
pip install -r ingestion/requirements.txt
pip install -r pipeline/requirements.txt
pip install -r reporting/requirements.txt
```

### Step 3: Run the Ingestion API
Start the Ingestion service locally on port 8000:
```powershell
cd ingestion
uvicorn main:app --host 0.0.0.0 --port 8000
```
*Note: Since no `GCP_PROJECT_ID` is set, the console will boot in `[MOCK MODE]` and output all received events to the console log.*

### Step 4: Run the Reporting API
In a new terminal window (with virtual environment activated), start the Reporting service on port 8001:
```powershell
cd reporting
uvicorn main:app --host 0.0.0.0 --port 8001
```
*Note: If no Redis or BigQuery credentials are found, the server automatically boots in local mock mode, generating realistic financial metrics with random fluctuations for display.*

### Step 5: Start the React Dashboard
In a new terminal window, navigate to the frontend folder, install npm modules, and boot Vite on port 3000:
```powershell
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000` in your web browser. 

*   Vite will automatically boot and route requests starting with `/api` to the reporting service running on port 8001.
*   Toggle the **Auto-Generate Events** button on the console to start streaming synthetic load into the ingestion server, which will automatically update the charts, burn metrics, and telemetry scroll in real-time!

### Step 6: Test the Apache Beam Pipeline (Optional)
To verify the stream parsing, combinations, and threshold breach evaluation in Apache Beam locally, run the main pipeline file with the `--local` flag:
```powershell
cd pipeline
python main.py --local
```
This runs the pipeline on the local `DirectRunner` engine using a generated sequence of transactions, prints raw BigQuery outputs, computes windowed sums, evaluates budget compliance, and outputs budget breaches directly to stdout.

---

## 4. GCP Provisioning (Terraform)

To configure the resources on Google Cloud Platform, see the guide in `c:\Users\hp\Google\terraform_induction.md` and apply:
```powershell
cd terraform
terraform init
terraform plan
terraform apply
```
This provisions Pub/Sub topics, BigQuery datasets, Cloud SQL Postgres databases, and the required Service Accounts with least-privilege IAM scopes.

---

## 5. Google Cloud Deployment

### Deployment 1: Submit Dataflow Job
Deploy the Apache Beam pipeline to Cloud Dataflow:
```powershell
python pipeline/main.py \
    --runner=DataflowRunner \
    --project=YOUR_PROJECT_ID \
    --region=us-central1 \
    --temp_location=gs://YOUR_STAGING_BUCKET/temp \
    --staging_location=gs://YOUR_STAGING_BUCKET/staging \
    --service_account_email=dataflow-worker@YOUR_PROJECT_ID.iam.gserviceaccount.com \
    --streaming
```

### Deployment 2: Deploy Ingest API & Reporting API to Cloud Run
1. Containerize the applications and push to Artifact Registry.
2. Deploy the Ingestion container:
```powershell
gcloud run deploy fastapi-ingester \
    --image=us-central1-docker.pkg.dev/YOUR_PROJECT_ID/fpa-repo/fastapi-ingester:latest \
    --region=us-central1 \
    --service-account=fastapi-ingester@YOUR_PROJECT_ID.iam.gserviceaccount.com \
    --set-env-vars=GCP_PROJECT_ID=YOUR_PROJECT_ID,PUBSUB_TOPIC_ID=transactions
```

3. Deploy the Reporting container:
```powershell
gcloud run deploy fastapi-reporting \
    --image=us-central1-docker.pkg.dev/YOUR_PROJECT_ID/fpa-repo/fastapi-reporting:latest \
    --region=us-central1 \
    --service-account=fastapi-reporting@YOUR_PROJECT_ID.iam.gserviceaccount.com \
    --set-env-vars=GCP_PROJECT_ID=YOUR_PROJECT_ID,REDIS_HOST=YOUR_REDIS_IP
```
