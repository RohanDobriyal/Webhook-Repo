# Webhook-Repo

A simple Flask-based GitHub webhook receiver and real-time event viewer.



## GitHub Repositories

* **Action Repo** (dummy code): [RohanDobriyal/dummy-repo](https://github.com/RohanDobriyal/dummy-repo)
* **Webhook Repo** (this project): [RohanDobriyal/Webhook-Repo](https://github.com/RohanDobriyal/Webhook-Repo)



## Overview

1. **GitHub → Webhook**: Receives `push` and `pull_request` events.
2. **Normalization → MongoDB**: Stores minimal fields (`request_id`, `author`, `action`, `from_branch`, `to_branch`, `timestamp`).
3. **Polling UI**: Static HTML page that fetches `/events` every 15 seconds and displays colored cards.



## Quick Start

### 1. Clone this repo

```bash
git clone https://github.com/RohanDobriyal/Webhook-Repo.git
cd Webhook-Repo
```

### 2. Create a virtual environment & install

```bash
python -m venv venv
venv\Scripts\activate     # Windows
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env` if necessary:

```
MONGO_URI=mongodb://localhost:27017
MONGO_DB=github_events
MONGO_COLLECTION=events
PORT=5000
```

### 4. Run services

* **MongoDB**: ensure it’s running locally or update `MONGO_URI` accordingly.
* **Flask app**:

  ```bash
  python app.py
  ```
* **ngrok tunnel** (for GitHub to reach your local server):

  ```bash
  ngrok http 5000
  ```

  Copy the HTTPS URL for webhook setup.



## Configure GitHub Webhook

In your **Action Repo** (`dummy-repo`) → **Settings** → **Webhooks**:

* **Payload URL**: `https://<NGROK_SUBDOMAIN>.ngrok-free.app/webhook`
* **Content type**: `application/json`
* **Events**: Select **Push** and **Pull requests**



## Usage

* **UI**: Open `http://localhost:5000/` (or your ngrok URL) to see the live dashboard.
* **API**:

  * `GET /events` — returns JSON array of latest 50 events.
  * `POST /webhook` — GitHub’s webhook target.



## Folder Structure

```
Webhook-Repo/
├── app.py             # Flask server
├── requirements.txt   # Python dependencies
├── .env.example       # Environment variable template
└── static/            # Static UI files
    └── index.html
`
