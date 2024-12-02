import os
import httpx
import logging
from typing import Dict, List
from datetime import datetime, timedelta
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from .ai_client import AIClient

load_dotenv()

class ResearchAgent:
    def __init__(self):
        self.news_api_key = os.getenv('NEWS_API_KEY')
        if not self.news_api_key:
            raise ValueError("NEWS_API_KEY not found in environment variables")
        # Load a smaller, faster model
        self.embedding_model = SentenceTransformer('paraphrase-MiniLM-L3-v2')
        self.ai_client = AIClient()
        self.companies = {
            'apple': ['Apple', 'AAPL'],
            'microsoft': ['Microsoft', 'MSFT'],
            'google': ['Google', 'Alphabet', 'GOOGL'],
            'amazon': ['Amazon', 'AMZN'],
            'nvidia': ['NVIDIA', 'NVDA'],
            'meta': ['Meta', 'Facebook', 'META'],
            'tesla': ['Tesla', 'TSLA']
        }

    async def get_news(self, query: str) -> List[Dict]:
        """
        Get news articles based on the query.
        """
        try:
            # Enhance the search query for better results
            search_terms = query.lower()
            if 'apple' in search_terms:
                search_terms = '(AAPL OR Apple) AND (earnings OR revenue OR quarterly OR financial results)'
            
            logging.info(f"Fetching news with search terms: {search_terms}")
            
            async with httpx.AsyncClient() as client:
                params = {
                    'q': search_terms,
                    'apiKey': self.news_api_key,
                    'language': 'en',
                    'sortBy': 'relevancy',
                    'from': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                }
                logging.info(f"NewsAPI request params: {params}")
                
                response = await client.get(
                    'https://newsapi.org/v2/everything',
                    params=params
                )
                
                if response.status_code == 200:
                    data = response.json()
                    total_results = len(data.get('articles', []))
                    logging.info(f"NewsAPI returned {total_results} total articles")
                    
                    if not data.get('articles'):
                        logging.warning(f"No articles found for query: {search_terms}")
                        return []
                        
                    articles = [
                        {
                            'title': article['title'],
                            'description': article['description'] or '',
                            'url': article['url'],
                            'published_at': article['publishedAt'],
                            'source': article['source']['name']
                        }
                        for article in data.get('articles', [])[:10]  # Get top 10 articles
                        if article.get('title') and article.get('description')  # Only include articles with title and description
                    ]
                    
                    filtered_count = len(articles)
                    logging.info(f"Filtered to {filtered_count} relevant articles with titles and descriptions")
                    
                    if filtered_count == 0:
                        logging.warning("All articles were filtered out due to missing titles or descriptions")
                    
                    return articles
                else:
                    error_msg = f"NewsAPI error: {response.status_code} - {response.text}"
                    logging.error(error_msg)
                    if response.status_code == 401:
                        logging.error("NewsAPI authentication failed - check your API key")
                    elif response.status_code == 429:
                        logging.error("NewsAPI rate limit exceeded")
                    return []
        except Exception as e:
            logging.error(f"Error in get_news method: {str(e)}")
            return []

    async def research(self, query: str) -> dict:
        """
        Perform research based on the query.
        """
        progress = []
        result = {
            "query": query,
            "articles": [],
            "progress": progress,
            "message": None
        }

        try:
            # Fetch news articles
            progress.append({
                "step": "Fetching recent news articles...",
                "status": "in_progress"
            })
            articles = await self.get_news(query)
            
            if not articles:
                progress[-1]["status"] = "warning"
                progress[-1]["details"] = "No relevant articles found"
                result["message"] = "Could not find any recent news articles matching your query. Try broadening your search terms."
                return result
                
            progress[-1]["status"] = "complete"
            progress[-1]["details"] = f"Found {len(articles)} relevant articles"
            result["articles"] = articles
            
            try:
                # Try to get AI-powered insights
                progress.append({
                    "step": "Expanding research context...",
                    "status": "in_progress"
                })
                expanded_context = await self.ai_client.expand_research_context(query)
                progress[-1]["status"] = "complete"
                result["expanded_context"] = expanded_context

                progress.append({
                    "step": "Generating topic tags...",
                    "status": "in_progress"
                })
                tags = await self.ai_client.generate_tags(query)
                progress[-1]["status"] = "complete"
                result["tags"] = tags

                progress.append({
                    "step": "Analyzing articles for insights...",
                    "status": "in_progress"
                })
                insights = await self.ai_client.generate_insights(articles, query)
                progress[-1]["status"] = "complete"
                progress[-1]["details"] = f"Generated insights from {len(articles)} articles"
                result["insights"] = insights

            except Exception as ai_error:
                logging.error(f"AI features unavailable: {str(ai_error)}")
                # Mark current step as failed
                if progress and progress[-1]["status"] == "in_progress":
                    progress[-1]["status"] = "failed"
                    progress[-1]["error"] = str(ai_error)
                result["message"] = "AI insights temporarily unavailable. Please try again in about an hour."
            
        except Exception as e:
            logging.error(f"Error in research method: {str(e)}")
            if progress and progress[-1]["status"] == "in_progress":
                progress[-1]["status"] = "failed"
                progress[-1]["error"] = str(e)
            raise

        return result
