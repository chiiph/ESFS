ESFS
====
The encrypted steganography filesystem

This is a kind of FAQ that will answer/explain some of the things that
are behind this. For more details see the concepts file.

If you want to understand what is going on here, please read this whole
document, otherwise, just go to the "How to use?" section.

Content
-------
* What's this?
* License?
* Dependencies?
* Hey, this is really slow!
* How can I know how much space I have with a given set of images?
* What do you aim with this?
* How to use it?
* What's the future of this?
* Found any bugs?


### What's this?

Just like the title says, it's a filesystem. Particularly, it's a FUSE
filesystem that's implemented entirely in Python (for now), and it's a
proof of concept in alpha state, so don't save stuff only within this
filesystem just yet.
A couple of weeks ago, I started reading about and playing with encrypted
filesystems (LUKS + dmcrypt, encfs, etc). I came across an email
(actually, a friend of mine tossed me the link) from the now well-known
Assange, about a Linux kernel module he and other people were working on
that provided different layers of encryption in a filesystem, so you can
say "oh, yes, I have encrypted data in here", but in a deeper layer you'd
have more encrypted data, with another key, and nobody but you would
know about it. And I thought it was a really cool idea. I started looking
for the code, but it was too old to be used with the current kernel.
A couple of days before that, I read about StegFS, a filesystem that uses
steganography to hide your files within your other files. And again, I
thought it was a really cool idea, BUT I didn't like the fact that (and
please correct me if I'm wrong) when you copied a file in StegFS, there's
a chance you'll lose some other file. So, this one is usable, but this
drawback didn't suit me.
I started bouncing ideas with a lot of friends, and then it hit me:
a filesystem, hides its data in images and encrypts this data.
I wanted to build a FUSE filesystem since I first learned about it, so I finally
had an idea to work with. This idea gives you the same
advantages of Assange's kernel module: you have a bunch of images
that seem like regular files, but when you mount the filesystem with certain
parameters BAM! you have lots of files that nobody knew were there.

### License?

All the content in this repo is under GPLv2, even when the files don't say so.
I've also used stepic by Lenny Domnitser, properly credited in the stepic.py 
file.

### Dependencies?

Python, FUSE, pycrypto, fuse-python, PIL.

### Hey, this is really slow!

Well, yes, it's Python cicling through all the pixels of an image, encrypting
its data, and saving files. If you code it with double for's or stuff like 
that, it's going to be slow. But it doesn't matter right now, this is a
prototype, a proof of concept. Our first aim was for it to be a really secure
filesystem, and once we have that assured, we'll focus in its speed.

### How can I know how much space I have with a given set of images?

It's hard to say. Some images are used to stored raw data, other are used to
store metadata. The main difference between this filesystem and what you read
in the books is that there are no "fixed size blocks" in here. Every image
has its own set of pixels, and that affects how storage works.
I recommend using a lot of medium size images (512x512), so you'll be able to 
have both space and speed.

### What do you aim with this?

Nothing specific, I'm doing this for fun and because I think it's a great
idea to have something like this in the world we are living in.
I'm not planning to change the world or anything, and there's probably a
tool just like this one that I haven't found yet, but even then, I like
reinventing the wheel, so no loss there.
Back to the technical stuff, this is intended to be used with small files:
text, code, etc. Not movies or stuff like that, because it'll work, but
it's _really_ slow. For now, I've only copied files inside the "partition"
and then cat or diff them to the originals, and said "wow, it works!",
I'm not using it every day. So it's kind of a locker for now.

### How to use it?

First of all you need to format your esfs partition, but this is no common
partition, but a set of png images. Gather the PNG images you want to use 
(just PNG, nothing else for now) and you put them in a directory.
To format the partition, you'll do the following:

	$ cd <path to the esfs repo>
	$ python mkesfs.py <path to images>

And that's it, but WAIT! have you read _everything_ mkesfs.py said?
There are three important concepts in here: the root inode, the encryption
key, and the prefix.
The root inode: if you don't know what an inode is, don't worry. The root
inode is the "gate" into the filesystem, so for that, mkesfs.py will pick
one picture at random.  It's very important you remember which picture it
was, otherwise you won't be able to access your files.
The encryption key: every image has information hidden, and each file is 
encrypted with its own key. The only key you'll need to know is the one of
the root inode; from there esfs will manage. Yes, it's hard to remember,
so write it on a piece of paper, and don't lose it (cryp.sr is a nice
place to save it).
The prefix: esfs is designed to be pretty flexible when it comes to where
the images are, but this implementation is somehow limited, so your images
will be all in one place. Suppose you have them in /home/user/whatever/images.
if you don't mount the filesystem with a "cd /home/user/whatever/images", you 
won't be able to work with the files.  Why? Because the images themselves 
indicate file contents in a relative fashion, and you need to say to them "ok, 
you are actually in *here*", where *here* is the prefix.
Let's see an example:

	$ cd /home/user/whatever/images
	$ python mkesfs.py .
	<save the important data somewhere!>
	$ cd /home/user/
	$ python esfs.py tmp-mount-point/
	Root inode: whatever/images/someimage.png
	Encryption key: <really long random key>
	Prefix: 
	$ ls tmp-mount-point/
	WRONG! IT DOESN'T WORK
	$ fusermount -u tmp-mount-point

	(let's try again)
	$ cd /home/user/
	$ python esfs.py tmp-mount-point/
	Root inode: someimage.png             <--- Note that there's no whatever/images/?
	Encryption key: <really long random key>
	Prefix: whatever/images/              <--- Here it is! (note the last /, it's very important!)
	$ ls tmp-mount-point/
	YAY! We have a filesystem
	<do your filesystemy stuff here>
	$ fusermount -u tmp-mount-point

### What's the future of this?

I don't know, but there are _a lot_ of things to need to be done. As you saw,
this isn't the most usable piece of code, but it works when you get around
those details. So, the idea is to see how it works for you, and based on that
we'll plan how to improve this. The basic concepts are a lot bigger, and we
plan to get to that, so if you want to read more, see the concepts file.

### Found any bugs?

Please let us know about them, for now, you can contact me directly through
`chiiph at gmail dot com`
