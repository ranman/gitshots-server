import cStringIO
from datetime import datetime
from collections import defaultdict

from flask import (
    Flask,
    render_template,
    make_response,
    request,
    Response,
    jsonify
)

from flask.ext.pymongo import PyMongo
from flask.ext.cache import Cache
from bson.json_util import dumps, loads
from bson import binary
import Image


def request_wants_json():
    jsonstr = 'application/json'
    best = request.accept_mimetypes.best_match([jsonstr, 'text/html'])
    return best == jsonstr and \
        request.accept_mimetypes[best] > request.accept_mimetypes['text/html']


app = Flask(__name__)
app.config.from_object('config')

cache = Cache(app)
mongo = PyMongo(app)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.route('/post_image', methods=['POST'])
def post_image():
    f = request.files['photo']
    if f:
        imgstr = cStringIO.StringIO(f.stream.read())
        img = Image.open(imgstr)
        img.convert('RGB')
        img.thumbnail((300, 300))
        imgbuf = cStringIO.StringIO()
        img.save(imgbuf, format='JPEG')
        gitshot = dict(img=binary.Binary(imgbuf.getvalue()))
        return str(mongo.db.gitshots.insert(gitshot))
    return 400


@app.route('/post_commit', methods=['POST'])
def post_commit(gitshot_id):
    data = loads(request.data)
    data['ts'] = datetime.fromtimestamp(data['ts'])
    return str(mongo.db.gitshots.save(data))


@app.route('/put_commit/<ObjectId:gitshot_id>', methods=['PUT'])
def put_commit(gitshot_id):
    data = loads(request.data)
    data['ts'] = datetime.fromtimestamp(data['ts'])
    gitshot = mongo.db.gitshots.find_one_or_404(gitshot_id)
    gitshot.update(data)
    return str(mongo.db.gitshots.save(gitshot))


@app.route('/img/<ObjectId:gitshot_id>.jpg')
@cache.memoize(3600)  # cache for 1 hour
def render_image(gitshot_id):
    def wsgi_app(environ, start_response):
        start_response('200 OK', [('Content-type', 'image/jpeg')])
        return img

    gitshot = mongo.db.gitshots.find_one_or_404(gitshot_id, {'img': True})
    if 'img' in gitshot:
        img = gitshot['img']
        return make_response(wsgi_app)
    else:
        img = open('static/no_image.jpg').read()
        return make_response(wsgi_app)


@app.route('/user/<username>')
def user_profile(username):
    gitshots = mongo.db.gitshots.find({'author': username}, {'img': False})
    if request_wants_json():
        return jsonify(items=list(gitshots))
    ret = defaultdict(list)
    for gitshot in gitshots:
        ret[gitshot['project']].append(gitshot)
    return render_template('user.html', gitshots=ret)


@app.route('/project/<project>')
def project(project):
    gitshots = mongo.db.gitshots.find({'project': project}, {'img': False})
    if request_wants_json():
        return jsonify(items=[list(gitshots)])
    ret = defaultdict(list)
    for gitshot in gitshots:
        ret[gitshot['project']].append(gitshot)
    return render_template('project.html', gitshots=ret)


@app.route('/')
def index():
    projects = mongo.db.gitshots.distinct('project')
    users = mongo.db.gitshots.distinct('author')
    return render_template('index.html', projects=projects, users=users)


if __name__ == "__main__":
    app.run()
