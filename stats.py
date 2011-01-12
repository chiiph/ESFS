import stat
import errno
import fuse
from time import time
from subprocess import *
from common.file import File, Directory, Stat
from common.structure import Inode

def print_sep(str, sep = 0):
  print "\t"*sep + str

def stat_block(block, sep = 0):
  print_sep("Size: %d" % block.size, sep)
  print_sep("Key: %s" % block.key, sep)
  print_sep("Image: %s" % block.src, sep)

def stat_block_usage(inode, sep = 0):
  if inode.exists_next_block():
    print_sep("Using blocks:", sep)
  else:
    print_sep("Empty file", sep)

  inode.rewind()
  while inode.exists_next_block():
    block = inode.next_block()
    stat_block(block, sep+1)

def stat_file(inode, sep = 0):
  if inode.is_dir():
    print "ERROR: Not a file"
    return

  print_sep("File Name: %s" % inode.name, sep)
  stat_block(inode, sep)
  stat_block_usage(inode, sep)

def stat_dir(inode, pref, sep = 0):
  if not inode.is_dir():
    print "ERROR: Not a dir"
    return

  print_sep("Dir Name: %s" % inode.name, sep)
  stat_block(inode, sep)
  stat_block_usage(inode, sep)
  print_sep("readdir:", sep)

  dir = Directory(inode, prefix=pref)
  for key in dir.dirs:
    if key == "." or key == "..":
      continue

    if dir.dirs[key].is_dir():
      stat_dir(dir.dirs[key], pref, sep+1)
    else:
      stat_file(dir.dirs[key], sep+1)

if __name__ == '__main__':
  root = "block10.png"
  key = "zOaV0YzkcrwUfQg1Rh_XFpZoiItuP-c4C35RvWWNkh8="
  pref = "common/test_imgs/"

  inode = Inode(root, key, prefix=pref)
  stat_dir(inode, pref)
