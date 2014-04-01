#!/usr/bin/env python2.7
import os
import sys
# if we're rebasing just quit
if os.path.isdir('.git/rebase-merge'):
    sys.exit()

# try to fork as soon as possible to not block shell
try:
    if os.fork():  # will not work on windows
        sys.exit()
except AttributeError:
    pass

import subprocess
import calendar
import json
import requests
from datetime import datetime

GITSHOTS_PATH = os.getenv('GITSHOTS_PATH', '~/.gitshots/')
GITSHOTS_SERVER_URL = os.getenv(
    'GITSHOTS_SERVER_URL',
    'http://gitshots.ranman.org')
GITSHOTS_IMAGE_CMD = os.getenv(
    'GITSHOTS_IMG_CMD',
    'imagesnap -q ')
LOCATION_URI = os.getenv(
    'LOCATION_URI',
    'http://where.ranman.org/current_location.json')

# ensure directory exists
if not os.path.exists(os.path.expanduser(GITSHOTS_PATH)):
    os.makedirs(os.path.expanduser(GITSHOTS_PATH))


def run_command(command):
    """Command helper"""
    return subprocess.check_output(command.split()).rstrip()

#get the top-level directory for this repo:
tld = run_command('git rev-parse --show-toplevel')
failed_path = os.path.join(tld, '.git/failed_gitshots')


# filename is unix epoch time
filename = str(calendar.timegm(datetime.now().utctimetuple())) + '.jpg'
imgpath = os.path.abspath(os.path.expanduser(GITSHOTS_PATH + filename))
img_command = GITSHOTS_IMAGE_CMD + imgpath

user = run_command('git config github.user')
if not user:
    print('run git config --global github.user <user>')
    sys.exit(1)


def post_gitshot(gitshot):
    img = open(gitshot['imgpath'])
    data = json.dumps(gitshot, ensure_ascii=False)
    try:
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
        # check if this is failed and cleanup if it is
        cleanup(gitshot)
    except:
        print("Unable to upload gitshot, saving for later")
        save_gitshot(gitshot)


def save_gitshot(gitshot):
    if not os.path.exists(failed_path):
        os.makedirs(failed_path)
    with open(os.path.join(failed_path, gitshot['sha1']+'.json')) as f:
        f.write(json.dumps(gitshot))


def get_failures():
    if os.path.exists(failed_path):
        gitshots = []
        for fpath in os.listdir(failed_path):
            with open(fpath) as f:
                gitshots.append(json.loads(f.read()))


def cleanup(gitshot):
    if os.path.exists(os.path.join(failed_path, gitshot['sha1']+'.json')):
        os.remove(os.path.join(failed_path, gitshot['sha1']+'.json'))


def get_project():
    data = {}
    try:
        url = run_command('git config remote.origin.url')
        if not url.startswith('http'):
            url = url.replace(':', '/').replace('git@', 'https://')
        url = url.replace('.git', '')
        data['url'] = url
    except:
        pass
    data['project'] = os.path.basename(tld)
    return data


def collect_stats():
    data = {
        'user': user,
        # get the timestamp
        'ts': int(filename[:10]),
        # grab commit message and chop off the last newline
        'msg': run_command('git log -n 1 HEAD --format=format:%s%n%b'),
        # get the shaw 1 of this commit
        'sha1': run_command('git rev-parse HEAD'),
        'branch': run_command('git rev-parse --abbrev-ref HEAD')
    }
    data.update(get_project())
    data['dstats'] = file_stats()
    data['where'] = where()
    try:
        data['imgpath'] = take_gitshot()
    except:
        print("Unable to take a gitshot! Is your image command configured?")
    with open(imgpath[:-3] + 'json', 'w') as f:
        f.write(json.dumps(data, ensure_ascii=False))

    return data


def where():
    # now figure out where we are
    r = requests.get(LOCATION_URI).json()
    if r:
        l = r.get('venue').get('location')
        where = {
            'type': 'Point',
            'coordinates': [l['lng'], l['lat']],
            'err': '0'
        }
        del l['lat']
        del l['lng']
        where.update(l)
        where['ts'] = r['createdAt']
        return where


def file_stats():
    # this command should be empty if this is the first commit
    is_not_initial_commit = run_command('git rev-list --min-parents=1 HEAD')
    if not is_not_initial_commit:
        return 'initial commit'
    stats = run_command('git diff --cached --numstat HEAD~')
    stats = stats.split('\n')
    # split the stats up by number of lines added/removed
    dstats = []
    for line in stats:
        line = line.split('\t')
        st = {'f': line[2]}
        # we can't get line diffs on binary files.
        if '-' in line[:2]:
            st['+'] = 'binary'
            st['-'] = 'binary'
        else:
            st['+'] = int(line[0])
            st['-'] = int(line[1])
        dstats.append(st)
    return dstats


def take_gitshot():
    run_command(img_command)
    return imgpath

if __name__ == '__main__':
    gitshots = get_failures() or []
    gitshots.append(collect_stats())
    if GITSHOTS_SERVER_URL:
        for gitshot in gitshots:
            post_gitshot(gitshot)
