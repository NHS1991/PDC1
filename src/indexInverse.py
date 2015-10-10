#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'NHS'

import sys
import re
import matplotlib.pyplot as pyplot
from os import listdir
from os.path import isfile, join, splitext
from porterStemmer import PorterStemmer
from collections import defaultdict
from nltk.corpus import stopwords

porter_stemmer=PorterStemmer()

class IndexInverse:
    def __init__(self):
        self.index=defaultdict(defaultdict)    #index inversé


    def getStopwords(self):
        stop_words=stopwords.words('english')
        self.stopwords=dict.fromkeys(stop_words)


    def getTerms(self, line):
        line=line.lower()
        line=re.sub(r'[^a-z0-9 ]',' ',line) #remplacer les caractères non-alphabetiques par espace
        line=[x for x in line.split() if x not in self.stopwords]  #eliminer les mots vides
        line=[porter_stemmer.stem(word, 0, len(word)-1) for word in line]
        return line


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


    def writeFileIndex(self):
        f=open(self.indexFile, 'w')
        for term in self.index.iterkeys():
            postinglist=[]
            count = 0
            position_dict = self.index[term]
            for file_name in position_dict.keys():
                list_pos_by_doc_id = []
                for doc_id in position_dict[file_name].keys():
                    positions = position_dict[file_name][doc_id]
                    count += len(positions)
                    list_pos_by_doc_id.append(str(doc_id)+':'+','.join(str(pos) for pos in positions))
                postinglist.append(file_name+'|'+";".join(list_pos_by_doc_id))
            print >> f, term+'||'+str(count)+'||'+'||'.join(postinglist)
        f.close()


    def getParams(self):
        param=sys.argv
        self.docsFolder=param[1]
        self.indexFile=param[2]


    def createIndex(self):
        self.getParams()
        self.getStopwords()
        docs_path = self.docsFolder
        files = [f for f in listdir(docs_path) if isfile(join(docs_path,f)) and splitext(f)[1]=='']
        nb_files = 0
        for file in files:
            # if nb_files<3:
                file_name = splitext(file)[0]
                nb_files += 1
                print 'En cours '+file_name
                f_read = open(docs_path+file,'r')
                self.file_data = f_read
                doc_dict=self.getDoc()
                while doc_dict != {}:
                    doc_content = doc_dict['content']
                    doc_text = ''
                    for p_content in doc_content.values():
                        doc_text += p_content + '\n'
                    doc_id = int(doc_dict['doc_id'])
                    terms = self.getTerms(doc_text)

                    #construire indexe pour le document courant
                    term_doc_dict = {}
                    for position, term in enumerate(terms):
                        try:
                            term_doc_dict[term][file_name][doc_id].append(position)
                        except:
                            try:
                                term_doc_dict[term][file_name][doc_id] = [position]
                            except:
                                try:
                                    term_doc_dict[term][file_name] = {}
                                    term_doc_dict[term][file_name][doc_id] = [position]
                                except:
                                    term_doc_dict[term] = {}
                                    term_doc_dict[term][file_name] = {}
                                    term_doc_dict[term][file_name][doc_id] = [position]

                        #ajouter indexe du document courant à l'indexe global
                    for term_doc, posting_doc in term_doc_dict.iteritems():
                        self.index[term_doc].update(posting_doc)
                    doc_dict = self.getDoc()
                f_read.close()
            # else:
            #     break
        self.writeFileIndex()

    def verifyZipf(self):
        f_read = open(self.indexFile,"r")
        f_write = open("test1.txt","w")
        list_fr = []
        for line in f_read:
            line_arr = line.split("||")
            freq = line_arr[1]
            list_fr.append(freq)
        list_fr.sort(reverse=True)
        for freqe in list_fr:
            f_write.writeln(freqe)
        pyplot.plot(list_fr)
        pyplot.savefig("test.png")
        f_read.close()
        f_write.close()

if __name__== "__main__":
    index = IndexInverse()
    index.createIndex()
    index.verifyZipf()


