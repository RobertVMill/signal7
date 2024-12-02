# Signal 7

A real-time enterprise activity tracker for the tech industry's most influential companies. Monitor enterprise-focused announcements, strategic moves, and market impact of Apple, Microsoft, Alphabet, Amazon, NVIDIA, Meta, and Tesla.

## Features

- Real-time news aggregation focused on enterprise activities
- Stock market data and trends
- Enterprise product launch tracking
- Partnership and acquisition monitoring
- Market sentiment analysis
- Interactive dashboard with customizable alerts

## Tech Stack

- Backend: Python/FastAPI
- Frontend: React with TypeScript
- Database: PostgreSQL
- Real-time updates: WebSockets
- Data Sources: Financial APIs, News APIs, Company Press Releases

## Setup

1. Clone the repository
2. Install Python dependencies: `pip install -r requirements.txt`
3. Install Node.js dependencies: `cd frontend && npm install`
4. Set up environment variables (see `.env.example`)
5. Run the development servers:
   - Backend: `uvicorn app.main:app --reload`
   - Frontend: `cd frontend && npm start`

## Project Structure

```
signal7/
├── app/                    # Backend application
│   ├── api/               # API routes
│   ├── core/              # Core functionality
│   ├── models/            # Database models
│   └── services/          # Business logic
├── frontend/              # React frontend
├── tests/                 # Test suite
├── requirements.txt       # Python dependencies
└── README.md             # Project documentation
```
