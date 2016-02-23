import os
import sys

from zipfile import BadZipfile

from utils import get_id_version, is_signed, set_version


def find_addons(directory):
    found_files = {}
    for root, dirs, files in os.walk(directory):
        for filename in files:
            filename = os.path.join(root, filename)
            if filename.endswith('.xpi'):
                print 'Checking: %s' % filename
                try:
                    if is_signed(filename):
                        print ' Already signed.'
                        continue
                except (BadZipfile, KeyError):
                    print ' Error processing.'
                    continue

                try:
                    id, version = get_id_version(filename)
                except KeyError:
                    print ' Error processing.'
                    continue

                unique = '%s-%s' % (id, version)
                found_files.setdefault(unique, [])
                found_files[unique].append({
                    'path': os.path.join(root, filename),
                    'id': id,
                    'version': version
                })
    return found_files


def print_addons(found_files):
    print
    for unique, files in found_files.items():
        if len(files) < 2:
            continue
        else:
            print 'Addon id: %s, found %s files' % (unique, len(files))
            for filename in files:
                print '*', filename['path']
        print


def next_version(version):
    pre, post = version.split('.')
    post = int(post) + 1
    return '%s.%s' % (pre, post)


def fix_addons(found_files, addon_id):
    fix_addons = []
    for unique, files in found_files.items():
        skip = False
        for addon in files:
            if addon['id'] != addon_id:
                skip = True

        if skip:
            continue

        fix_addons.append((addon['path'], addon['version']))

    fix_addons = sorted(fix_addons)
    assert len(fix_addons) > 1, '%s add-on with that id' % len(fix_addons)
    base = fix_addons[0][1]
    for path, version in fix_addons[0:]:
        new_version = next_version(base)
        set_version(path, version, new_version)
        print ' %s updated to %s' % (path, new_version)


def usage():
    print """
Usage:
    unique-addon --print directory
    unique-addon --fix directory addon-id
"""


if __name__ == '__main__':
    try:
        if sys.argv[1] == '--print':
            print_addons(find_addons(sys.argv[2]))
        elif sys.argv[1] == '--fix':
            fix_addons(find_addons(sys.argv[2]), sys.argv[3])
        else:
            usage()
    except IndexError:
        usage()
        raise
