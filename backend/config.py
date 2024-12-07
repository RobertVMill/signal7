import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask settings
    DEBUG = False
    TESTING = False
    
    # API keys
    NEWS_API_KEY = os.getenv('NEWS_API_KEY')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    SEC_API_KEY = os.getenv('SEC_API_KEY')
    
    # CORS settings
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'https://signal7.vercel.app').split(',')
    
    # Rate limiting
    RATELIMIT_DEFAULT = "100 per day"
    RATELIMIT_STORAGE_URL = os.getenv('REDIS_URL', 'memory://')

class DevelopmentConfig(Config):
    DEBUG = True
    CORS_ORIGINS = ['http://localhost:3000', 'http://localhost:3001', 'http://localhost:3002']

class ProductionConfig(Config):
    # Production-specific settings
    pass

class TestingConfig(Config):
    TESTING = True

# Map environment names to config classes
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

# Get config based on environment
def get_config():
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])
