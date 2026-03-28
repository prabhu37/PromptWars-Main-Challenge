# Deploying CLARITY AI to Google Cloud Run

To safely and reliably host your Streamlit application on the public internet, Google Cloud Run is an excellent serverless choice. 

I have automatically added a `Dockerfile` and `.dockerignore` to your local project to get it ready. **Commit those files and push them to your repository first.**

```bash
git add Dockerfile .dockerignore
git commit -m "Add Docker files for Cloud Run deployment"
git push
```

## Method 1: Continuous Deployment from GitHub (Recommended & Easiest)

Google Cloud Run can automatically pull from your GitHub repository and build your container on every push.

1. Go to the [Google Cloud Console](https://console.cloud.google.com/run).
2. Click **Create Service**.
3. Select **Continuously deploy new revisions from a source repository**.
4. Click **Set up with Cloud Build**.
   - **Provider**: GitHub
   - **Repository**: Select `prabhu37/PromptWars-WarmUp`
   - **Branch**: `^main$`
   - **Build Type**: `Dockerfile` (it should automatically detect the `/Dockerfile` we just made)
5. Under **Authentication**, choose **Allow unauthenticated invocations** (so anyone on the internet can see your app).
6. Under **Container(s), Volumes, Networking, Security**:
   - Make sure **Container port** is set to `8080` (matches the Dockerfile).
   - Under the **Variables & Secrets** tab, click **ADD VARIABLE**, and add:
     - Name: `GEMINI_API_KEY`
     - Value: `<YOUR_ACTUAL_GEMINI_API_KEY>`
7. Click **Create**.

Google Cloud will automatically build your Docker container and give you a live HTTPS URL in about 2-3 minutes!

## Method 2: Deploying manually via Google Cloud CLI (`gcloud`)

If you prefer deploying it directly from your local terminal instead of linking GitHub, you can use the `gcloud` CLI.

> [!NOTE]
> You must have the [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed and be authenticated (`gcloud auth login`).

Run this command inside your terminal:

```bash
gcloud run deploy clarity-ai \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --set-env-vars="GEMINI_API_KEY=<YOUR_ACTUAL_API_KEY>"
```

Google Cloud will automatically build the container behind the scenes using Cloud Build, deploy it, and output the live URL.
