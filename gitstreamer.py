import os
from flask import Flask, render_template, send_from_directory, make_response, \
    request, Response
from flask.ext.pymongo import PyMongo
from bson.json_util import dumps


def request_wants_json():
    jsonstr = 'application/json'
    best = request.accept_mimetypes.best_match([jsonstr, 'text/html'])
    return best == jsonstr and \
        request.accept_mimetypes[best] > request.accept_mimetypes['text/html']


def jsonify(*args, **kwargs):
    return Response(dumps(dict(*args, **kwargs)), mimetype='application/json')

app = Flask(__name__)
app.config.update(
    DEBUG=True,
    HOST='0.0.0.0',
    PORT=8080,
    MONGO_DBNAME='gitstreamer',
    MONGO_HOST='localhost',
    MONGO_PORT=27017,
    MONGO_USERNAME='gitstreamer',
    MONGO_PASSWORD='gitstreamer'
)
mongo = PyMongo(app)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'), 'ico/favicon.ico')


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.route('/img/<ObjectId:gitshot_id>')
def render_image(gitshot_id):
    img = mongo.db.gitshots.find_one_or_404(gitshot_id, {'img': True})['img']

    def wsgi_app(environ, start_response):
        start_response('200 OK', [('Content-type', 'image/jpeg')])
        return img

    return make_response(wsgi_app)


@app.route('/user/<username>')
def user_profile(username):
    gitshots = mongo.db.gitshots.find({'author': username}, {'img': False})
    if request_wants_json():
        return jsonify(items=[gitshot for gitshot in gitshots])
    return render_template('user.html', gitshots=gitshots)


@app.route('/')
def index():
    gitshots = mongo.db.gitshots.find({}, {'img': False})
    return render_template('index.html', gitshots=gitshots)

if __name__ == "__main__":
    app.run()
