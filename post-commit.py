#!/usr/bin/env python2.7
# this is an awesome githook by randall at 4am.
# now to get back to real work
import os
import getpass
import subprocess
import time
import json
import requests
from datetime import datetime


gitshots_path = '~/.gitshots/'
server_url = 'http://gitshots.ranman.org'
# must have space at end
img_command = 'imagesnap -q '
# filename is unix epoch time
filename = str(time.mktime(datetime.now().timetuple()))[:10] + '.jpg'
imgpath = os.path.abspath(os.path.expanduser(gitshots_path + filename))
img_command = img_command + imgpath
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
    server_url + '/post_image',
    files={'photo': ('photo', img)}
)
print "Image pushed: {0}".format(response.text)
response = requests.put(
    server_url + '/put_commit/' + response.text,
    data=data
)
print "Data pushed: {0}".format(response.text)
