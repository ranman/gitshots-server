import os

DEBUG = True

if os.environ.get('MONGOHQ_URL'):
    MONGO_URI = os.environ.get('MONGOHQ_URL')

MONGO_DBNAME = os.environ.get('MONGO_DB', 'gitshots')
MONGO_HOST = os.environ.get('MONGO_HOST', 'localhost')
MONGO_PORT = os.environ.get('MONGO_PORT', 27017)
MONGO_USERNAME = os.environ.get('MONGO_USERNAME', None)
MONGO_PASSWORD = os.environ.get('MONGO_PASSWORD', None)

AUTH_USERNAME = os.environ.get('AUTH_USERNAME', None)
AUTH_PASSWORD = os.environ.get('AUTH_PASSWORD', None)

CACHE_TYPE = 'filesystem'
CACHE_DIR = 'static/imgs'

MAX_CONTENT_LENGTH = 4 * 1024 * 1024  # No more than 10MB per file system
