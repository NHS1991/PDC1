#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'NHS'

import sys
import re
import struct
from os import listdir, makedirs
from os.path import isfile, join, splitext, exists
from collections import defaultdict
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer

porter_stemmer=PorterStemmer()

class IndexInverse:
    def __init__(self):
        self.index = defaultdict(lambda: defaultdict())#index inversé

    def getStopwords(self):
        stop_words=stopwords.words('english')
        self.stopwords=dict.fromkeys(stop_words)


    def getTerms(self, doc):
        doc=doc.lower()
        doc=re.sub(r"[^a-z0-9 ]",' ',doc) #remplacer les caractères non-alphabetiques par espace
        doc=[x for x in doc.split() if x not in self.stopwords]  #eliminer les mots vides
        doc=[porter_stemmer.stem(word) for word in doc] #Récuperer les termes
        return doc


    def getDoc(self):
        doc=[]
        for line in self.file_data:
            doc.append(line)
            if line=='</DOC>\n':
                break
        curr_doc=''.join(doc)
        doc_id=re.search(r"<DOCID>(.*?)</DOCID>", curr_doc, re.DOTALL)
        doc_no=re.search(r"<DOCNO>(.*?)</DOCNO>", curr_doc, re.DOTALL)
        listP=re.finditer(r"<P>(.*?)</P>", curr_doc, re.DOTALL)
        doc_text = {}
        pos_p = 1
        for p in listP:
            p_content = p.group(1)
            doc_text[pos_p]=p_content
            pos_p += 1

        if doc_id is None or not doc_text:
            return {}
        doc_dict = {}
        doc_dict['doc_id']=doc_id.group(1)
        doc_dict['doc_no']=doc_no.group(1)
        doc_dict['content']=doc_text

        return doc_dict


    def writeFileIndex(self,index_file):
        file_write=open(self.indexFolder+index_file, 'w')
        inverse_index = sorted(self.index.items(), key=lambda item: item[0])
        self.index.clear()
        for elem in inverse_index:
            term = elem[0]
            postinglist=[]
            docs_list = sorted(elem[1].items(),key=lambda item:item[0])
            for doc in docs_list:
                doc_id = doc[0]
                nb_occur = doc[1]
                postinglist.append(str(doc_id)+'|'+str(nb_occur))
            print >> file_write, term+'|'+str(len(postinglist))+'||'+'||'.join(postinglist)
        file_write.close()
        print (str(sys.getsizeof(self.index))+"\n")

    def getParams(self,param):
        self.docsFolder=param[1] #répertoire contient les fichiers docs (latimes)
        self.indexFolder=param[2] #répertoire à écrire les fichiers indexes
        self.mapFile = param[3] #fichier à écrire les correspondances des nouveaux docids
        if not exists(self.indexFolder):
            makedirs(self.indexFolder)


    def createIndex(self,param):
        self.getParams(param)
        self.getStopwords()
        docs_path = self.docsFolder
        files = [f for f in listdir(docs_path) if isfile(join(docs_path,f)) and splitext(f)[1]=='' and 'la' in splitext(f)[0]]
        files = sorted(files)
        nb_index_file = 0
        doc_id =0 #doc id recompté par rapport à l'ordre d'apparaître
        mapFile_write = open(self.mapFile,"w")
        for file in files:
            file_name = splitext(file)[0]
            print 'En cours '+file_name
            f_read = open(docs_path+file,'r')
            self.file_data = f_read
            doc_dict=self.getDoc()
            while doc_dict != {}:
                doc_content = doc_dict['content']
                doc_text = ''
                doc_id += 1
                for p_content in doc_content.values():
                    doc_text += p_content
                docID = doc_dict['doc_id'].strip()
                print >>mapFile_write, str(doc_id) + ":" + file_name + "-" + docID
                terms = self.getTerms(doc_text)
                #construire indexe pour le document courant
                for term in terms:
                #ajouter indexe du document courant à l'indexe global
                    try:
                        self.index[term][doc_id] +=1 #term_doc_dict[term][doc_id]
                    except:
                        self.index[term][doc_id] =1
                    if sys.getsizeof(self.index) > 1000000:
                        print (str(sys.getsizeof(self.index))+"\n")
                        nb_index_file += 1
                        index_file = str(nb_index_file)+".txt"
                        self.writeFileIndex(index_file)
                        print nb_index_file
                doc_dict = self.getDoc()
            f_read.close()
        if (len(self.index)>0):
            print (str(sys.getsizeof(self.index))+"\n")
            nb_index_file += 1
            index_file = str(nb_index_file)+".txt"
            self.writeFileIndex(index_file)
            print nb_index_file

