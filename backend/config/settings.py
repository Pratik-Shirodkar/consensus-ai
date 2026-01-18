"""
Configuration settings for Consensus AI
"""
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # AWS Bedrock
    aws_access_key_id: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    aws_secret_access_key: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    aws_region: str = os.getenv("AWS_REGION", "us-east-1")
    bedrock_model_id: str = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")
    
    # WEEX API
    weex_api_key: str = os.getenv("WEEX_API_KEY", "")
    weex_api_secret: str = os.getenv("WEEX_API_SECRET", "")
    weex_passphrase: str = os.getenv("WEEX_PASSPHRASE", "")
    weex_base_url: str = os.getenv("WEEX_BASE_URL", "https://api-contract.weex.com")
    
    # Trading Parameters - COMPETITION MODE (AGGRESSIVE)
    max_leverage: int = int(os.getenv("MAX_LEVERAGE", "20"))  # Max for competition
    max_position_size_pct: float = float(os.getenv("MAX_POSITION_SIZE_PCT", "25"))  # Very aggressive
    default_symbol: str = os.getenv("DEFAULT_SYMBOL", "cmt_btcusdt")
    trading_interval: str = os.getenv("TRADING_INTERVAL", "1m")  # Faster interval
    
    # Server
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    
    # Debate settings - ULTRA AGGRESSIVE for competition
    debate_interval_seconds: int = 15  # Much faster debates = more opportunities
    min_confidence_threshold: float = 0.55  # Lower threshold = many more trades
    
    # Demo Mode (for safe testing without real trades)
    demo_mode: bool = False  # LIVE MODE for competition
    demo_balance: float = 10000.0  # Not used in live mode
    
    # Allowed symbols for trading
    allowed_symbols: list = [
        "cmt_btcusdt", "cmt_ethusdt", "cmt_solusdt", "cmt_dogeusdt",
        "cmt_xrpusdt", "cmt_adausdt", "cmt_bnbusdt", "cmt_ltcusdt"
    ]
    
    class Config:
        env_file = ".env"


settings = Settings()
