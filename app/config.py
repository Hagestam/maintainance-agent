from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    openai_api_key: str
    whatsapp_token: str
    phone_number_id: str
    whatsapp_verify_token: str
    
    class Config:
        env_file = ".env"
        
settings = Settings()

#This reads everything from your .env file and makes it available anywhere in 
#your project as settings.openai_api_key, settings.whatsapp_token, etc. 
#Clean and centralised — you never hardcode a key into actual code.