import os

class Settings:
    """
    A class to hold all configuration settings for the application.
    """
    HASHED_PASSWORDS_FILE = "/app_data/hashed_passwords.json"
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
    USER_USERNAME = os.getenv("USER_USERNAME")
    USER_PASSWORD = os.getenv("USER_PASSWORD")
    
settings = Settings()