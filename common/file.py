import stat
from structure import Inode, Block, Direction
import crypt
from fuse import Stat

class Stat(Stat):
  def __init__(self):
    self.st_mode = stat.S_IFDIR | 0755
    self.st_ino = 0
    self.st_dev = 0
    self.st_nlink = 0
    self.st_uid = 1000
    self.st_gid = 1002
    self.st_size = 4096
    self.st_atime = 0
    self.st_mtime = 0
    self.st_ctime = 0

class File(object):
  def __init__(self, inode, free=[], prefix=""):
    self.inode = inode
    self.free = free
    self.prefix = prefix
    self.count = 0

  def __del__(self):
    self.save_data()

  def release(self):
    self.save_data()

  def save_data(self):
    self.inode.save_data()
    
  def read(self, size, offset):
    """ Reads size from this file beggining in offset """

    # rewind the block iterator 
    # TODO: optimize this
#    self.inode.rewind()

    # find the block where offset is

    found = False
    block = None
    # if the current position is passed the offset
    # look backwards
    if self.count > offset:
#      if self.inode.exists_prev_block() and not found:
#        block = self.inode.prev_block()
#        found = self.count-block.size > offset
      if not (self.inode.current_block() is None):
        block = self.inode.current_block()
        found = self.count <= offset
      while self.inode.exists_prev_block() and not found:
        block = self.inode.prev_block()
        found = (self.count-block.size) <= offset
        if not found:
          self.count -= block.size
    else:
      # else look forward
      if not (self.inode.current_block() is None):
        block = self.inode.current_block()
        found = self.count+block.size > offset
      while self.inode.exists_next_block() and not found:
        block = self.inode.next_block()
        found = self.count+block.size > offset
        if not found:
          self.count += block.size

    # if it doesn't exists return nothing
    if block is None:
      return str()

    # set the new offset
    newfrom = offset
    # set a new size
    newsize = size

    # data is still nothing
    data = ""
    # while we haven't read the whole size of what we want
    # or we haven't reach the end of the block:
    # read and advance
    while newsize > 0 and (newfrom - self.count) < block.size and newfrom < self.inode.file_size:
      data += str(block[newfrom - self.count])
      newfrom += 1
      newsize -= 1

    # if we are trying to read passed the file size, return just what we've read
    if newfrom >= self.inode.file_size:
      return str(data)
    # if we've reach the end of the block and there's more to read
    # read the newsize from newfrom
    if newsize > 0:
      data += self.read(newsize, newfrom)
    
    return str(data)

  def write(self, buf, offset):
    """ Writes bug from this file beggining in offset """

    # rewind the block iterator 
    # TODO: optimize this
    self.inode.rewind()

    # find the block where offset is
    found = False
    count = 0
    block = None
    while self.inode.exists_next_block() and not found:
      block = self.inode.next_block()
      found = count+block.size > offset
      if not found:
        count += block.size

    # if there's no block found to write on, and the idea is to write
    # in a new block
    if not found and (self.inode.file_size - offset) <= 0:
      # if there are no free blocks, return
      if len(self.free) == 0:
        return
      # create a new key for encryption
      byte,key = crypt.GenerateKey()
      type = 1 # local

      newblock = Block(self.free[0], key, new=True, prefix=self.prefix)

      self.inode.add_direction(type, newblock.src, newblock.size, newblock.key)

      del self.free[0]
      block = self.inode.next_block()

    # if it doesn't exists return nothing
    if block is None:
      return

    # set the new offset
    newfrom = offset
    # set a new size
    newsize = len(buf)
    written = 0

    # while we haven't read the whole size of what we want
    # or we haven't reach the end of the block:
    # write and advance
    while newsize > 0 and (newfrom - count) < block.size:
      # as there is still space left on the block, write that byte
      block[newfrom - count] = buf[newfrom - offset]
      newfrom += 1
      newsize -= 1
      written += 1
      if newfrom > self.inode.file_size:
        # if there's still space left on the block, but it's the last block
        # and the declared file size is reached, increase the file size
        self.inode.set_size(self.inode.file_size + 1)

    # if we've reach the end of the block and there's more to write
    # write the newbuf from newfrom
    if newsize > 0:
      written += self.write(buf[newfrom - offset:], newfrom)

    return written

  def getattr(self):
    st = Stat()
    st.st_size = self.inode.file_size
    st.st_mode = stat.S_IFREG | 0666
    return st

  def truncate(self, length):
    self.modified = True
    old = self.inode.file_size
    diff = length - old
    if diff > 0:
      # Write null bytes until the end of the file
      self.write("\0"*diff, old)
    else:
      self.inode.file_size = length

class Directory(File):
  def __init__(self, inode, free=[], prefix=""):
    super(Directory, self).__init__(inode, free, prefix)
    self.dirs = dict()
    self.readdir(0)

  def __del__(self):
    self.save_data()

  def readdir(self, offset):
    self.dirs["."] = None
    self.dirs[".."] = None
    
    data = self.read(self.inode.file_size, 0).split("$")
    for dir in data:
      if len(dir) != 0:
        d = Direction(dir)
        inode = Inode(d.path, d.key, prefix=self.prefix)
        self.dirs[inode.name] = inode

  def mkdir(self, name, offset=0):
    self.mkobj(name, offset, "1")

  def mkfile(self, name):
    self.mkobj(name, 0, "0")

  def mkobj(self, name, offset=0, type="0"):
    if len(self.free) == 0:
      return

    if name in self.dirs.keys():
      return

    print "Generating random key"
    key = crypt.GenerateKey()

    inode_img = self.free[0]
    print "Creating inode with %s" % inode_img
    inode = Inode(inode_img, key[1], new = True, prefix=self.prefix)
    print "Setting new data"
    del self.free[0]

    inode.type = type
    inode.set_name(name)
    inode.add_direction_str(Direction("0|||$"))
    inode.add_direction_str(Direction("0|||$"))
    inode.add_direction_str(Direction("0|||$"))
    inode.add_direction_str(Direction("0|||$"))
    inode.add_direction_str(Direction("0|||$"))
    inode.add_direction_str(Direction("0|||$"))
    inode.add_direction_str(Direction("0|||$"))
    inode.add_direction_str(Direction("0|||$"))
    inode.add_direction_str(Direction("0|||$"))
    inode.add_direction_str(Direction("0|||$"))
    inode.add_direction_str(Direction("0|||$"))
    inode.add_direction_str(Direction("0|||$"))
    inode.file_size = 0

    print "Saving new inode data"
    inode.save_data()

    self.dirs[name] = inode
    self.inode.modified = True

  def is_empty(self):
    return len(self.dirs)

  def delete(self, name):
    obj = self.dirs[name]
    if obj.is_dir() and not Directory(obj, obj.key, self.prefix).is_empty():
      return

    self.free.append(obj.src)
    obj.rewind()
    while obj.exists_next_block():
      self.free.append(obj.next_block().src)

    # Force modified
    self.inode.modified = True
    del self.dirs[name]
    self.save_data()
    self.readdir(0)

  def getattr(self):
    st = Stat()
    return st

  def save_data(self):
    if not self.inode.modified:
      return
    data = ""
    for k in self.dirs:
      if self.dirs[k] is None:
        continue
      # TODO: implement, they are all local
      data += "1|" + self.dirs[k].src + "|" + str(self.dirs[k].size) + "|" + self.dirs[k].key + "$"

    if len(data) < self.inode.file_size:
      self.truncate(len(data))
    self.write(data,0)
    self.inode.save_data()
