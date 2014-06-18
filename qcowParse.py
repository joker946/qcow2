#qcowparse
# -*- coding: utf-8 -*-
#https://github.com/qemu/QEMU/blob/master/docs/specs/qcow2.txt
#http://forge.univention.org/bugzilla/attachment.cgi?id=3426
#https://docs.python.org/2.7/library/struct.html#format-strings
#https://docs.python.org/2/library/json.html

import json
import parsedirs
import parsers
import sys
class DictDiffer(object):
    """
    Calculate the difference between two dictionaries as:
    (1) items added
    (2) items removed
    (3) keys same in both but changed values
    (4) keys same in both and unchanged values
    """
    def __init__(self, current_dict, past_dict):
        self.current_dict, self.past_dict = current_dict, past_dict
        self.set_current, self.set_past = set(current_dict.keys()), set(past_dict.keys())
        self.intersect = self.set_current.intersection(self.set_past)
    def added(self):
        return self.set_current - self.intersect 
    def removed(self):
        return self.set_past - self.intersect 
    def changed(self):
        return set(o for o in self.intersect if self.past_dict[o] != self.current_dict[o])
    def unchanged(self):
        return set(o for o in self.intersect if self.past_dict[o] == self.current_dict[o])



def getobjectnb(filename, f1, f2, attr):
    for i in range(0, len(f1)):
        for j in range(0, len(f2)):
            for key in f1:
                if f1[i][attr] == filename and f2[j][attr] == filename:
                    return (i, j)
    return (-1, -1)
def compare(new_data):
	#load json
    if new_data == None:
        return
    try:
        json_data = open(parsers.NAMESPACE.file)
    except IOError:
        sys.stderr.write("There is not any"\
        "file with name %s \n"%(parsers.NAMESPACE.file))
    else:
        try:
            data = json.load(json_data)
        except ValueError:
            sys.stderr.write("%s may be corrupted \n"%(parsers.NAMESPACE.file))
        else:
		#if new file was added
            isnewfile = True
            nb_newfiles = 0
            newfiles = []
            for i in range(0, len(new_data)):
                for j in range(0, len(data)):
                    if new_data[i]['filename'] == data[j]['filename']:
                        isnewfile = False
                if isnewfile == True:
                    nb_newfiles += 1
                    newfiles.append(new_data[i])
                isnewfile = True
            if len(newfiles) != 0:
                sys.stdout.write("%s new file(s)"\
                " was added\n"%(str(len(newfiles))))
            for i in range(0, len(newfiles)):
                sys.stdout.write(json.dumps(newfiles[i], indent=2)+"\n")
			#if file was deleted
            isdelfile = True
            nb_delfiles = 0
            delfiles = []
            for i in range(0, len(data)):
                for j in range(0, len(new_data)):
                    if data[i]['filename'] == new_data[j]['filename']:
                        isdelfile = False
                if isdelfile == True:
                    nb_delfiles += 1
                    delfiles.append(data[i])
                isdelfile = True
            if len(delfiles) != 0:
                sys.stdout.write("%s file(s)"\
                " was deleted\n"%(str(len(delfiles))))
            for i in range(0, len(delfiles)):
                sys.stdout.write(json.dumps(delfiles[i], indent=2)+"\n")
			#if snapshot was added
            isnewsp = True
            nb_newsp = 0
            newsps = []
            for i in range(0, len(new_data)):
                for key in new_data[i]:
                    for j in range(0, len(data)):
                        if key == 'snapshots':
                            if new_data[i]['filename'] == data[j]['filename']:
                                for _A in range(0, len(new_data[i]['snapshots'])):
                                    for _B in range(0, len(data[j]['snapshots'])):
                                        if new_data[i]['snapshots'][_A]['name'] == data[j]['snapshots'][_B]['name']:
                                            isnewsp = False
                                    if isnewsp == True:
                                        nb_newsp += 1
                                        newsps.append(new_data[i]['snapshots'][_A])
                                    isnewsp = True
            if len(newsps) != 0:
                sys.stdout.write("%s snapshot's were added"%(str(len(newsps))))
            for i in range(0, len(newsps)):
                sys.stdout.write(json.dumps(newsps[i], indent=2)+"\n")
			#if snapshot was deleted
            isdelsp = True
            nb_delsp = 0
            delsps = []
            for i in range(0, len(data)):
                for key in data[i]:
                    for j in range(0, len(new_data)):
                        if key == 'snapshots':
                            if new_data[j]['filename'] == data[i]['filename']:
                                for a in range(0, len(data[i]['snapshots'])):
                                    for b in range(0, len(new_data[j]['snapshots'])):
                                        if new_data[j]['snapshots'][b]['name'] == data[i]['snapshots'][a]['name']:
                                            isdelsp = False
                                    if isdelsp == True:
                                        nb_delsp += 1
                                        delsps.append(data[i]['snapshots'][a])
                                    isdelsp = True
            if len(delsps) != 0:
                sys.stdout.write("%s snapshot's were deleted"%(str(len(delsps))))
            for i in range(0, len(delsps)):
                sys.stdout.write(json.dumps(delsps[i], indent=2)+"\n")
            if len(new_data) > len(data):
                maxlen = len(new_data)
                objofmaxlen = new_data
                objofminlen = data
            else:
                maxlen = len(data)
                objofmaxlen = data
                objofminlen = new_data
            for x in range(0, maxlen):
                i, j = getobjectnb(objofmaxlen[x]['filename'],\
                new_data, data, 'filename')
                if i == -1 and j == -1:
                    continue
                ob = DictDiffer(new_data[i],data[j])
                sys.stdout.write("\nFile: %s \n"%(objofmaxlen[x]['filename']))
                sys.stdout.write("Added: \n")
                for n in ob.added():
                    sys.stdout.write("attr:{0}\n"\
                    .format(n))
                sys.stdout.write("Removed: \n")
                for n in ob.removed():
                    sys.stdout.write("attr:{0}\n"\
                    .format(n))
                sys.stdout.write("Changed: \n")
                for n in ob.changed():
                    if n!= 'snapshots':
                        sys.stdout.write("attr:{0} new:{1} old:{2} \n"\
                            .format(n, new_data[i][n], data[j][n]))
                    else:
                        if len(new_data[i]['snapshots']) > len(data[j]['snapshots']):
                            ss_maxnbob = new_data[i]['snapshots']
                        else:
                            ss_maxnbob = data[j]['snapshots']
                        sys.stdout.write("Snapshot:\n")
                        for y in range(0, len(ss_maxnbob)):
                            a, b = getobjectnb(objofmaxlen[x][n][y]['id'],\
                            new_data[i][n], data[j][n], 'id')
                            if a == -1 and b == -1:
                                continue
                            ss_ob = DictDiffer(new_data[i][n][a],\
                            data[j][n][b])
                            
                            for h in ss_ob.added():
                                sys.stdout.write("id:'{0}' Added attr:{1}\n"\
                                .format(new_data[i][n][a]['id'], h))
                            for h in ss_ob.removed():
                                sys.stdout.write("id:'{0}' Removed attr:{1}\n"\
                                .format(new_data[i][n][a]['id'], h))
                            for h in ss_ob.changed():
                                sys.stdout.write("id:'{0}' Changed attr:{1}"\
                                " new:{2} old:{3}\n".format(\
                                data[i][n][a]['id'], h,\
                                new_data[i][n][a][h], data[j][n][b][h]))
        finally:
            json_data.close()
FILES = parsedirs.parsedirs(parsers.CURRENTPATH) #array of files in dict-format
#print FILES
compare(FILES)
