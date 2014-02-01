import cStringIO
import re
from datetime import datetime
from collections import defaultdict

from flask import (
    Flask,
    render_template,
    make_response,
    request,
    jsonify
)

from flask.ext.pymongo import PyMongo
from flask.ext.cache import Cache
from bson.json_util import loads
from bson import binary, ObjectId
from PIL import Image


def request_wants_json():
    jsonstr = 'application/json'
    best = request.accept_mimetypes.best_match([jsonstr, 'text/html'])
    return best == jsonstr and \
        request.accept_mimetypes[best] > request.accept_mimetypes['text/html']


app = Flask(__name__)
app.config.from_object('config')

cache = Cache(app)
mongo = PyMongo(app)

_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')


@app.template_filter()
def commitmsg(value):
    result = u'\n\n'.join(
        u'<p>{}</p>'.format(p.replace('.\n', '.<br/>\n'))
        for p in _paragraph_re.split(value))
    return result


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
        img.thumbnail((600, 600))
        imgbuf = cStringIO.StringIO()
        img.save(imgbuf, format='JPEG', optimize=True, progressive=True)
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


@app.route('/gitshot/<ObjectId:gitshot_id>.jpg')
@cache.memoize(3600)  # cache for 1 hour
def render_image(gitshot_id):
    def wsgi_app(environ, start_response):
        start_response('200 OK', [
            ('Content-Type', 'image/jpeg'),
            ('Cache-Control', 'max-age=43200')
        ])
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
    limit = int(request.args.get('limit', 10))
    sort = request.args.get('sort', 'ts')
    projects = mongo.db.gitshots.find(
        {'author': username}).distinct('project')
    gitshots = []
    for project in projects:
        shots = mongo.db.gitshots.find(
            {'author': username,
             'project': project},
            {'img': False}
        ).limit(limit).sort(sort, -1)
        gitshots.extend(shots)

    if request_wants_json():
        return jsonify(items=list(gitshots))
    ret = defaultdict(list)
    for gitshot in gitshots:
        ret[gitshot['project']].append(gitshot)
    return render_template('user.html', gitshots=ret)


@app.route('/project/<project>')
def project(project):
    limit = int(request.args.get('limit', 100))
    sort = request.args.get('sort', 'ts')
    gitshots = mongo.db.gitshots.find(
        {'project': project},
        {'img': False}
    ).limit(limit).sort(sort, -1)
    if request_wants_json():
        return jsonify(items=[list(gitshots)])
    ret = defaultdict(list)
    for gitshot in gitshots:
        ret[gitshot['project']].append(gitshot)
    return render_template('project.html', gitshots=ret)


@app.route('/gitshot/<ObjectId:gitshot_id>.html')
def gitshot(gitshot_id):
    gitshot = mongo.db.gitshots.find_one(ObjectId(gitshot_id))
    return render_template('commit.html', gitshot=gitshot)


@app.route('/')
@cache.memoize(300)  # cache for five minutes
def index():
    projects = mongo.db.gitshots.distinct('project')
    users = mongo.db.gitshots.distinct('author')
    return render_template('index.html', projects=projects, users=users)


if __name__ == "__main__":
    app.run()
