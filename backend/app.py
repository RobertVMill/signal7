from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
from newsapi import NewsApiClient
from market_analysis import MarketAnalyst
from company_research import CompanyResearch
from config import get_config
import os
from dotenv import load_dotenv

load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(get_config())

# Configure CORS
CORS(app, resources={
    r"/api/*": {
        "origins": app.config['CORS_ORIGINS'],
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type"]
    }
})

# Initialize clients
newsapi = NewsApiClient(api_key=app.config['NEWS_API_KEY'])
market_analyst = MarketAnalyst()
company_research = CompanyResearch()

COMPANIES = {
    'AAPL': 'Apple',
    'MSFT': 'Microsoft',
    'GOOGL': 'Google',
    'AMZN': 'Amazon',
    'META': 'Meta',
    'TSLA': 'Tesla',
    'NVDA': 'NVIDIA'
}

@app.route('/api/companies', methods=['GET'])
def get_companies():
    return jsonify([
        {'symbol': symbol, 'name': name}
        for symbol, name in COMPANIES.items()
    ])

@app.route('/api/news/<company>', methods=['GET'])
def get_company_news(company):
    logger.info(f"Received news request for {company}")
    
    if company not in COMPANIES:
        logger.error(f"Company not found: {company}")
        return jsonify({'error': 'Company not found'}), 404
    
    try:
        news = newsapi.get_everything(
            q=COMPANIES[company],
            language='en',
            sort_by='publishedAt',
            page_size=5
        )
        logger.info(f"Successfully fetched news for {company}")
        return jsonify(news)
    except Exception as e:
        logger.error(f"Error fetching news: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analysis/<company>', methods=['GET'])
def get_market_analysis(company):
    logger.info(f"Received market analysis request for {company}")
    
    if company not in COMPANIES:
        logger.error(f"Company not found: {company}")
        return jsonify({'error': 'Company not found'}), 404
    
    try:
        # Get period from query parameters, default to 5d
        period = request.args.get('period', '5d')
        if period not in ['1d', '5d', '1mo', '3mo', '1y']:
            logger.error(f"Invalid period: {period}")
            return jsonify({'error': 'Invalid period'}), 400
            
        logger.info(f"Fetching news for {company}")
        # Get news first
        news = newsapi.get_everything(
            q=COMPANIES[company],
            language='en',
            sort_by='publishedAt',
            page_size=5
        )
        
        logger.info(f"Getting market analysis for {company} with period {period}")
        # Get market analysis
        analysis = market_analyst.analyze_market(
            company_name=COMPANIES[company],
            symbol=company,
            news_articles=news['articles'],
            period=period
        )
        
        logger.info("Analysis completed successfully")
        return jsonify(analysis)
    except Exception as e:
        logger.error(f"Error in market analysis: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/ask/<company>', methods=['POST'])
def ask_question(company):
    logger.info(f"Received question for {company}")
    
    if company not in COMPANIES:
        logger.error(f"Company not found: {company}")
        return jsonify({'error': 'Company not found'}), 404
    
    try:
        # Get the question from the request body
        data = request.get_json()
        if not data or 'question' not in data:
            logger.error("No question provided")
            return jsonify({'error': 'No question provided'}), 400
            
        logger.info(f"Fetching news for {company}")
        # Get news first
        news = newsapi.get_everything(
            q=COMPANIES[company],
            language='en',
            sort_by='publishedAt',
            page_size=5
        )
        
        logger.info("Asking AI the question")
        # Ask the question
        answer = market_analyst.ask_financial_question(
            company_name=COMPANIES[company],
            symbol=company,
            question=data['question'],
            news_articles=news['articles']
        )
        
        logger.info("Question answered successfully")
        return jsonify(answer)
    except Exception as e:
        logger.error(f"Error processing question: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/research/<company>', methods=['GET'])
def get_company_research(company):
    logger.info(f"Received research request for {company}")
    
    if company not in COMPANIES:
        logger.error(f"Company not found: {company}")
        return jsonify({'error': 'Company not found'}), 404
    
    try:
        research = company_research.get_company_research(company, COMPANIES[company])
        logger.info("Research completed successfully")
        return jsonify(research)
    except Exception as e:
        logger.error(f"Error getting research: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/search', methods=['GET'])
def search_filings():
    logger.info("Received filings search request")
    try:
        query = request.args.get('q', '')
        form_types = request.args.getlist('form_type')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        page = request.args.get('page', '1')
        
        logger.info(f"Searching filings with query: {query}, form_types: {form_types}")
        results = company_research.search_filings(
            query=query,
            form_types=form_types,
            start_date=start_date,
            end_date=end_date,
            page=page
        )
        
        logger.info("Search completed successfully")
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error searching filings: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
