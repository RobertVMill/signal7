from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
import yfinance as yf
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
router = APIRouter()

class ResearchRequest(BaseModel):
    query: str

class CompanyAnalysisRequest(BaseModel):
    ticker: str

@router.post("/research")
async def perform_research(request: ResearchRequest):
    try:
        logger.info(f"Research request received: {request.query}")
        return {
            "status": "success",
            "query": request.query,
            "message": "Research functionality coming soon"
        }
    except Exception as e:
        logger.error(f"Research failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/company/{ticker}")
async def get_company_info(ticker: str):
    try:
        logger.info(f"Fetching info for {ticker}")
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Get basic stock information
        return {
            "status": "success",
            "company": {
                "name": info.get("longName", ""),
                "symbol": ticker,
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
                "current_price": info.get("currentPrice", 0),
                "market_cap": info.get("marketCap", 0),
                "pe_ratio": info.get("trailingPE", 0)
            }
        }
    except Exception as e:
        logger.error(f"Failed to get company info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test")
async def test_endpoint():
    return {"status": "API is working"}
