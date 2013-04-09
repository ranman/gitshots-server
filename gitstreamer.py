import os
from flask import Flask, render_template, send_from_directory
from flask.ext.pymongo import PyMongo

app = Flask(__name__)
app.config.update(
    DEBUG=True,
)
mongo = PyMongo(app)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'ico/favicon.ico')


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.route('/')
def index():
    return render_template('index.html')

if __name__ == "__main__":
    app.run()
