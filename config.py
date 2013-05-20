import os

DEBUG = True

MONGO_DBNAME = os.environ.get('MONGO_DB', 'gitshots')
MONGO_HOST = os.environ.get('MONGO_HOST', 'localhost')
MONGO_PORT = os.environ.get('MONGO_PORT', 27017)
MONGO_USERNAME = os.environ.get('MONGO_USERNAME', None)
MONGO_PASSWORD = os.environ.get('MONGO_PASSWORD', None)

CACHE_TYPE = 'filesystem'
CACHE_DIR = 'static/imgs'

UPLOAD_FOLDER = 'uploads'

GITSHOTS_PATH = '~/.gitshots/'
GITSHOTS_SERVER_URL = os.environ.get('GITSHOTS_SERVER_URL', 'http://gitshots.ranman.org')
GITSHOTS_IMAGE_CMD = 'imagesnap -q '

MAX_CONTENT_LENGTH = 4 * 1024 * 1024  # No more than 4MB per file system
