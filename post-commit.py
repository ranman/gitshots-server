#!/usr/bin/env python
import os
import subprocess
import time
from datetime import datetime
from pymongo import MongoClient
from bson import binary
host = 'localhost'
port = 27017
database = 'gitscraper'
auth = ('gitscraper', 'gitscraper')
gitshots_path = '~/.gitshots/'
image_command = 'imagesnap -q -w .5'
author = 'ranman'
db = MongoClient(host, port, database)
db.authenticate(*auth)
# filename is unix epoch time
filename = str(time.mktime(datetime.now().timetuple()))[:10] + '.jpg'
subprocess.check_output([image_command.split(' '),
                        ''.join(gitshots_path, filename)], shell=False)
imgpath = path = os.path.abspath(os.path.expanduser(gitshots_path + filename))
data = dict()
with open(imgpath, 'rb') as f:
    # binary, yo
    data['img'] = binary.Binary(f.read())

data['author'] = 'ranman'
# timestamp
data['ts'] = datetime.fromtimestamp(int(filename[:10]))
# commit message
data['msg'] = subprocess.check_output(
    ["git", "log", "-n", "1", "HEAD", "--format=format:%s%n%b"],
    shell=False)
# project name or document
data['project'] = os.basename(os.getcwd())
# diff stats
stats = subprocess.check_output(['git', 'diff', 'HEAD~1', '--numstat'])
stats = stats.split('\n')
dstats = [dict(zip(['+', '-', 'f'], line.split('\t'))) for line in stats]
data['dstats'] = dstats
del data['img']
print data
    #db.gitshots.insert(data)