#mergeIndex Blocked sort-based indexing
def mergeIndex(files_folder, index_file):
    files = [f for f in listdir(files_folder) if isfile(join(files_folder,f)) and splitext(f)[0].isdigit()]
    files = sorted(files, key=lambda item:int(splitext(item)[0]))
    line_dict = defaultdict(list)
    list_fread = []
    open(index_file, 'w').close()
    pos = 0
    for file in files:
        list_fread.append(files_folder+file)
        with open(list_fread[pos],"r") as f_read:
            line = f_read.readline()
            line = line.rstrip()
            pos_firstvline = line.find("|")
            pos_firstdbline = line.find("||",pos_firstvline+1)
            term = line[:pos_firstvline]
            nb_doc = int(line[pos_firstvline+1:pos_firstdbline])
            posting_list = line[pos_firstdbline:]
            last_pos_line = f_read.tell()
            line_dict[pos] = [term,nb_doc,posting_list,last_pos_line]
        pos +=1
    sorted_term = sorted(line_dict.items(),key=lambda item:(item[1][0],item[0]))
    while sorted_term:
        term_write = []
        for term_elem in sorted_term:
            if term_write:
                if term_elem[1][0] == term_write[0]:
                    term_write[1] += term_elem[1][1]
                    term_write[2] += term_elem[1][2]
                    with open(list_fread[term_elem[0]],"r") as f_read:
                        f_read.seek(line_dict[term_elem[0]][-1])
                        next_line = f_read.readline()
                        next_line = next_line.rstrip()
                        if next_line:
                            pos_firstvline = next_line.find("|")
                            pos_firstdbline = next_line.find("||",pos_firstvline+1)
                            term = next_line[:pos_firstvline]
                            nb_doc = int(next_line[pos_firstvline+1:pos_firstdbline])
                            posting_list = next_line[pos_firstdbline:]
                            last_pos_line = f_read.tell()
                            line_dict[term_elem[0]] = [term,nb_doc,posting_list,last_pos_line]
                        else:
                            del line_dict[term_elem[0]]
                else:
                    break
            else:
                term_write = term_elem[1]
                with open (list_fread[term_elem[0]],"r") as f_read:
                    f_read.seek(line_dict[term_elem[0]][-1])
                    next_line = f_read.readline()
                    next_line = next_line.rstrip()
                    if next_line:
                        pos_firstvline = next_line.find("|")
                        pos_firstdbline = next_line.find("||",pos_firstvline+1)
                        term = next_line[:pos_firstvline]
                        nb_doc = int(next_line[pos_firstvline+1:pos_firstdbline])
                        posting_list = next_line[pos_firstdbline:]
                        last_pos_line = f_read.tell()
                        line_dict[term_elem[0]] = [term,nb_doc,posting_list,last_pos_line]
                    else:
                        del line_dict[term_elem[0]]
        with open(index_file, "a") as f_write:
            f_write.write(term_write[0]+"|"+str(term_write[1])+term_write[2]+"\n")
        sorted_term = sorted(line_dict.items(),key=lambda item:(item[1][0],item[0]))
#

if __name__== "__main__":
    param=sys.argv
    if len(param) == 4:
        if param[1] == 'merge':
            mergeIndex(param[2],param[3])
        else:
            index = IndexInverse()
            index.createIndex(param)
    else:
        erreur = str(struct.pack('i',222333))
        print "Erreur" +erreur


