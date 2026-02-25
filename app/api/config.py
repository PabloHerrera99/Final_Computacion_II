import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE_PATH = os.path.join(BASE_DIR, 'cuatro_en_linea.db')

SCHEMA_PATH = os.path.join(BASE_DIR, 'database', 'schema.sql')

# Configuración de Flask
class Config:
    
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DATABASE = DATABASE_PATH
    
    DEBUG = True

    HOST = '0.0.0.0'
    PORT = 5000