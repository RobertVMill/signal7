import os
import logging
from datetime import datetime, timedelta
from sec_api import ExtractorApi, QueryApi
from typing import Dict, List, Any, Optional
import re

class CompanyResearch:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        sec_api_key = os.getenv('SEC_API_KEY')
        if not sec_api_key:
            self.logger.warning("SEC_API_KEY not found in environment variables")
        self.sec_api = QueryApi(api_key=sec_api_key) if sec_api_key else None

    def get_company_research(self, symbol: str, company_name: str) -> Dict[str, Any]:
        """Get comprehensive research data for a company."""
        try:
            if not self.sec_api:
                self.logger.warning("SEC API not initialized - missing API key")
                return {
                    "success": False,
                    "filing_summary": "SEC filing data unavailable - API key not configured"
                }

            # Get SEC filings from the last year
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            
            query = {
                "query": {
                    "query_string": {
                        "query": f"ticker:{symbol} AND (formType:\"10-K\" OR formType:\"10-Q\" OR formType:\"8-K\")",
                        "time_zone": "America/New_York"
                    }
                },
                "from": "0",
                "size": "50",
                "sort": [{"filedAt": {"order": "desc"}}]
            }

            filings = self.sec_api.get_filings(query)
            
            # Organize filings by type with enhanced metadata
            organized_filings = {
                '10-K': [],
                '10-Q': [],
                '8-K': []
            }

            for filing in filings.get('filings', []):
                form_type = filing.get('formType', '')
                if form_type in organized_filings:
                    # Enhanced filing metadata
                    filing_data = {
                        'type': form_type,
                        'title': filing.get('description', ''),
                        'date': filing.get('filedAt', ''),
                        'url': filing.get('linkToFilingDetails', ''),
                        'accessionNo': filing.get('accessionNo', ''),
                        'periodOfReport': filing.get('periodOfReport', ''),
                        'highlights': self._extract_highlights(filing),
                        'documents': self._extract_documents(filing)
                    }
                    
                    # Add 8-K specific data
                    if form_type == '8-K':
                        filing_data['items'] = filing.get('items', [])
                    
                    organized_filings[form_type].append(filing_data)

            # Generate a summary of recent filings
            filing_summary = self._generate_filing_summary(organized_filings, company_name)

            # Get quarterly trends analysis
            quarterly_trends = self.analyze_quarterly_trends(symbol)

            return {
                "success": True,
                "sec_filings": organized_filings,
                "filing_summary": filing_summary,
                "quarterly_trends": quarterly_trends if quarterly_trends.get('success') else None
            }

        except Exception as e:
            self.logger.error(f"Error fetching SEC data for {symbol}: {str(e)}")
            return {
                "success": False,
                "filing_summary": f"Unable to fetch SEC filings at this time: {str(e)}"
            }

    def _extract_documents(self, filing: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract important documents from a filing."""
        documents = []
        for doc in filing.get('documentFormatFiles', []):
            if doc.get('type') and doc.get('documentUrl'):
                documents.append({
                    'type': doc['type'],
                    'url': doc['documentUrl'],
                    'description': doc.get('description', ''),
                    'size': doc.get('size', '')
                })
        return documents

    def _extract_highlights(self, filing: Dict[str, Any]) -> List[str]:
        """Extract important highlights from a filing."""
        highlights = []
        
        # Add description
        description = filing.get('description', '')
        if description:
            highlights.append(description)
            
        # Add 8-K items if present
        items = filing.get('items', [])
        if items:
            highlights.extend([f"Reported {item}" for item in items])
            
        return highlights

    def _generate_filing_summary(self, filings: Dict[str, List[Dict]], company_name: str) -> str:
        """Generate a human-readable summary of recent filings."""
        try:
            summary_parts = []
            
            # Add 10-K summary with period
            if filings['10-K']:
                latest_10k = filings['10-K'][0]
                period = latest_10k.get('periodOfReport', '').split('T')[0]
                summary_parts.append(
                    f"Most recent annual report (10-K) filed on {latest_10k['date'][:10]}" +
                    (f" for period ending {period}" if period else "")
                )

            # Add 10-Q summary with periods
            recent_10q = filings['10-Q'][:3]  # Last 3 quarters
            if recent_10q:
                quarters = [f"{q.get('periodOfReport', '').split('T')[0]}" for q in recent_10q]
                summary_parts.append(
                    f"Filed {len(recent_10q)} quarterly reports (10-Q) in the past year" +
                    (f" for periods ending {', '.join(quarters)}" if quarters[0] else "")
                )

            # Add 8-K summary
            recent_8k = filings['8-K'][:5]  # Last 5 material events
            if recent_8k:
                summary_parts.append(
                    f"Filed {len(recent_8k)} material event notices (8-K) recently"
                )

            if not summary_parts:
                return f"No significant SEC filings found for {company_name} in the past year."

            return " | ".join(summary_parts)

        except Exception as e:
            self.logger.error(f"Error generating filing summary: {str(e)}")
            return "Error generating SEC filing summary"

    def search_filings(self, 
                      query: str, 
                      company_symbol: Optional[str] = None,
                      form_types: Optional[List[str]] = None,
                      start_date: Optional[str] = None,
                      end_date: Optional[str] = None,
                      page: str = "1") -> Dict[str, Any]:
        """
        Search through SEC filings using full-text search.
        
        Args:
            query: Search query string (can include boolean operators, exact phrases)
            company_symbol: Optional company ticker symbol to filter results
            form_types: Optional list of form types to filter results
            start_date: Optional start date in YYYY-MM-DD format
            end_date: Optional end date in YYYY-MM-DD format
            page: Page number for pagination (100 results per page)
        """
        try:
            if not self.sec_api:
                return {
                    "success": False,
                    "error": "SEC API not initialized - missing API key"
                }

            # Build the search request
            search_request = {
                "query": query,
                "page": page
            }

            # Add optional filters
            if company_symbol:
                # Get CIK for the company if symbol is provided
                cik_query = {
                    "query": {
                        "query_string": {
                            "query": f"ticker:{company_symbol}",
                            "time_zone": "America/New_York"
                        }
                    },
                    "from": "0",
                    "size": "1"
                }
                company_info = self.sec_api.get_filings(cik_query)
                if company_info.get('filings'):
                    cik = company_info['filings'][0].get('cik')
                    if cik:
                        search_request["ciks"] = [cik]

            if form_types:
                search_request["formTypes"] = form_types

            if start_date:
                search_request["startDate"] = start_date

            if end_date:
                search_request["endDate"] = end_date

            # Make the full-text search request
            response = self.sec_api.post("full-text-search", search_request)

            # Process and format the results
            formatted_results = []
            for filing in response.get('filings', []):
                result = {
                    'accessionNo': filing.get('accessionNo'),
                    'companyName': filing.get('companyNameLong', '').split(' (')[0],
                    'ticker': filing.get('ticker'),
                    'formType': filing.get('formType'),
                    'documentType': filing.get('type'),
                    'description': filing.get('description'),
                    'filingUrl': filing.get('filingUrl'),
                    'filedAt': filing.get('filedAt'),
                }
                
                # For 10-Q filings, extract quarterly highlights
                if filing.get('formType') == '10-Q' and filing.get('filingUrl'):
                    highlights = self.extract_quarterly_highlights(filing.get('filingUrl'))
                    if highlights.get('success'):
                        result['quarterlyHighlights'] = highlights
                
                formatted_results.append(result)

            return {
                "success": True,
                "total": response.get('total', {'value': 0, 'relation': 'eq'}),
                "results": formatted_results,
                "page": page
            }

        except Exception as e:
            self.logger.error(f"Error in full-text search: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to perform full-text search: {str(e)}"
            }

    def extract_quarterly_highlights(self, filing_url: str) -> Dict[str, Any]:
        """Extract key financial metrics and highlights from a 10-Q filing.
        
        Args:
            filing_url: URL to the SEC filing
            
        Returns:
            Dictionary containing key financial metrics and highlights
        """
        try:
            if not self.sec_api:
                return {"error": "SEC API not initialized"}
                
            # Initialize ExtractorApi for getting specific sections
            extractor_api = ExtractorApi(api_key=self.sec_api.api_key)
            
            # Get key sections from the 10-Q
            md_and_a = extractor_api.get_section(filing_url, "part1item2", "text")  # Management Discussion & Analysis
            risk_factors = extractor_api.get_section(filing_url, "part2item1a", "text")  # Risk Factors
            financial_statements = extractor_api.get_section(filing_url, "part1item1", "text")  # Financial Statements
            
            # Extract key metrics using regex patterns
            metrics = {
                "revenue": self._extract_metric(financial_statements, r"Total revenue[s]?\s*(?:of)?\s*\$?([\d,]+(?:\.\d+)?)\s*(?:million|billion)?"),
                "net_income": self._extract_metric(financial_statements, r"Net income[s]?\s*(?:of)?\s*\$?([\d,]+(?:\.\d+)?)\s*(?:million|billion)?"),
                "eps": self._extract_metric(financial_statements, r"Earnings per share[s]?\s*(?:of)?\s*\$?([\d,]+(?:\.\d+)?)"),
                "cash": self._extract_metric(financial_statements, r"Cash and cash equivalents[s]?\s*(?:of)?\s*\$?([\d,]+(?:\.\d+)?)\s*(?:million|billion)?"),
            }
            
            # Extract key highlights from MD&A
            highlights = []
            if md_and_a:
                # Split into paragraphs and get first few meaningful ones
                paragraphs = [p.strip() for p in md_and_a.split('\n\n') if len(p.strip()) > 100]
                highlights = paragraphs[:3]  # Get top 3 most relevant paragraphs
            
            # Extract key risks
            risks = []
            if risk_factors:
                # Split into bullet points or paragraphs and get top risks
                risk_points = [r.strip() for r in risk_factors.split('\n\n') if len(r.strip()) > 100]
                risks = risk_points[:3]  # Get top 3 most significant risks
                
            return {
                "metrics": metrics,
                "highlights": highlights,
                "risks": risks,
                "success": True
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting quarterly highlights: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to extract quarterly highlights: {str(e)}"
            }
            
    def _extract_metric(self, text: str, pattern: str) -> Optional[str]:
        """Helper method to extract financial metrics using regex patterns."""
        if not text:
            return None
            
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    def analyze_quarterly_trends(self, symbol: str, num_quarters: int = 4) -> Dict[str, Any]:
        """Analyze trends across multiple quarterly reports.
        
        Args:
            symbol: Company ticker symbol
            num_quarters: Number of recent quarters to analyze
            
        Returns:
            Dictionary containing quarterly metrics and trend analysis
        """
        try:
            if not self.sec_api:
                return {"error": "SEC API not initialized"}

            # Get recent 10-Q filings
            query = {
                "query": {
                    "query_string": {
                        "query": f"ticker:{symbol} AND formType:\"10-Q\"",
                        "time_zone": "America/New_York"
                    }
                },
                "from": "0",
                "size": str(num_quarters),
                "sort": [{"filedAt": {"order": "desc"}}]
            }

            filings = self.sec_api.get_filings(query)
            
            # Extract metrics from each quarterly report
            quarterly_data = []
            for filing in filings.get('filings', []):
                if filing.get('filingUrl'):
                    highlights = self.extract_quarterly_highlights(filing.get('filingUrl'))
                    if highlights.get('success') and highlights.get('metrics'):
                        quarterly_data.append({
                            'quarter': filing.get('periodOfReport', '').split('T')[0],
                            'metrics': highlights['metrics']
                        })

            # Calculate quarter-over-quarter changes
            trends = {
                'revenue_growth': [],
                'net_income_growth': [],
                'eps_growth': [],
                'cash_change': []
            }
            
            for i in range(len(quarterly_data) - 1):
                current = quarterly_data[i]['metrics']
                previous = quarterly_data[i + 1]['metrics']
                
                for metric in ['revenue', 'net_income', 'eps', 'cash']:
                    if current.get(metric) and previous.get(metric):
                        try:
                            current_val = float(current[metric].replace(',', ''))
                            prev_val = float(previous[metric].replace(',', ''))
                            pct_change = ((current_val - prev_val) / prev_val) * 100
                            trends[f'{metric}_growth'].append({
                                'period': quarterly_data[i]['quarter'],
                                'change': round(pct_change, 2)
                            })
                        except (ValueError, TypeError):
                            continue

            return {
                "success": True,
                "quarterly_data": quarterly_data,
                "trends": trends,
                "summary": self._generate_trend_summary(trends)
            }

        except Exception as e:
            self.logger.error(f"Error analyzing quarterly trends: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to analyze quarterly trends: {str(e)}"
            }

    def _generate_trend_summary(self, trends: Dict[str, List[Dict[str, Any]]]) -> str:
        """Generate a human-readable summary of quarterly trends."""
        summary_points = []
        
        for metric, changes in trends.items():
            if changes:
                # Get the most recent change
                latest = changes[0]
                if abs(latest['change']) > 10:  # Only highlight significant changes
                    direction = "increased" if latest['change'] > 0 else "decreased"
                    metric_name = metric.replace('_growth', '').replace('_', ' ').title()
                    summary_points.append(
                        f"{metric_name} {direction} by {abs(round(latest['change'], 1))}% "
                        f"compared to previous quarter"
                    )

        if not summary_points:
            return "No significant quarter-over-quarter changes detected."
            
        return " | ".join(summary_points)
