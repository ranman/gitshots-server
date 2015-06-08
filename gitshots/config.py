import os

DEBUG = os.environ.get('GITSHOTS_DEBUG', True)

if os.environ.get('MONGOHQ_URL'):
    MONGO_URI = os.environ.get('MONGOHQ_URL')

GITSHOTS_BASE_URL = os.environ.get('GITSHOTS_BASE_URL', 'http://gitshots.com')   

MONGO_DBNAME = os.environ.get('MONGO_DB', 'gitshots')
MONGO_HOST = os.environ.get('MONGO_HOST', '192.168.59.103')
MONGO_PORT = os.environ.get('MONGO_PORT', 27017)
MONGO_USERNAME = os.environ.get('MONGO_USERNAME', None)
MONGO_PASSWORD = os.environ.get('MONGO_PASSWORD', None)

SLACK_TOKEN = os.environ.get('SLACK_TOKEN', None)
SLACK_CHANNEL = os.environ.get('SLACK_CHANNEL', '#git')

AUTH_USERNAME = os.environ.get('AUTH_USERNAME', None)
AUTH_PASSWORD = os.environ.get('AUTH_PASSWORD', None)

CACHE_TYPE = 'filesystem'
CACHE_DIR = 'cache'

MAX_CONTENT_LENGTH = 4 * 1024 * 1024  # No more than 10MB per file
