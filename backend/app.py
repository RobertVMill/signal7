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
    if company not in COMPANIES:
        return jsonify({'error': 'Company not found'}), 404
    
    try:
        news = newsapi.get_everything(
            q=COMPANIES[company],
            language='en',
            sort_by='publishedAt',
            page_size=5
        )
        return jsonify(news)
    except Exception as e:
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
    if company not in COMPANIES:
        return jsonify({'error': 'Company not found'}), 404
    
    try:
        # Get the question from the request body
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({'error': 'No question provided'}), 400
            
        # Get news first
        news = newsapi.get_everything(
            q=COMPANIES[company],
            language='en',
            sort_by='publishedAt',
            page_size=5
        )
        
        # Get analysis for the specific question
        response = market_analyst.ask_financial_question(
            company_name=COMPANIES[company],
            symbol=company,
            question=data['question'],
            news_articles=news['articles']
        )
        
        return jsonify(response)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/research/<company>', methods=['GET'])
def get_company_research(company):
    if company not in COMPANIES:
        return jsonify({'error': 'Company not found'}), 404
    
    try:
        research = company_research.get_company_research(
            symbol=company,
            company_name=COMPANIES[company]
        )
        return jsonify(research)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search-filings', methods=['POST'])
@cross_origin()
def search_filings():
    try:
        data = request.get_json()
        query = data.get('query')
        if not query:
            return jsonify({
                'success': False,
                'error': 'Search query is required'
            }), 400

        # Get optional parameters
        company_symbol = data.get('company_symbol')
        form_types = data.get('form_types')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        page = data.get('page', '1')

        # Perform the search
        results = company_research.search_filings(
            query=query,
            company_symbol=company_symbol,
            form_types=form_types,
            start_date=start_date,
            end_date=end_date,
            page=page
        )

        return jsonify(results)

    except Exception as e:
        app.logger.error(f"Error in search-filings endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
