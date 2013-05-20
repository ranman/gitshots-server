# !/usr/bin/env python2.7
# this is an awesome githook created by randall at 4am.
# it has since been added to by jessepollak

import os
import getpass
import subprocess
import time
import json
import requests
from datetime import datetime

from config import (
    GITSHOTS_PATH,
    GITSHOTS_IMAGE_CMD,
    GITSHOTS_SERVER_URL
)

# filename is unix epoch time
filename = str(time.mktime(datetime.now().timetuple()))[:10] + '.jpg'
imgpath = os.path.abspath(os.path.expanduser(GITSHOTS_PATH + filename))
img_command = GITSHOTS_IMAGE_CMD + imgpath
author = getpass.getuser()

print "Taking capture into {0}...".format(imgpath)
subprocess.check_output(img_command.split(' '), shell=False)

data = dict()

with open(imgpath, 'rb') as f:
    img = f.read()

data['author'] = author
# timestamp
data['ts'] = int(filename[:10])
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
data = json.dumps(data)
response = requests.post(
    GITSHOTS_SERVER_URL + '/post_image',
    files={'photo': ('photo', img)}
)
print "Image pushed: {0}".format(response.text)
response = requests.put(
    GITSHOTS_SERVER_URL + '/put_commit/' + response.text,
    data=data
)
print "Data pushed: {0}".format(response.text)
