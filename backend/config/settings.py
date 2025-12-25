"""
Configuration settings for Consensus AI
"""
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # WEEX API
    weex_api_key: str = os.getenv("WEEX_API_KEY", "")
    weex_api_secret: str = os.getenv("WEEX_API_SECRET", "")
    weex_passphrase: str = os.getenv("WEEX_PASSPHRASE", "")
    weex_base_url: str = os.getenv("WEEX_BASE_URL", "https://api-contract.weex.com")
    
    # OpenAI
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    
    # Trading Parameters
    max_leverage: int = int(os.getenv("MAX_LEVERAGE", "20"))
    max_position_size_pct: float = float(os.getenv("MAX_POSITION_SIZE_PCT", "10"))
    default_symbol: str = os.getenv("DEFAULT_SYMBOL", "cmt_btcusdt")
    trading_interval: str = os.getenv("TRADING_INTERVAL", "5m")
    
    # Server
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    
    # Debate settings
    debate_interval_seconds: int = 60  # How often to run debates
    min_confidence_threshold: float = 0.7  # Minimum confidence to propose
    
    class Config:
        env_file = ".env"


settings = Settings()
