import sys
import os
from common.file import File, Directory, Stat
from common.structure import Inode, Direction
import common.crypt as crypt

def usage():
  print "mkesfs.py <image directory>"

print "ESFS-0.1alpha - This is experimental software"
print "use at your own risk"
print 

if len(sys.argv) != 2:
  print "ERROR: wrong number of arguments"
  usage()
  quit()

dir = sys.argv[-1]

print "Formatting the esfs \"partition\""
print

print "Generating random encryption key..."
print "IMPORTANT: Save the key, if you loose it, you loose *everything*"
print

key = crypt.GenerateKey()
print "Using key for root: ",key[1]

print "Scanning for PNG images in", dir

files = []
dirl = os.listdir(dir)
for name in dirl:
  if name.split(".")[-1] == "png":
    files.append(name)

print "Files used:", files

# 1 for the inode of the root
# 1 for the inode of the .freefile
# 2 for the blocks of the root and .freefile
if len(files) < 4:
  print "ERROR: Not enough images. ABORTING"
  quit()

print "IMPORTANT: Save the root inode location, it's as important as the key"
print "Using", files[0], "as the root inode"
inode_img = files[0]
del files[0]

inode = Inode(inode_img, key[1], new=True, prefix=dir)
inode.set_name("/")
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
inode.type = "1"
inode.save_data()

print "Creating .freefile"

f = Directory(inode, files, prefix=dir)
f.mkfile(".freefile")

freefile = File(f.dirs[".freefile"], files, prefix=dir)
# We need to write this twice...
freefile.write("$".join(files), 0)
freefile.save_data()
f.save_data()
freefile.truncate(len("$".join(files))-1)
freefile.write("$".join(files), 0)
freefile.save_data()
print files

print "Done formatting"
print "To start using your new filesystem execute:"
print "\t python esfs.py <mount point> --prefix=<path to the images files> --root_inode=<path to the root inode file> --key=<key>"
