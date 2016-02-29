import os
import shutil
import tempfile

from zipfile import ZipFile
from xml import sax

class RDF(sax.ContentHandler):
    def __init__(self):
        self.id = ''
        self.version = ''
        self.tag = None

    def startElement(self, name, attrs):
        if self.id and self.version:
            return
        self.tag = name

    def characters(self, chars):
        if self.tag == 'em:id':
            self.id += chars
        if self.tag == 'em:version':
            self.version += chars

    def endElement(self, *args, **kw):
        self.tag = None


def is_xpi(path):
    return os.path.isfile(path)


def get_id_version(path):
    print ' Getting id and version.'
    if is_xpi(path):
        zippy = ZipFile(open(path, 'r'))
        filedata = zippy.read('install.rdf')
    else:
        filedata = open(os.path.join(path, 'install.rdf'), 'r').read()

    parser = sax.make_parser()
    handler = RDF()
    parser.setContentHandler(handler)
    sax.parseString(filedata, handler)
    return handler.id.strip(), handler.version.strip()


def is_signed(path):
    print ' Checking signed.'
    assert os.path.exists(path)
    if is_xpi(path):
        zippy = ZipFile(open(path, 'r'))
        if 'META-INF/mozilla.sf' in zippy.namelist():
            return True
    else:
        return 'META-INF' in os.listdir(path)

    return False


def set_version(path, old_version, new_version):
    print ' Setting version from: %s to %s' % (old_version, new_version)
    tmpfd, tmpname = tempfile.mkstemp()
    os.close(tmpfd)

    def replace(data):
        return data.replace(
            '<em:version>%s</em:version>' % old_version,
            '<em:version>%s</em:version>' % new_version
        )

    if is_xpi(path):
        with ZipFile(path, 'r') as zin:
            with ZipFile(tmpname, 'w') as zout:
                for item in zin.infolist():
                    filedata = zin.read(item.filename)

                    if item.filename == 'install.rdf':
                        filedata = replace(filedata)

                    zout.writestr(item, filedata)

        os.remove(path)
        shutil.copy(tmpname, path)

    else:
        filedata = open(os.path.join(path, 'install.rdf'), 'r').read()
        filedata = replace(filedata)
        open(os.path.join(path, 'install.rdf'), 'w').write(filedata)
