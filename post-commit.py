#!/usr/bin/env python
import os
import subprocess
import time
from datetime import datetime
from pymongo import MongoClient
from bson import binary
host = ''
port = 27017
database = 'gitscraper'
auth = ('gitscraper', 'gitscraper')
gitshots_path = '~/.gitshots/'
# must have space at end
img_command = 'imagesnap -q '
# filename is unix epoch time
filename = str(time.mktime(datetime.now().timetuple()))[:10] + '.jpg'
imgpath = os.path.abspath(os.path.expanduser(gitshots_path + filename))
img_command = img_command + imgpath
# ??? BUG: better way to get this?
author = 'ranman'

db = MongoClient(host=host, port=port)[database]
db.authenticate(*auth)


subprocess.check_output(img_command.split(' '), shell=False)
data = dict()
with open(imgpath, 'rb') as f:
    # binary, yo
    data['img'] = binary.Binary(f.read())

data['author'] = author
# timestamp
data['ts'] = datetime.fromtimestamp(int(filename[:10]))
# grab commit message and chop off the last newline
data['msg'] = subprocess.check_output(
    ["git", "log", "-n", "1", "HEAD", "--format=format:%s%n%b"],
    shell=False).rstrip()
# project name or document
data['project'] = os.path.basename(os.getcwd())
# diff stats
stats = subprocess.check_output(['git', 'diff', 'HEAD~1', '--numstat'])
stats = stats.split('\n')
dstats = [dict(zip(['+', '-', 'f'], line.split('\t'))) for line in stats][:-1]
data['dstats'] = dstats
db.gitshots.insert(data)
