#!/usr/bin/python
# Filename: parsedirs.py
"""Method of parsing directories"""
import file_info
import os
import sys

def parsedirs(ssrc, idirs=0, ifiles=0, filesdata=[]):
    """Parsing directories"""
    if os.path.exists(ssrc):
        for fl_ in os.listdir(ssrc):
            file_wp = os.path.join(ssrc, fl_) #full path to file (with dir)
            if os.path.isdir(file_wp):
                idirs += 1
                filesdata, idirs, ifiles = parsedirs(file_wp,\
                idirs, ifiles, filesdata)
            else:
                file_o = open(file_wp, 'rb')
                ifiles += 1
                if file_info.getinfo(file_o, 0, 3, '3s') == 'QFI':
                    dictionaryoffiledata_ = file_info.getfiledict(file_o)
                    filesdata.append(dictionaryoffiledata_)
                file_o.close()
        return filesdata
    else:
        sys.stderr.write("Wrong path typed\n")
        return None

#End of parsedirs.py
