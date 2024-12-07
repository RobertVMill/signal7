# Signal7 - AI Research Platform for Big Tech

An AI-powered research platform focused on the Big 7 tech companies.

## Current Features
- Real-time market analysis for Big 7 tech companies
- News aggregation and sentiment analysis
- SEC filings integration
- Interactive market data visualization
- AI-powered company research and analysis
- Clean, modern dashboard interface

## Setup Instructions

### Backend Setup
1. Create a virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt
```

2. Create a .env file in the backend directory with your API keys:
```
NEWS_API_KEY=your_news_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
SEC_API_KEY=your_sec_api_key_here
```

3. Run the Flask server:
```bash
python app.py
```

### Frontend Setup
1. Install dependencies:
```bash
cd frontend
npm install
```

2. For local development:
```bash
npm run dev
```

3. For production build:
```bash
npm run build
npm start
```

## Deployment Instructions

### Docker Deployment
The easiest way to deploy Signal7 is using Docker:

1. Make sure you have Docker and Docker Compose installed
2. Copy `.env.example` to `.env` and fill in your API keys:
```bash
cp backend/.env.example backend/.env
```

3. Build and start the containers:
```bash
docker-compose up --build
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:5001

To run in production:
1. Update the `CORS_ORIGINS` in docker-compose.yml with your domain
2. Update `NEXT_PUBLIC_API_URL` with your backend API URL
3. Deploy using Docker Compose or Kubernetes

### Alternative Deployment Methods

#### Frontend Deployment (Vercel)
1. Fork this repository to your GitHub account
2. Create a new project on Vercel and connect it to your GitHub repository
3. Set the following environment variables in Vercel:
   - `NEXT_PUBLIC_API_URL`: Your backend API URL

#### Backend Deployment
The backend can be deployed to any cloud platform that supports Python (e.g., Heroku, DigitalOcean, AWS):

1. Set up your chosen cloud platform
2. Configure the following environment variables:
   - `NEWS_API_KEY`
   - `OPENAI_API_KEY`
   - `SEC_API_KEY`
3. Deploy the backend code
4. Update the frontend's `NEXT_PUBLIC_API_URL` to point to your deployed backend

## Tech Stack
- Frontend: Next.js 15 with TypeScript and Tailwind CSS
- Backend: Python Flask with LangChain
- Data Sources:
  - Yahoo Finance API for market data
  - NewsAPI for real-time news
  - SEC API for filings data
- AI: OpenAI for analysis and insights
- Charts: Recharts for data visualization

## Security Notes
- Never commit `.env` files to version control
- Always use environment variables for sensitive data
- Keep API keys secure and rotate them regularly
- Use CORS and rate limiting in production

## Contributing
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License
MIT License
