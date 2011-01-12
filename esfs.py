import stat
import errno
import fuse
from time import time
from subprocess import *
from common.file import File, Directory, Stat
from common.structure import Inode

fuse.fuse_python_api = (0, 2)

class ESFS(fuse.Fuse):
  def __init__(self, *args, **kw):
    fuse.Fuse.__init__(self, *args, **kw)

    self.parser.add_option("-c", "--config", type="string", dest="config", help="Use CONFIG as a configuration file", metavar="CONFIG")
#    self.parser.add_option("-k", "--key", type="string", dest="key", help="Use KEY to decrypt the filesystem", metavar="KEY")
#    self.parser.add_option("-p", "--prefix", type="string", dest="prefix", help="Prefix where the image files are", metavar="PREFIX")
#    self.parser.add_option("-i", "--root_inode", type="string", dest="root_inode", help="Root inode location", metavar="ROOT")
#    options, args = self.parser.parse_args()

#    if not options.key or not options.prefix or not options.root_inode:
#      self.parser.print_help()
#      quit()

#    self.root = options.root_inode
#    self.key = options.key
#    self.prefix = options.prefix

    self.root = raw_input("Root inode: ")
    self.key = raw_input("Encryption key: ")
    self.prefix = raw_input("Prefix: ")

    print self.root, self.key, self.prefix

    inode = Inode(self.root, self.key, prefix=self.prefix)

    self.root_dir = Directory(inode, prefix=self.prefix)
    self.freefile = File(self.root_dir.dirs[".freefile"])
    self.free = self.freefile.read(self.freefile.inode.file_size, 0).split("$")
    self.root_dir.free = self.free
    print self.root_dir.free

    self.last_objs = dict()

  def get_obj(self, path):
    """ Given a path it returns the file or directory of the last element """

    if path in self.last_objs.keys():
      return self.last_objs[path]

    pe = path.split('/')[1:]

    step = 0
    current = self.root_dir
    whole_path = ""

    # we cycle through the whole path
    for part in pe:
      in_cache = False
      whole_path += "/"+part
      if whole_path in self.last_objs.keys():
        in_cache = True
        current = self.last_objs[whole_path]
      else:
        # if its a dir, stand on it
        if current.dirs[part].is_dir():
          current = Directory(current.dirs[part], self.free, prefix=self.prefix)
        # if it's not a dir, and it's not the last element, error
        elif part != pe[-1]:
          return -errno.ENOENT
        # else it's a file and the last element of the path
        else:
          current = File(current.dirs[part], self.free, prefix=self.prefix)
        # if it's just a directory in the middle, cycle, and take the new current
        # as the base

      # save all the objects in a temporal cache
      if not in_cache:
        self.last_objs[whole_path] = current

    return current

  def clear_cache(self):
    self.last_objs = dict()

  def getattr(self, path):
    st = Stat()

    if path == '/':
      pass
    else:
      try:
        obj = self.get_obj(path)
        st = obj.getattr()
      except:
        return -errno.ENOENT
    return st

  def readdir(self, path, offset):
    dirs = dict()
    if path == '/':
      dirs = self.root_dir.dirs
    else:
      obj = self.get_obj(path)
      if obj.inode.is_dir():
        dirs = obj.dirs
      else:
        dirs = dict()
        dirs["."] = None
        dirs[".."] = None
    for r in dirs.keys():
      yield fuse.Direntry(r)

  def mknod(self, path, mode, dev):
    elems = path.split('/')
    npath = "/".join(elems[:-1])
    if npath == "":
      self.root_dir.mkfile(elems[-1])
      self.root_dir.save_data()
    else:
      d = self.get_obj(npath)
      d.mkfile(elems[-1])
      d.save_data()
      self.root_dir.save_data()

    self.release("",0)
    return 0

  def unlink(self, path):
    elems = path.split('/')
    npath = "/".join(elems[:-1])
    if npath == "":
      self.root_dir.delete(elems[-1])
      self.root_dir.save_data()
    else:
      d = self.get_obj(npath)
      d.delete(elems[-1])
      d.save_data()

    self.release("",0)
    return 0

  def read(self, path, size, offset):
    f = self.get_obj(path)
    return f.read(size, offset)

  def write(self, path, buf, offset):
    f = self.get_obj(path)
    written = f.write(buf, offset)
    f.save_data()
    return written

  def release(self, path, flags):
    self.freefile.truncate(len("$".join(self.free))-1)
    self.freefile.write("$".join(self.free), 0)
    self.freefile.save_data()

    return 0

  def open(self, path, flags):
    return 0

  def truncate(self, path, size):
    d = self.get_obj(path)
    d.truncate(size)
    return 0

  def utime(self, path, times):
    return 0

  def mkdir(self, path, mode):
    elems = path.split('/')
    npath = "/".join(elems[:-1])
    if npath == "":
      self.root_dir.mkdir(elems[-1])
      self.root_dir.save_data()
    else:
      d = self.get_obj(npath)
      d.mkdir(elems[-1])
      d.save_data()

    self.release("",0)
    return 0

  def rmdir(self, path):
    self.unlink(path)
    return 0

  def rename(self, pathfrom, pathto):
    return 0

  def fsync(self, path, isfsyncfile):
    return 0

def main():
  usage="""
  esfs
  """ + fuse.Fuse.fusage

  server = ESFS(version="%prog " + fuse.__version__,
        usage=usage, dash_s_do='setsingle')
  server.parse(errex=1)
  server.main()

if __name__ == '__main__':
  main()
