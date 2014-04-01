# Copyright (c) 2014, Randall Hunt
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import cStringIO
import re
from subprocess import Popen, PIPE
from datetime import datetime
from collections import defaultdict
from functools import wraps

from flask import (
    Flask,
    render_template,
    make_response,
    request,
    jsonify,
    Response,
    send_file
)

from flask.ext.pymongo import PyMongo
from flask.ext.cache import Cache
from bson.json_util import loads
from bson import binary, ObjectId
from PIL import Image
from PIL import ImageFile

# we have to set a larger block size for images
ImageFile.MAXBLOCK = 1920*1080

app = Flask(__name__)
app.config.from_object('config')
cache = Cache(app)
mongo = PyMongo(app)

_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')
FFMPEG = "ffmpeg -y -f image2pipe -vcodec mjpeg -i - -vcodec mpeg4 -qscale 5 -r {0} {1}.avi"


def request_wants_json():
    jsonstr = 'application/json'
    best = request.accept_mimetypes.best_match([jsonstr, 'text/html'])
    return best == jsonstr and \
        request.accept_mimetypes[best] > request.accept_mimetypes['text/html']


def check_auth(username, password):
    return (username == app.config['AUTH_USERNAME'] and
            password == app.config['AUTH_PASSWORD'])


def authenticate():
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if (app.config['AUTH_USERNAME'] and app.config['AUTH_PASSWORD']) and (
                not auth or not check_auth(auth.username, auth.password)):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


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
        width, height = img.size
        if not(width <= 1920 and height <= 1080):
            img.thumbnail((1920, 1080), Image.ANTIALIAS)
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


@app.route('/install')
def install():
    return send_file('install.sh')


@app.route('/<user>/')
@requires_auth
def user_profile(user):
    limit = int(request.args.get('limit', 10))
    sort = request.args.get('sort', 'ts')
    projects = mongo.db.gitshots.find({'user': user}).distinct('project')
    gitshots = []
    for project in projects:
        shots = mongo.db.gitshots.find(
            {'user': user,
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


@app.route('/<user>.avi')
@requires_auth
def render_video(user):
    images = mongo.db.gitshots.find({'user': user, 'img': {'$exists': True}})
    if images.count() <= 10:
        frames = 2
    elif images.count() < 100:
        frames = 15
    else:
        frames = 24
    cmd = FFMPEG.format(frames, user)
    p = Popen(cmd.split(), stdin=PIPE)
    for image in images:
        p.stdin.write(image['img'])
    p.stdin.close()
    p.wait()
    return send_file(open(user+'.avi'), as_attachment=True)


@app.route('/<ObjectId:gitshot_id>.jpg')
@requires_auth
@cache.memoize(3600)  # cache in app for 1 hour
def render_image(gitshot_id):
    gitshot = mongo.db.gitshots.find_one_or_404(gitshot_id)
    img = gitshot.get('img')
    response = make_response(img)
    response.content_type = 'image/jpeg'
    response.headers['Cache-Control'] = 'max-age=43200'
    return response


@app.route('/<ObjectId:gitshot_id>')
@requires_auth
def gitshot(gitshot_id):
    gitshot = mongo.db.gitshots.find_one(ObjectId(gitshot_id))
    return render_template('commit.html', gitshot=gitshot)


@app.route('/<user>/<project>/commit/<sha1>.jpg')
@requires_auth
def get_image_by_sha1(user, project, sha1):
    gitshot = mongo.db.gitshots.find_one_or_404(
        {'project': project, 'sha1': sha1},
        {'img': False})
    return render_image(gitshot['_id'])


@app.route('/<user>/<project>/commit/<sha1>')
@requires_auth
def github_sha1(user, project, sha1):
    gitshot = mongo.db.gitshots.find_one_or_404(
        {'project': project, 'sha1': sha1},
        {'img': False})
    return render_template('commit.html', gitshot=gitshot)


@app.route('/gs/<project>')
@requires_auth
def gitshot_project(project):
    limit = int(request.args.get('limit', 100))
    sort = request.args.get('sort', 'ts')
    gitshots = mongo.db.gitshots.find(
        {'project': project}, {'img': False}
    ).limit(limit).sort(sort, -1)

    if request_wants_json():
        return jsonify(items=[list(gitshots)])

    ret = defaultdict(list)
    for gitshot in gitshots:
        ret[gitshot['project']].append(gitshot)
    return render_template('project.html', gitshots=ret)


@app.route('/<user>/<project>/commits')
@requires_auth
def github_project(user, project):
    limit = int(request.args.get('limit', 100))
    sort = request.args.get('sort', 'ts')
    gitshots = mongo.db.gitshots.find(
        {'project': project, 'user': user},
        {'img': False}
    ).limit(limit).sort(sort, -1)

    if request_wants_json():
        return jsonify(items=[list(gitshots)])

    ret = defaultdict(list)
    for gitshot in gitshots:
        ret[gitshot['project']].append(gitshot)
    return render_template('project.html', gitshots=ret)


@app.route('/')
@requires_auth
@cache.memoize(300)  # cache for five minutes
def index():
    users = mongo.db.gitshots.distinct('user')
    return render_template('index.html', users=users)


if __name__ == "__main__":
    app.run()
