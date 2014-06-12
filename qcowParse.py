#https://github.com/qemu/QEMU/blob/master/docs/specs/qcow2.txt
#http://forge.univention.org/bugzilla/attachment.cgi?id=3426
#https://docs.python.org/2.7/library/struct.html#format-strings

import struct
import os
#f = open ('img/Fedora-x86_64-19-20140407-sda.qcow2', 'rb')
cirpath = 'img/cir.img'
fedpath = 'img/fed.qcow2'
diskpath = 'img/disk.img'
sspath = 'img/ss.img'
currentpath = sspath
f = open (currentpath, 'rb')

def getInfo (file, begin, read, paramOfUnpack):
	file.seek(begin)
	info_ = file.read(read)
	info = struct.unpack(paramOfUnpack, info_)
	return 	str(info[0])
def getBFName (file, backing_file_offset_start):
	if (int(backing_file_offset_start)==0):
		return 'There is not any backing file found'
	else:
		file.seek(int(backing_file_offset_start))
		i=1
		info_ = file.read(i)# read first char
		while (struct.unpack('c', info_)[0]!='\x00'): #until we have met 00 as hex
			i+=1
			info_ = file.read(1)
		file.seek(int(backing_file_offset_start))
		info_ = file.read(i)
		info = struct.unpack(str(i)+'s', info_)
		return str(info[0])
def getSnapshotId(file, ss_offset, x):
	offset = 64 * x - 8
	file.seek(int(int(ss_offset)+offset))
	value = file.read(1)
	return value
def Print():
	nb_ss = getInfo(f, 60, 4, '>I') #number of snapshots
	ss_offset = getInfo(f, 64, 8, '>Q')
	print 'magic: ' + getInfo (f, 0, 4, '4s')  #magic
	print 'Filename: ' + str(os.path.abspath(currentpath))
	print 'Version: ' + getInfo (f, 4, 4, '>I')  #version
	print 'Backing File path: ' + getBFName(f, getInfo(f, 8, 8, '>Q'))
	print 'Virtual Size (byte): ' + getInfo (f, 24, 8, '>Q')  #vsize
	print 'Size (byte): ' + str(os.stat(currentpath).st_size) #size
	print 'Number of snapshots: ' + nb_ss
	print 'Snapshots offset: ' + getInfo(f, 64, 8, '>Q')
	for x in range(1, int(nb_ss)+1):
		print '-- Snapshot ID: ' + getSnapshotId(f, ss_offset, x)
def Main():
	backing_file_offset_start = getInfo(f, 8,8,'>Q') # trying to get BF offset. It returns '0' if isn't found
	ss_offset = getInfo(f, 64, 8, '>Q')

	Print()
Main()
#print 'size (byte): ' + str(os.stat("img/Fedora-x86_64-19-20140407-sda.qcow2").st_size)

f.close()
