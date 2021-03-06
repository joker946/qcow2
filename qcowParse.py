#!/usr/bin/python
# -*- coding: utf-8 -*- 

#https://github.com/qemu/QEMU/blob/master/docs/specs/qcow2.txt
#http://forge.univention.org/bugzilla/attachment.cgi?id=3426
#https://docs.python.org/2.7/library/struct.html#format-strings
#https://docs.python.org/2/library/json.html

import struct
import sys
import os
import argparse #for parsing of argumenets
import json 
from collections import OrderedDict  #for sorting keys in dictionary

def createParser ():
	parser = argparse.ArgumentParser()
	parser.add_argument ('-d', '--directory', default = 'img')
	parser.add_argument ('-f', '--file', default = 'test.json')

	return parser


#f = open ('img/Fedora-x86_64-19-20140407-sda.qcow2', 'rb')
cirpath = 'img/cir.img'
fedpath = 'img/fed.qcow2'
diskpath = 'img/disk.img'
sspath = 'img/ss.img'


parser = createParser()
namespace = parser.parse_args(sys.argv[1:])

currentpath = format(namespace.directory)

def parseDirs(sSrc, iDirs=0, iFiles=0, filesData = []):
	if (os.path.exists(sSrc)):
		for file in os.listdir(sSrc):
			file_wp= os.path.join(sSrc,file) #full path to file (with dir)
			if os.path.isdir(file_wp):
				iDirs+=1
				#sys.stdout.write('\nFolder: ' + file_wp)
				filesData, iDirs, iFiles = parseDirs(file_wp,iDirs,iFiles,filesData)
			else:
				file_o = open (file_wp, 'rb')
				iFiles += 1
				#sys.stdout.write ("\nFile: " + file_wp)
				if (getInfo (file_o, 0, 3, '3s') == 'QFI'):
					#sys.stdout.write(' - QFI-file!')
					dictionaryOfFileData = getFileDict(file_o)
					filesData.append(dictionaryOfFileData)
				file_o.close()
		return filesData
	else:
		sys.stderr.write("Wrong path typed\n")
		return None


def getInfo (file, begin, read, paramOfUnpack):
	file.seek(begin)
	info_ = file.read(read)
	info = struct.unpack(paramOfUnpack, info_)
	return 	str(info[0])

def getBFName (file, backing_file_offset_start, backing_file_size):
	if (int(backing_file_offset_start)==0):
		return -1 #if backing missed
	else:
		intBFOffset = int (backing_file_offset_start)
		intBFSize = int (backing_file_size) 

		file.seek(intBFOffset)
		info_ = file.read(intBFSize) #read all backing file bytes
		info = struct.unpack(str(intBFSize)+'s', info_)
		return str(info[0])

def getSnapshot(file, ss_offset):

	file.seek(int(ss_offset)+12)#length of id
	len_id_ = file.read(2)
	len_id = struct.unpack('>H', len_id_)

	file.seek(int(ss_offset)+14)#length of name
	len_name_ = file.read(2)
	len_name = struct.unpack('>H', len_name_)

	file.seek(int(ss_offset)+32)# size of ss
	ss_size_ = file.read(4)
	ss_size = struct.unpack('>I', ss_size_)

	file.seek(int(ss_offset)+36)#size of extra data
	ex_data_size_ = file.read(4)
	ex_data_size = struct.unpack('>I', ex_data_size_)

	file.seek(int(int(ss_offset)+40+int(ex_data_size[0])))#offset to id position
	ss_id_ = file.read(int(len_id[0]))
	ss_id = struct.unpack('c', ss_id_)

	file.seek(int(int(ss_offset)+40+int(ex_data_size[0])+len_id[0]))#offset to name position
	ss_name_ = file.read(int(len_name[0]))
	ss_name  = struct.unpack(str(len_name[0])+'s', ss_name_)

	currentlength = int(int(ss_offset)+40+int(ex_data_size[0])+len_id[0]+len_name[0])#offset to padding to round up
	while (currentlength%8!=0):
		currentlength+=1

	ssobj = {'id': ss_id[0], 'name':ss_name[0], 'virtual_size':ss_size[0]}


	return (ssobj, currentlength) #sorted snapshot info

def getFileDict(file):

	qcowDict = {} #create dictionary of file info

	nb_ss = int(getInfo(file, 60, 4, '>I')) #number of snapshots
	ss_offset = getInfo(file, 64, 8, '>Q')	#snapshots offset

	filename = str(os.path.abspath(file.name))
	size = str(os.stat(file.name).st_size)
	virtual_size = getInfo (file, 24, 8, '>Q')
	backing_file = getBFName(file, getInfo(file, 8, 8, '>Q'), getInfo(file, 16, 4, '>I'))

	qcowDict ['filename'] = filename
	qcowDict ['size'] = size
	qcowDict ['virtual_size'] = virtual_size

	if (backing_file != -1):
		qcowDict ['backing_file'] = backing_file

	if (nb_ss != 0): #if there are some snapshots in file
		qcowDict ['snapshots'] = [] 
		for i in range (1, nb_ss+1): #go around all snapshots
			snapShotObj, ss_offset = getSnapshot(file, ss_offset)

			keyorder_ss = ["id", "name", "virtual_size"]
			snapShotObj_sorted = OrderedDict(sorted(snapShotObj.items(), key = lambda i:keyorder_ss.index(i[0]))) 

			qcowDict['snapshots'].append(snapShotObj_sorted)

	keyorder_file = ["filename", "size", "virtual_size", "backing_file", "snapshots"]
	qcowDict = OrderedDict(sorted(qcowDict.items(), key = lambda i:keyorder_file.index(i[0])))

	return qcowDict
	
