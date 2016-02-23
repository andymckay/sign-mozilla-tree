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


def get_id_version(path):
    print ' Getting id and version.'
    zippy = ZipFile(open(path, 'r'))
    filedata = zippy.read('install.rdf')
    parser = sax.make_parser()
    handler = RDF()
    parser.setContentHandler(handler)
    sax.parseString(filedata, handler)
    return handler.id.strip(), handler.version.strip()


def is_signed(path):
    print ' Checking signed.'
    assert os.path.exists(path)
    assert path.endswith('.xpi')
    zippy = ZipFile(open(path, 'r'))
    if 'META-INF/mozilla.sf' in zippy.namelist():
        return True
    return False


def set_version(path, old_version, new_version):
    print ' Setting version from: %s to %s' % (old_version, new_version)
    tmpfd, tmpname = tempfile.mkstemp()
    os.close(tmpfd)

    with ZipFile(path, 'r') as zin:
        with ZipFile(tmpname, 'w') as zout:
            for item in zin.infolist():
                filedata = zin.read(item.filename)

                if item.filename == 'install.rdf':
                    filedata = filedata.replace(
                        '<em:version>%s</em:version>' % old_version,
                        '<em:version>%s</em:version>' % new_version
                    )

                zout.writestr(item, filedata)

    os.remove(path)
    shutil.copy(tmpname, path)
