# Deployment & CI/CD Guide

This document outlines the CI/CD and deployment strategy for the Multimodal Validation System, including the frontend and the three distinct backend microservices: **Kumesha**, **Minuk**, and **Voshan**.

## 1. Frontend Deployment

### Recommended: Vercel or Netlify

The frontend is a `React + Vite` application, making it perfectly suited for free managed hosting like Vercel or Netlify.

**Steps for Vercel:**
1. Log into [Vercel](https://vercel.com) and create a New Project.
2. Connect your GitHub repository.
3. Select the `frontend` directory as the **Root Directory**.
4. The framework preset should auto-detect **Vite**.
5. Click **Deploy**. Vercel will automatically trigger a deployment whenever you push to `main`.

**GitHub Actions (CI)**
A GitHub Action is located at `.github/workflows/frontend-ci.yml`. It will automatically test the frontend on pushes/PRs affecting the `frontend/` folder.

---

## 2. Backend Microservices Deployment

The backend is composed of three distinct microservices (`Kumesha`, `minuk`, and `Voshan`). Because they use different machine learning models, deploying them via separate Docker containers allows for independent scaling and ensures dependency isolation.

### Option A: Render.com (Web Services)
This is easiest if you want fully-managed, containerized platforms.

1. **Kumesha API:** Create a new Web Service, choose "Docker", and specify `Dockerfile.kumesha` as the Dockerfile path.
2. **Minuk API:** Create another Web Service, choose "Docker", and specify `Dockerfile.minuk`.
3. **Voshan API:** Create a third Web Service, choose "Docker", and specify `Dockerfile.voshan`.

Ensure each service has at least 2GB-4GB of RAM (or more depending on model loads).

### Option B: DigitalOcean Droplet / AWS EC2 (VPS) with Docker Compose
If you want to host them all on a single unified server to save money, a VPS with Docker Compose is the best route.

1. Provision a DigitalOcean Droplet (Ubuntu, 8GB+ RAM recommended if running all three heavily).
2. SSH into the server and install Docker and Docker Compose.
3. Clone your repository:
   ```bash
   git clone https://github.com/your-username/multimodal-validation.git
   cd multimodal-validation
   ```
4. Build and start all services via `docker-compose`:
   ```bash
   docker-compose up -d --build
   ```
   This will start:
   - Kumesha on Port `8000`
   - Minuk on Port `8001`
   - Voshan on Port `8002`

You can use an NGINX reverse proxy locally or on the VPS to route Traffic from `api.domain.com/kumesha` to `8000`, etc.

### GitHub Actions (CI)
There are three specific workflows created for each microservice:
- `.github/workflows/backend-kumesha-ci.yml`
- `.github/workflows/backend-minuk-ci.yml`
- `.github/workflows/backend-voshan-ci.yml`

Changes made to `Kumesha/**` will only trigger the Kumesha CI workflow. The CI workflow installs requirements, runs tests if any exist, and performs a test-build of the specific `Dockerfile.kumesha`.
