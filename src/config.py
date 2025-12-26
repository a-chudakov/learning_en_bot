from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    telegram_token: str = Field(
        ...,  
        description="Telegram bot token from @BotFather"
    )
        default="learning_en_bot", 
        description="Bot username"
    )
    
    # БАЗА ДАННЫХ
    
    database_path: str = Field(
        default="./data/bot.db",
        description="Path to database"
    )
   
    # ЛОГИРОВАНИЕ
    
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
   
    # ЧАСОВОЙ ПОЯС
    
    timezone: str = Field(
        default="UTC",
        description="Timezone for scheduled tasks"
    )
    
    # НАСТРОЙКИ PYDANTIC
    
    class Config:
        env_file = Path(__file__).parent.parent / ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

_config: Optional[Settings] = None

def get_config() -> Settings:
    global _config
    if _config is None:
        _config = Settings()
        db_path = Path(_config.database_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
    return _config
