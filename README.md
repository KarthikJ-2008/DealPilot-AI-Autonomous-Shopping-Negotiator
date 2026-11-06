# DealPilot AI — Autonomous Shopping Negotiator

> **Developed for the PayPal Hackathon 2026**

DealPilot is an AI-powered shopping assistant designed to help users discover products, negotiate better prices with merchants, and complete secure checkout flows while staying within policy guardrails.

This project combines:
- A FastAPI backend for negotiation and payment workflows
- A browser-based frontend dashboard for product discovery and AI negotiation simulation
- AI-based recommendation logic for purchase decisions
- PayPal Sandbox checkout integration
- Merchant and spending policy enforcement
- Analytics for purchases and savings

---

## Features

- **Product Search & Merchant Comparison:** Discover products and compare prices across multiple supported merchants.
- **AI-Driven Negotiation Flow:** Automated, round-based counteroffer generation powered by Google Gemini.
- **Deal Recommendation Engine:** Intelligent decision-making logic for purchase viability and historical discount analysis.
- **Spending Guardrails & Approval Logic:** Set custom budget limits and policy rules for transaction safety.
- **Merchant Whitelist Support:** Restrict transactions strictly to approved and trusted merchants.
- **PayPal Sandbox Checkout:** Seamless order creation, verification, and payment capture via PayPal Sandbox APIs.
- **Transaction Analytics Dashboard:** Real-time insights into total purchases, spending trends, and money saved.
- **Single-Page Frontend UI:** Clean dashboard designed for smooth demoing and testing.

---

## Tech Stack

### Backend
- **Python:** 3.10+
- **Framework:** FastAPI
- **Validation:** Pydantic
- **Database:** MongoDB (Motor)
- **AI Integration:** Google GenAI / Gemini
- **Payments:** PayPal Sandbox REST API
- **HTTP Client:** HTTPX

### Frontend
- **HTML5 / CSS3 / JavaScript**
- **UI Components:** AG Grid, Font Awesome
- **Data Visualization:** Chart.js

---

## Getting Started

### Prerequisites
Before running the application, ensure you have:
- Python 3.10 or later
- MongoDB instance or MongoDB Atlas connection
- Google Gemini API key
- Channel3 API key (for product search / merchant integrations)
- PayPal Sandbox credentials (`CLIENT_ID` and `CLIENT_SECRET`)

## 1. Clone the Repository

```bash
git clone https://github.com/KarthikJ-2008/DealPilot-AI-Autonomous-Shopping-Negotiator.git
cd DealPilot-AI-Autonomous-Shopping-Negotiator
```

## 2. Set Up the Backend

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment:

**Windows:**
```bash
.venv\Scripts\activate
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## 3. Configure Environment Variables

Create a `.env` file inside the `backend` folder with the following configuration:

```env
PROJECT_NAME=DealPilot AI Backend
ENVIRONMENT=development
DEBUG=True

MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=dealpilot

GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash

CHANNEL3_API_KEY=your_channel3_api_key
CHANNEL3_BASE_URL=https://api.channel3.ai/v1

PAYPAL_CLIENT_ID=your_paypal_client_id
PAYPAL_CLIENT_SECRET=your_paypal_client_secret
PAYPAL_BASE_URL=https://api-m.sandbox.paypal.com

ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000,http://localhost:5500,http://127.0.0.1:5500
```

**Note:** Replace the placeholder API keys and credentials with your actual credentials.

## 4. Run the Backend

Make sure you are inside the `backend` directory and your virtual environment is activated.

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

The backend runs on:

```text
http://127.0.0.1:8000
```

**Note:** The backend serves the API and also hosts the frontend static files under `/app`.

## 5. Open the Frontend

You can access the frontend using any of the following methods:

**Option 1: Open Directly**

Open `frontend/index.html` in your browser.

**Option 2: Use a Local Static File Server**

Run a local static file server to access the frontend.

**Option 3: Access Through the Backend (Recommended)**

Open the following URL in your browser:

```text
http://127.0.0.1:8000/app
```

---

**DealPilot AI – Autonomous Shopping Negotiator**
