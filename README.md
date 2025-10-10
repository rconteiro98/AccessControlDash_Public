# AccessControlDash

A **multi-container access control platform** that integrates ANPR (Automatic Number Plate Recognition) with a PostgreSQL database, Flask webhook API, and Nginx static server.

I built the **Webhook**, **Database**, and **Nginx containers**, plus the Docker Compose integration.  
The **Django Dashboard** UI was developed by a teammate and connects to the same database.

---

## 🧩 Architecture



Camera → Flask Webhook → PostgreSQL
↳ saves XML & images → served via Nginx
↳ optional Email / Telegram alerts


---

## 🚀 Quick Start

### With Docker
```bash
git clone https://github.com/<your-username>/access-control-dash.git
cd access-control-dash
cp .env.example .env
docker compose up --build


Services

Flask Webhook → http://localhost:5000/webhookcallback

Images served via Nginx:

http://localhost/licenseimage/

http://localhost/detectionimage/

🧾 Example Request

Send test data to the webhook:

curl -X POST http://localhost:5000/webhookcallback \
  -F "anpr.xml=@test/anpr.xml" \
  -F "platePicture.jpg=@test/plate.jpg" \
  -F "detectionPicture.jpg=@test/detect.jpg"

🗄️ Database Schema

The main table for detections:

CREATE TABLE public.lprdetecciones (
  id SERIAL PRIMARY KEY,
  ipAddress VARCHAR(255),
  eventType VARCHAR(255),
  licensePlate VARCHAR(50),
  vehicleType VARCHAR(50),
  confidenceLevel INT,
  direction VARCHAR(50),
  channelName VARCHAR(100),
  licenseImage TEXT,
  detectionImage TEXT,
  dataTime TIMESTAMP
);

🧠 Technologies

Flask (Gunicorn) – Webhook API

PostgreSQL 17 – Database

Nginx – Static serving

Docker Compose – Multi-service orchestration

Optional: yagmail + python-telegram-bot for notifications

📊 Django Dashboard

Frontend interface built by a teammate.
Connects to the same PostgreSQL DB.
Repo: access-control-dashboard

🔒 Notes

Never commit real .env files or credentials.

Use .env.example as a safe template.

Default ports: 5000 (Flask), 80 (Nginx), 5433 (Postgres).

🧑‍💻 Author

Ruben Conteiro
Infrastructure & Backend Engineer
📧 rconteiro98@gmail.com

🌐 linkedin.com/in/rconteiro


---

## 🪞 5. GitHub repo details

### 🏷️ Tagline (for the top of your GitHub page)
> **ANPR Access Control System — Flask + PostgreSQL + Nginx + Docker Compose. I built the backend containers and infra integration.**

### 🧠 Suggested Topics


docker
flask
postgresql
nginx
gunicorn
docker-compose
anpr
iot
smart-systems
devops
python
automation


---

## ✅ Folder Summary

When you finish, your root directory should look like this:



access-control-dash/
├── DB/
├── Webhook/
├── Nginx/
├── docker-compose.yml
├── .env.example
├── .gitignore
├── LICENSE
└── README.md
