from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict
from app.services.research_agent import ResearchAgent

router = APIRouter()

class ResearchRequest(BaseModel):
    query: str

class CompanyAnalysisRequest(BaseModel):
    ticker: str

@router.post("/research")
async def perform_research(request: ResearchRequest):
    try:
        agent = ResearchAgent()
        
        # Initialize response with progress steps
        result = {
            "status": "in_progress",
            "progress": [
                {"step": "Initializing research", "status": "pending"},
                {"step": "Searching for relevant articles", "status": "pending"},
                {"step": "Analyzing information", "status": "pending"},
                {"step": "Generating insights", "status": "pending"}
            ]
        }
        
        # Update progress as we go
        result["progress"][0]["status"] = "complete"
        expanded_query = await agent.ai_client.expand_research_context(request.query)
        
        result["progress"][1]["status"] = "complete"
        articles = await agent.get_news(request.query)
        
        result["progress"][2]["status"] = "complete"
        tags = await agent.ai_client.generate_tags(request.query)
        
        result["progress"][3]["status"] = "in_progress"
        insights = await agent.ai_client.generate_insights(articles, request.query)
        result["progress"][3]["status"] = "complete"
        
        # Add the final results
        result.update({
            "status": "complete",
            "query": request.query,
            "expanded_query": expanded_query,
            "articles": articles,
            "tags": tags,
            "insights": insights
        })
        
        return result
    except Exception as e:
        print(f"Error in research endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing your request: {str(e)}"
        )

@router.post("/analyze/{ticker}")
async def analyze_company(ticker: str) -> Dict:
    """Generate comprehensive analysis for a company."""
    agent = ResearchAgent()
    try:
        result = await agent.analyze_company(ticker)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test-openai")
async def test_openai():
    """Test if OpenAI API key is working"""
    try:
        agent = ResearchAgent()
        # Try a simple completion to test the API
        test_result = agent.ai_client.expand_research_context("test query")
        return {
            "status": "success",
            "message": "OpenAI API is working correctly",
            "test_response": test_result
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"OpenAI API error: {str(e)}"
        }

@router.get("/test-newsapi")
async def test_newsapi():
    """Test if NewsAPI key is working"""
    try:
        agent = ResearchAgent()
        articles = await agent.get_news("AAPL earnings")
        return {
            "status": "success",
            "message": f"NewsAPI is working. Found {len(articles)} articles",
            "articles": articles
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"NewsAPI error: {str(e)}"
        }
