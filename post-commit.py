#!/usr/bin/env ruby
import subprocess
import time
from datetime import datetime
from pymongo import MongoClient
from bson import binary
db = MongoClient().gitscraper
gitshots_path = '~/.gitshots/'
filename = str(time.mktime(datetime.now().timetuple()))[:10] + '.jpg'
subprocess.check_output('imagesnap', '-q', '-w', '.5',
                        ''.join(gitshots_path, filename), shell=False)
with open(filename, 'rb') as f:
    data = dict()
    # binary, yo
    data['img'] = binary.Binary(f.read())
    # timestamp
    data['ts'] = datetime.fromtimestamp(int(filename[:10]))
    # commit message
    data['msg'] = subprocess.check_output(
        ["git", "log", "-n", "1", "HEAD", "--format=format:%s%n%b"],
        shell=False)
    # project name or document
    data['project'] = ''
    # diff stats
    data['dstats']
    #db.gitshots.insert(data)