def Compare(new_data):
	#load json
	if (new_data==None):
		return
	try:
		json_data = open(namespace.file)
	except IOError, e:
		sys.stderr.write("There is not any file with name %s \n"%(namespace.file))
	else:
		try:
			data = json.load(json_data)
		except ValueError, e:
			sys.stderr.write("%s may be corrupted \n"%(namespace.file))
		else:
		#if new file was added
			isnewfile = True
			nb_newfiles = 0
			newfiles = []
			for i in range(0, len(new_data)):
				for j in range (0, len(data)):
					if (new_data[i]['filename'] == data[j]['filename']):
						isnewfile = False
				if (isnewfile == True):
					nb_newfiles += 1
					newfiles.append(new_data[i])
				isnewfile = True
			if (len(newfiles)!=0):
				sys.stdout.write("%s new file(s) was added\n"%(str(len(newfiles))))
			for i in range(0, len(newfiles)):
				sys.stdout.write(json.dumps(newfiles[i],indent = 2)+"\n")
			#if file was deleted
			isdelfile = True
			nb_delfiles = 0
			delfiles = []
			for i in range(0, len(data)):
				for j in range (0, len(new_data)):
					if (data[i]['filename'] == new_data[j]['filename']):
						isdelfile = False
				if (isdelfile == True):
					nb_delfiles +=1
					delfiles.append(data[i])
				isdelfile = True
			if (len(delfiles)!=0):
				sys.stdout.write("%s file(s) was deleted\n"%(str(len(delfiles))))
			for i in range(0, len(delfiles)):
				sys.stdout.write(json.dumps(delfiles[i], indent = 2)+"\n")
			#if snapshot was added
			isnewsp = True
			nb_newsp = 0
			newsps = []
			for i in range(0, len(new_data)):
				for key in new_data[i]:
					for j in range(0, len(data)):
						if (key=='snapshots'):
							if (new_data[i]['filename']==data[j]['filename']):
								for a in range(0, len(new_data[i]['snapshots'])):
									for b in range(0, len(data[j]['snapshots'])):
										if (new_data[i]['snapshots'][a]['name']==data[j]['snapshots'][b]['name']):
											isnewsp = False
									if (isnewsp == True):
										nb_newsp+=1
										newsps.append(new_data[i]['snapshots'][a])
									isnewsp = True
			if (len(newsps)!=0):
				sys.stdout.write("%s snapshot's were added"%(str(len(newsps))))
			for i in range(0, len(newsps)):
				sys.stdout.write(json.dumps(newsps[i], indent = 2)+"\n")
			#if snapshot was deleted
			isdelsp = True
			nb_delsp = 0
			delsps = []
			for i in range(0, len(data)):
				for key in data[i]:
					for j in range(0, len(new_data)):
						if (key=='snapshots'):
							if (new_data[j]['filename']==data[i]['filename']):
								for a in range(0, len(data[i]['snapshots'])):
									for b in range(0, len(new_data[j]['snapshots'])):
										if (new_data[j]['snapshots'][b]['name']==data[i]['snapshots'][a]['name']):
											isdelsp = False
									if (isdelsp == True):
										nb_delsp+=1
										delsps.append(data[i]['snapshots'][a])
									isdelsp = True
			if (len(delsps)!=0):
				sys.stdout.write("%s snapshot's were deleted"%(str(len(delsps))))
			for i in range(0, len(delsps)):
				sys.stdout.write(json.dumps(delsps[i], indent = 2)+"\n")

			for x in range(0, len(data)):
				for key in data[x]:
					for i in range(0, len(new_data)):
						if (data[x]['filename']==new_data[i]['filename']):
							if (data[x][key]!=new_data[i][key] and key!='snapshots'):
								er_obj = "In file: %s changed %s (Old Value: %s) (New Value: %s)"%(str(new_data[i]['filename']), 
									str(key), str(data[x][key]), str(new_data[i][key]))
								sys.stdout.write(er_obj+"\n")
							if (key=='snapshots'):
								for a in range(0, len(data[x]['snapshots'])):
									for skey in data[x]['snapshots'][a]:
										for b in range(0, len(new_data[i]['snapshots'])):
											if (data[x][key][a]['id']==new_data[i][key][b]['id']):
												if (data[x]['snapshots'][a][skey]!=new_data[i]['snapshots'][b][skey]):
													er_obj = "In file: %s changed snapshot's %s (Old Value: %s)(New Value: %s)"%(str(new_data[i]['filename']),
													 str(skey), str(data[x][key][a][skey]), str(new_data[i][key][b][skey]))
													sys.stdout.write(er_obj+"\n")

						
		finally:
			json_data.close()
files = parseDirs(currentpath) #array of files in dict-format
Compare(files)