import os

class Config:
    DEBUG = False

class ProdConfig(Config):
    pass

class DevConfig(Config):
    DEBUG = True
    SECRET_KEY = 'd3v3lopm3nt'