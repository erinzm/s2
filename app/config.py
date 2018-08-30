import os

class Config:
    DEBUG = False
    DATABASE_URL = os.environ.get("DATABASE_URL", "postgres://localhost/s2")

class ProdConfig(Config):
    pass

class DevConfig(Config):
    DEBUG = True
    SECRET_KEY = 'd3v3lopm3nt'