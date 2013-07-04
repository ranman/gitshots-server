# !/usr/bin/env python2.7
# this is an awesome githook created by randall at 4am.
# it has since been added to by jessepollak

import os
import io
import getpass
import subprocess
import time
import json
import sys
import requests
from datetime import datetime
if os.fork():
    sys.exit()

GITSHOTS_PATH = '~/.gitshots/'
GITSHOTS_SERVER_URL = os.environ.get(
    'GITSHOTS_SERVER_URL', 'http://gitshots.ranman.org')
GITSHOTS_IMAGE_CMD = 'imagesnap -q '

# ensure directory exists
if not os.path.exists(os.path.expanduser(GITSHOTS_PATH)):
    os.makedirs(os.path.expanduser(GITSHOTS_PATH))

# filename is unix epoch time
filename = str(time.mktime(datetime.now().timetuple()))[:10] + '.jpg'
imgpath = os.path.abspath(os.path.expanduser(GITSHOTS_PATH + filename))
# this may need to change
img_command = GITSHOTS_IMAGE_CMD + imgpath
author = getpass.getuser()

print "Taking capture into {0}...".format(imgpath)
subprocess.check_output(img_command.split(' '), shell=False)

with open(imgpath, 'rb') as f:
    img = f.read()

data = {
    'author': author,
    # get the timestamp
    'ts': int(filename[:10]),
    # grab commit message and chop off the last newline
    'msg': subprocess.check_output(
        'git log -n 1 HEAD --format=format:%s%n%b'.split(),
        shell=False).rstrip(),
    # get the shaw 1 of this commit
    'sha1': subprocess.check_output('git rev-parse HEAD'.split(), shell=False),
    # project name or document
    'project': os.path.basename(os.getcwd()),
}


# this command should be empty if this is the first comit
initial_commit = subprocess.check_output(
    'git rev-list --min-parents=1 HEAD'.split(), shell=False)
if initial_commit:
    stats = subprocess.check_output('git diff HEAD~ --numstat'.split(),
    shell=False)
    stats = stats.split('\n')
    # split the stats up by number of lines added, removed, and the filename
    # then chop off the blank line at the end [:-1]
    dstats = [
        dict(
            zip(
                ['+', '-', 'f'], line.split('\t')
            )
        )
        for line in stats][:-1]
    data['dstats'] = dstats
else:
    data['dstats'] = 'initial commit'

# chop off the jpg extensions and add json instead (ensure unicode)
with io.open(imgpath[:-3] + 'json', 'w', encoding='utf-8') as f:
    f.write(unicode(json.dumps(data, ensure_ascii=False)))

if GITSHOTS_SERVER_URL and GITSHOTS_SERVER_URL.lower() != "false":
    data = json.dumps(data, ensure_ascii=False)
    response = requests.post(
        GITSHOTS_SERVER_URL + '/post_image',
        files={'photo': ('photo', img)}
    )
    response.raise_for_status()
    response = requests.put(
        GITSHOTS_SERVER_URL + '/put_commit/' + response.text,
        data=data
    )
    response.raise_for_status()
