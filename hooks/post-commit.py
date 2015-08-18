#!/usr/bin/env python2.7
import os
import sys
import subprocess


def run_command(command):
    return subprocess.check_output(command.split()).rstrip()

#get the top-level directory for this repo:
tld = run_command('git rev-parse --show-toplevel')

# if we're rebasing just quit
if os.path.isdir(os.path.join(tld, '.git/rebase-merge')):
    sys.exit()

import calendar
import json
import requests
from datetime import datetime

GITSHOTS_PATH = os.getenv('GITSHOTS_PATH', '~/.gitshots/')
GITSHOTS_SERVER_URL = os.getenv('GITSHOTS_SERVER_URL', 'http://gitshots.com/api')
GITSHOTS_IMAGE_CMD = os.getenv('GITSHOTS_IMG_CMD', 'imagesnap -w 1.0 -q ')
LOCATION_CMD = os.getenv('LOCATION_CMD', 'CoreLocationCLI -once yes -format %longitude_%latitude')
LOCATION_URI = os.getenv('LOCATION_URI', 'http://iplocator.adaofeliz.com/api/location')

# ensure directory exists
if not os.path.exists(os.path.expanduser(GITSHOTS_PATH)):
    os.makedirs(os.path.expanduser(GITSHOTS_PATH))

failed_path = os.path.join(tld, '.git/failed_gitshots')


# filename is unix epoch time
filename = str(calendar.timegm(datetime.now().utctimetuple())) + '.jpg'
imgpath = os.path.abspath(os.path.expanduser(GITSHOTS_PATH + filename))
img_command = GITSHOTS_IMAGE_CMD + imgpath

try:
    user = run_command('git config github.user')
except:
    import getpass
    user = getpass.getuser()
    print('run git config --global github.user <user>')


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
        return False
    except:
        save_gitshot(gitshot)
        return True


def save_gitshot(gitshot):
    if not os.path.exists(failed_path):
        os.makedirs(failed_path)
    with open(os.path.join(failed_path, gitshot['sha1']+'.json'), 'w') as f:
        f.write(json.dumps(gitshot))


def get_failures():
    gitshots = []
    if os.path.exists(failed_path):
        for fpath in os.listdir(failed_path):
            with open(os.path.join(failed_path, fpath)) as f:
                gitshots.append(json.loads(f.read()))
    return gitshots


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
        'sha1': run_command('git rev-parse HEAD'),
        'branch': run_command('git rev-parse --abbrev-ref HEAD'),
        'dstats': file_stats()
    }
    data.update(where())
    data.update(get_project())
    try:
        data['imgpath'] = take_gitshot()
    except:
        print("Unable to take a gitshot! Is your image command configured?")
    with open(imgpath[:-3] + 'json', 'w') as f:
        f.write(json.dumps(data, ensure_ascii=False))
    return data


def where():

    # now figure out where we are
    where = {}

    if LOCATION_CMD:
        try:
            location = run_command(GITSHOTS_WHERE_CMD).split('_')
            longitude = location[0]
            latitude = location[1]
            where = {
                'type': 'Point',
                'coordinates': [longitude, latitude],
                'properties': {'err': '0'}
            }
            where['properties']['ts'] = int(filename[:10])
            where = {'where': where}
        except:
            print('Unable to grab location data using ' + LOCATION_CMD)

    elif LOCATION_URI:
        try:
            r = requests.get(LOCATION_URI).json()
            if r:
                l = r.get('location')
                where = {
                    'type': 'Point',
                    'coordinates': [l['longitude'], l['latitude']],
                    'properties': {'err': '0'}
                }
                del l['latitude'], l['longitude']
                where['properties'].update(l)
                where['properties']['ts'] = int(filename[:10])
                where = {'where': where}
        except:
            print('Unable to grab location data from ' + LOCATION_URI)

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
        if len(line) > 0:
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
    gitshots = get_failures()
    for gitshot in gitshots:
        if post_gitshot(gitshot):
            print("Upload failed, saving {0}".format(gitshot['sha1']))

    # try to fork as soon as possible to not block shell
    try:
        if os.fork():  # will not work on windows
            sys.exit()
    except AttributeError:
        pass

    gitshot = collect_stats()  # collect the stats
    if GITSHOTS_SERVER_URL:  # upload them
        post_gitshot(gitshot)
