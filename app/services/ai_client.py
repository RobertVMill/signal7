from openai import AsyncOpenAI
import os
from dotenv import load_dotenv
from datetime import datetime
import logging

# Force reload of environment variables
load_dotenv(override=True)

class AIClient:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        logging.info(f"Initializing OpenAI client with key starting with: {api_key[:8]}...")
        
        self.client = AsyncOpenAI(
            api_key=api_key
        )

    async def expand_research_context(self, query: str) -> dict:
        """Expand user query with additional context."""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a research analyst assistant."},
                    {"role": "user", "content": f"Expand this research query with relevant context: {query}"}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"Error in expand_research_context: {str(e)}")
            raise

    async def generate_tags(self, query: str) -> list:
        """Generate relevant research tags."""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Generate relevant research tags. Return only a comma-separated list of tags, no other text."},
                    {"role": "user", "content": f"Generate 3-5 relevant research tags for: {query}"}
                ]
            )
            # Split the response into an array of tags and clean them
            tags = [tag.strip() for tag in response.choices[0].message.content.split(',')]
            return tags
        except Exception as e:
            logging.error(f"Error in generate_tags: {str(e)}")
            raise

    async def generate_insights(self, articles: list, query: str) -> dict:
        """Generate insights from news articles."""
        try:
            if not articles:
                raise ValueError("No articles provided for analysis")
                
            articles_text = "\n\n".join([
                f"Article {i+1}:\nTitle: {article['title']}\nSource: {article['source']}\nDescription: {article['description']}"
                for i, article in enumerate(articles[:5])  # Limit to top 5 articles
            ])
            
            # First, get the main insights
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system", 
                        "content": """You are a senior research analyst providing insights on tech companies. 
                        Format your response in markdown with proper headers and formatting:
                        
                        1. Use # for main headers (e.g. # Key Insights)
                        2. Use ## for subheaders (e.g. ## Summary of Key Developments)
                        3. Use - for bullet points
                        4. Use **bold** for emphasis
                        5. Include article references in (Article X)
                        6. Use proper line breaks between sections"""
                    },
                    {
                        "role": "user", 
                        "content": f"""Based on these recent news articles about '{query}':\n\n{articles_text}\n\n
                        Provide a well-formatted markdown analysis with:
                        
                        # Key Insights
                        
                        ## Summary of Key Developments
                        - List 2-3 major developments
                        - Reference specific articles
                        
                        ## Key Insights for Business Leaders
                        - Provide 3 actionable insights
                        - Support with article references
                        
                        ## Potential Risks and Challenges
                        - Identify key risks
                        - Support with evidence"""
                    }
                ]
            )
            
            # Then, get an explanation of the analysis process
            process_response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """Explain the research and analysis process clearly and transparently.
                        Format your response in markdown with:
                        
                        1. Use # for the main header
                        2. Use ## for process steps
                        3. Use - for bullet points
                        4. Use **bold** for emphasis"""
                    },
                    {
                        "role": "user",
                        "content": f"""For the query '{query}', explain:
                        
                        # Analysis Process
                        
                        ## Article Analysis
                        - How you analyzed the articles
                        - What methods you used
                        
                        ## Pattern Identification
                        - What patterns or trends you identified
                        - How you connected information across articles
                        
                        ## Information Prioritization
                        - How you prioritized information
                        - What factors influenced your analysis
                        
                        ## Limitations
                        - Any limitations in the analysis
                        - What additional data would be helpful"""
                    }
                ]
            )
            
            return {
                "analysis": response.choices[0].message.content,
                "process_explanation": process_response.choices[0].message.content,
                "timestamp": datetime.now().isoformat(),
                "sources": [
                    {
                        "title": article['title'],
                        "source": article['source'],
                        "url": article['url']
                    }
                    for article in articles[:5]
                ]
            }
        except Exception as e:
            logging.error(f"Error in generate_insights: {str(e)}")
            raise

    async def analyze(self, prompt: str) -> dict:
        """Generate analysis from provided data."""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert business analyst."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"Error in analyze: {str(e)}")
            raise