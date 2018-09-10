import os

class Config:
    DEBUG = False
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    POSTGRES_URL = os.environ.get("POSTGRES_URL", "postgres://localhost/s2")

class ProdConfig(Config):
    pass

class DevConfig(Config):
    DEBUG = True
    SECRET_KEY = 'd3v3lopm3nt'