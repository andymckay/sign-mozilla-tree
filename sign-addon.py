import os
import pprint
import random
import shutil
import sys
import tempfile
import time

from zipfile import ZipFile

import tempfile

import requests
import jwt

from utils import get_id_version, is_xpi, is_signed

AMO_KEY = os.environ['AMO_SIGNING_KEY']
AMO_SECRET = os.environ['AMO_SIGNING_SECRET']
server = 'https://addons.mozilla.org'

found = []
signed = []

files_to_ignore = (
    # These are not a valid zip file.
    'toolkit/mozapps/extensions/test/addons/test_install4/badaddon.xpi',
    'toolkit/mozapps/extensions/test/addons/test_install7/addon1.xpi',
    'toolkit/mozapps/extensions/test/addons/test_install7/addon2.xpi',
    'toolkit/mozapps/extensions/test/xpcshell/data/corrupt.xpi',
    'toolkit/mozapps/extensions/test/xpcshell/data/corruptfile.xpi',
    # These shouldn't be signed at all.
    'toolkit/mozapps/extensions/test/browser/unsigned_hotfix.xpi',
    'toolkit/mozapps/extensions/test/xpcshell/data/empty.xpi',
    # Not sure...
    'toolkit/mozapps/extensions/test/xpcshell/data/signing_checks/hotfix_broken.xpi'
)


def sign_addon(path):
    if is_xpi(path):
        sign(path, copyover=True)

    else:
        tmpfd, tmpname = tempfile.mkstemp()
        os.close(tmpfd)
        orig = os.path.curdir
        with ZipFile(tmpname, 'w') as zout:
            for root, dirs, files in os.walk(path):
                for filename in files:
                    os.chdir(root)
                    zout.write(filename)

        os.chdir(orig)
        filename = sign(tmpname, copyover=False)

        with ZipFile(filename, 'w') as zin:
            zin.extractall(path)


def sign(path, copyover=False):
    if path.endswith(files_to_ignore):
        print 'Skipping: %s' % path
        return

    found.append(path)
    print
    print 'Signing addon: %s' % path
    if is_signed(path):
        print 'Addon: %s is already signed' % path
        return

    id, version = get_id_version(path)
    print ' ID: %s, Version: %s' % (id, version)

    url = server + '/api/v3/addons/%s/versions/%s/' % (id, version)
    print ' Signing addon on server: %s' % url

    with open(path, 'r') as xpi:
        res = requests.put(
            url,
            files={'upload': xpi},
            headers=server_auth()
        )
        if res.status_code == 409:
            print ' Version already exists on server'
        elif res.status_code == 201:
            print ' Version created'
            if not res.json()['automated_signing']:
                print 'Warning: not automatically signed.'
                return


    exit = False
    downloaded = False
    for x in range(0, 8):
        res = requests.get(
            url,
            headers=server_auth()
        )
        if res.status_code == 403:
            print ' Server returned: %s' % res.status_code
            print ' No access to sign: %s' % path
            return

        assert res.status_code == 200, 'Server returned: %s' % res.status_code

        for file in res.json()['files']:
            if file['signed']:
                print ' Downloading signed copy.'
                res = requests.get(
                    file['download_url'],
                    headers=server_auth()
                )
                assert res.status_code == 200
                download, download_name = tempfile.mkstemp('.xpi')
                open(download_name, 'w').write(res.content)
                print ' Downloaded to %s' % download_name
                downloaded = True
                exit = True
            else:
                print ' File there, but not signed.'
                pprint.pprint(res.json())
                exit = True

        if x > 6:
            print ' Taking more than a few seconds, likely something went wrong...'
            pprint.pprint(res.json())

        if exit:
            break

        time.sleep(1)
        print ' ... waiting.'
    else:
        print ' Warning: failed to download for %s' % path

    if downloaded:
        shutil.copy(download_name, path)
        print 'Signing complete for %s' % path
        signed.append(path)


def server_auth():
    issue = time.time()
    payload = {
        'iss': AMO_KEY,
        'iat': issue,
        'jti': random.random(),
        'exp': issue + 60,
    }
    return {
        'Authorization': 'JWT %s' % jwt.encode(
            payload, AMO_SECRET, algorithm='HS256')
    }


def check_auth():
    url = server + '/api/v3/accounts/profile/'
    print 'Checking server auth:', url
    res = requests.get(url, headers=server_auth())
    assert res.status_code == 200, 'Could not authenticate with server'


def find_addons(dir_or_file):
    if os.path.isfile(dir_or_file):
        sign(dir_or_file)
        return

    found_files = []
    for root, dirs, files in os.walk(dir_or_file):
        for filename in files:
            if filename.endswith('.xpi'):
                found_files.append(os.path.join(root, filename))

# Attempt to sign directories, but that's a bit flaky.
#    if not found_files:
#        sign_addon(dir_or_file)

    for k, filename in enumerate(found_files):
        print 'File: %s.' % (k + 1)
        sign_addon(filename)

    print '-'  * 40
    print 'Found %s addons.' % len(found_files)

    not_signed = [path for path in found if path not in signed]
    if not_signed:
        print 'The following were NOT signed:'
        for path in found:
            if path not in signed:
                print ' %s' % path

    if signed:
        print 'The following %s were signed:' % len(signed)
        for path in signed:
            print ' %s' % path


if __name__ == '__main__':
    check_auth()
    find_addons(sys.argv[1])
