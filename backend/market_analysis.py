import logging
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import os
from company_research import CompanyResearch

class MarketAnalyst:
    def __init__(self):
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.llm = ChatOpenAI(temperature=0.7)
        self.company_research = CompanyResearch()
        self.analysis_prompt = ChatPromptTemplate.from_template("""
            Analyze the market activity for {company_name} ({symbol}) based on the following data:
            
            Stock Data:
            - Current Price: ${current_price}
            - Price Change: {price_change}%
            - Volume: {volume}
            - 5-day High: ${high}
            - 5-day Low: ${low}
            
            Recent News:
            {news_summary}
            
            Recent SEC Filings:
            {sec_summary}
            
            Please provide a comprehensive analysis including:
            1. Key market movements and their potential causes
            2. Important news developments and their impact
            3. Significant SEC filings and their implications
            4. Overall market sentiment
            5. Key takeaways for investors
            
            Keep the analysis clear, factual, and focused on the most important points.
            """)
        
        # Create the analysis chain using LCEL
        self.chain = self.analysis_prompt | self.llm | StrOutputParser()

    def get_stock_data(self, symbol, period="5d"):
        max_retries = 3
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Fetching stock data for {symbol} with period {period} (attempt {attempt + 1}/{max_retries})")
                stock = yf.Ticker(symbol)
                
                # First try to get basic info to validate the ticker
                try:
                    # Only request minimal info first
                    info = stock.fast_info
                    if not info:
                        raise ValueError("No stock info available")
                except Exception as e:
                    self.logger.error(f"Failed to get stock info: {str(e)}")
                    raise ValueError(f"Invalid stock symbol or API error: {symbol}")
                
                # Adjust interval based on period for better data resolution
                interval = "1h" if period in ["1d", "5d"] else "1d"
                hist = stock.history(period=period, interval=interval)
                
                if len(hist) == 0:
                    self.logger.error(f"No data returned for {symbol}")
                    raise ValueError(f"No stock data available for {symbol}")
                
                # Get historical data for chart
                chart_data = []
                for date, row in hist.iterrows():
                    chart_data.append({
                        "date": date.strftime("%Y-%m-%d %H:%M"),
                        "price": round(row['Close'], 2),
                        "volume": int(row['Volume'])
                    })
                
                current_price = hist['Close'].iloc[-1]
                prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
                price_change = ((current_price - prev_close) / prev_close) * 100
                
                # Calculate technical indicators
                sma_20 = hist['Close'].rolling(window=min(20, len(hist))).mean().iloc[-1]
                sma_50 = hist['Close'].rolling(window=min(50, len(hist))).mean().iloc[-1]
                rsi = self._calculate_rsi(hist['Close'])
                
                # Use fast_info for basic data to avoid rate limiting
                market_cap = getattr(info, 'market_cap', 0) or 0
                
                return {
                    "current_price": f"{current_price:.2f}",
                    "price_change": f"{price_change:.2f}",
                    "volume": f"{hist['Volume'].iloc[-1]:,}",
                    "avg_volume": f"{int(hist['Volume'].mean()):,}",
                    "high": f"{hist['High'].max():.2f}",
                    "low": f"{hist['Low'].min():.2f}",
                    "chart_data": chart_data,
                    "technical_indicators": {
                        "sma_20": f"{sma_20:.2f}",
                        "sma_50": f"{sma_50:.2f}",
                        "rsi": f"{rsi:.2f}",
                    },
                    "market_data": {
                        "market_cap": market_cap,
                        "pe_ratio": 0,  # Simplified for now
                        "dividend_yield": 0,
                        "beta": 0,
                        "52w_high": getattr(info, 'year_high', 0) or 0,
                        "52w_low": getattr(info, 'year_low', 0) or 0,
                    }
                }
            except Exception as e:
                self.logger.error(f"Error fetching stock data for {symbol} (attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                    continue
                raise ValueError(f"Failed to fetch stock data after {max_retries} attempts: {str(e)}")

    def _calculate_rsi(self, prices, period=14):
        """Calculate Relative Strength Index."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs.iloc[-1]))

    def analyze_market(self, company_name, symbol, news_articles, period="5d"):
        self.logger.info(f"Starting market analysis for {company_name} ({symbol})")
        
        try:
            # Get stock data
            self.logger.info(f"Fetching stock data for period: {period}")
            stock_data = self.get_stock_data(symbol, period)
            self.logger.info("Successfully fetched stock data")
            
            # Prepare news summary
            self.logger.info("Preparing news summary")
            news_summary = "\n".join([
                f"- {article['title']} ({article['publishedAt']})"
                for article in news_articles[:5]
            ])
            
            # Get SEC filings summary
            self.logger.info("Fetching SEC filings")
            sec_data = self.company_research.get_company_research(symbol, company_name)
            sec_summary = sec_data.get('filing_summary', 'No recent SEC filings found.')
            
            # Prepare input for the analysis chain
            self.logger.info("Preparing analysis input")
            chain_input = {
                "company_name": company_name,
                "symbol": symbol,
                **stock_data,
                "news_summary": news_summary,
                "sec_summary": sec_summary
            }
            
            # Run the analysis chain
            self.logger.info("Running analysis chain")
            analysis = self.chain.invoke(chain_input)
            self.logger.info("Analysis completed successfully")
            
            return {
                "success": True,
                "analysis": analysis,
                "data_sources": {
                    "stock_data": {
                        "source": "Yahoo Finance",
                        "period": period,
                        "metrics": ["price", "volume"]
                    }
                },
                "stock_data": {
                    "current_price": float(stock_data["current_price"]),
                    "price_change": float(stock_data["price_change"]),
                    "percent_change": float(stock_data["price_change"]),
                    "volume": int(stock_data["volume"].replace(",", "")),
                    "high_5d": float(stock_data["high"]),
                    "low_5d": float(stock_data["low"]),
                    "chart_data": stock_data["chart_data"]
                }
            }
        except Exception as e:
            self.logger.error(f"Analysis failed: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to analyze market data: {str(e)}"
            }

    def ask_financial_question(self, company_name, symbol, question, news_articles):
        try:
            stock_data = self.get_stock_data(symbol)
            if not stock_data:
                return {
                    "success": False,
                    "error": "Could not fetch stock data"
                }
                
            # Get SEC filings data
            sec_data = self.company_research.get_company_research(symbol, company_name)
            sec_summary = sec_data.get('filing_summary', '') if sec_data.get('success', False) else ''
                
            # Format news articles into a summary
            news_summary = "\n".join([
                f"- {article['title']}: {article['description']}"
                for article in news_articles[:5]
            ])
            
            # Create a specialized prompt for financial questions
            financial_prompt = ChatPromptTemplate.from_template("""
                You are a financial expert analyzing {company_name} ({symbol}). 
                
                Current Market Data:
                - Current Price: ${current_price}
                - Price Change: {price_change}%
                - Volume: {volume}
                - 5-day High: ${high}
                - 5-day Low: ${low}
                
                Recent News:
                {news_summary}
                
                Recent SEC Filings:
                {sec_summary}
                
                Question from a financial professional: {question}
                
                Please provide a detailed, professional analysis focusing on:
                - Relevant market metrics and their implications
                - Impact of recent news and developments
                - Insights from recent SEC filings
                - Technical and fundamental factors
                - Potential risks and opportunities
                - Professional recommendations or considerations
                
                Keep the response concise but thorough, using financial terminology appropriate for a professional audience.
                """)
            
            # Create a specialized chain for financial questions
            qa_chain = financial_prompt | self.llm | StrOutputParser()
            
            # Prepare input for the chain
            chain_input = {
                "company_name": company_name,
                "symbol": symbol,
                "question": question,
                **stock_data,
                "news_summary": news_summary,
                "sec_summary": sec_summary
            }
            
            # Run the analysis chain
            analysis = qa_chain.invoke(chain_input)
            return {
                "success": True,
                "analysis": analysis,
                "stock_data": {
                    "current_price": float(stock_data["current_price"]),
                    "price_change": float(stock_data["price_change"]),
                    "percent_change": float(stock_data["price_change"]),
                    "volume": int(stock_data["volume"].replace(",", "")),
                    "high_5d": float(stock_data["high"]),
                    "low_5d": float(stock_data["low"]),
                    "chart_data": stock_data["chart_data"]
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
