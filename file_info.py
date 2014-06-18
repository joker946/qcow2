#!/usr/bin/python
# Filename: file_info.py

import sys
import struct
import os

def getinfo(fl, begin, read, paramofunpack):
    fl.seek(begin)
    info_ = fl.read(read)
    info = struct.unpack(paramofunpack, info_)
    return str(info[0])

def getbfname(file, backing_file_offset_start, backing_file_size):
    if int(backing_file_offset_start) == 0:
        return -1 #if backing missed
    else:
        intBFOffset = int(backing_file_offset_start)
        intBFSize = int(backing_file_size)

        file.seek(intBFOffset)
        info_ = file.read(intBFSize) #read all backing file bytes
        info = struct.unpack(str(intBFSize)+'s', info_)
        return str(info[0])

def getsnapshot(file, ss_offset):
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

    file.seek(int(int(ss_offset)+40+\
    int(ex_data_size[0])+len_id[0]))#offset to name position
    ss_name_ = file.read(int(len_name[0]))
    ss_name = struct.unpack(str(len_name[0])+'s', ss_name_)

    currentlength = int(int(ss_offset)+40\
    +int(ex_data_size[0])+len_id[0]+len_name[0])#offset to padding to round up
    while currentlength%8 != 0:
        currentlength += 1

    ssobj = {'id': ss_id[0], 'name':ss_name[0], 'virtual_size':ss_size[0]}


    return (ssobj, currentlength) #sorted snapshot info

def getfiledict(file):

    qcowDict = {} #create dictionary of file info

    nb_ss = int(getinfo(file, 60, 4, '>I')) #number of snapshots
    ss_offset = getinfo(file, 64, 8, '>Q')	#snapshots offset

    filename = str(os.path.abspath(file.name))
    size = str(os.stat(file.name).st_size)
    virtual_size = getinfo(file, 24, 8, '>Q')
    backing_file = getbfname(file, getinfo(file, 8, 8, '>Q'),\
    getinfo(file, 16, 4, '>I'))

    qcowDict['filename'] = filename
    qcowDict['size'] = size
    qcowDict['virtual_size'] = virtual_size

    if backing_file != -1:
        qcowDict['backing_file'] = backing_file

    if nb_ss != 0: #if there are some snapshots in file
        qcowDict['snapshots'] = []
        for i in range(1, nb_ss+1): #go around all snapshots
            snapShotObj, ss_offset = getsnapshot(file, ss_offset)


            qcowDict['snapshots'].append(snapShotObj)
    return qcowDict

#End of file_info.py