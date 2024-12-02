from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

class DatabaseClient:
    def __init__(self):
        self.client = supabase

    async def fetch_company_data(self, ticker: str):
        """Fetch company profile and latest reports."""
        response = self.client.table('companies').select('*').eq('ticker', ticker).execute()
        return response.data

    async def fetch_financial_data(self, company_id: str, limit: int = 1):
        """Fetch latest financial reports for a company."""
        response = self.client.table('reports')\
            .select('*')\
            .eq('company_id', company_id)\
            .order('report_date', desc=True)\
            .limit(limit)\
            .execute()
        return response.data

    async def store_analysis(self, analysis_data: dict):
        """Store a new analysis."""
        response = self.client.table('analyses').insert(analysis_data).execute()
        return response.data