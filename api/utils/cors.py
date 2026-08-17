import os

def get_cors_origins():
    origins = os.getenv("CORS_ALLOW_ORIGINS", "")
    allowed_origins = [origin.strip() for origin in origins.split(",") if origin.strip()] or ["https://wabi-sabi.beauty", "https://www.wabi-sabi.beauty"]
    return allowed_origins