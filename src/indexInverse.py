#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'NHS'

import sys
import re
import struct
import time
from os import listdir, makedirs, remove
from os.path import isfile, join, splitext, exists
from collections import defaultdict
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
from blist import sorteddict

porter_stemmer=PorterStemmer()

class IndexInverse:
    def __init__(self):
        self.index = defaultdict(lambda:defaultdict())#index inversé

    #Récuperer la liste de mots vides en anglais
    def getStopwords(self):
        stop_words=stopwords.words('english')
        self.stopwords=dict.fromkeys(stop_words)

    #Récuperer les vocabulaires
    def getTerms(self, doc):
        doc=doc.lower()
        doc=re.sub(r"[^a-z0-9 ]",' ',doc) #remplacer les caractères non-alphabetiques par espace
        doc=[x for x in doc.split() if x not in self.stopwords]  #eliminer les mots vides
        doc=[porter_stemmer.stem(word) for word in doc] #Récuperer les termes
        return doc

    #Grouper tous les paragraphes de chaque doc
    def getDoc(self):
        doc=[]
        #Lire le fichier doc par doc
        for line in self.file_data:
            doc.append(line)
            if line=='</DOC>\n':
                break
        #Construire le contenu de doc
        curr_doc = ''.join(doc)
        doc_id=re.search(r"<DOCID>(.*?)</DOCID>", curr_doc, re.DOTALL)
        listP=re.finditer(r"<P>(.*?)</P>", curr_doc, re.DOTALL)
        doc_text = {}
        pos_p = 1
        for p in listP:
            p_content = p.group(1)
            doc_text[pos_p]= p_content
            pos_p += 1
        doc_dict = {}
        #Vérifie si le docid existe et le contenu de doc n'est pas vide
        if doc_id is not None and doc_text:
            doc_dict['doc_id']= doc_id.group(1)
            doc_dict['content']= doc_text
        return doc_dict

    #écire les petits fichiers index quand la taille de l'index dépasse 1mo
    def writeBinaryFileIndex(self,index_file):
        file_index = open(self.indexFolder+index_file, 'wb')
        file_term = open(self.termFolder+index_file+'.txt','w')
        inverse_index = sorteddict(self.index)
        self.index.clear()
        pos_term = 0
        for elem in inverse_index.items():
            term = elem[0]
            nb_doc = 0
            docs_list = sorteddict(elem[1])
            for doc in docs_list.items():
                nb_doc += 1
                doc_id = doc[0]
                nb_occur = doc[1]
                file_index.write(struct.pack('ii',doc_id,nb_occur))
            file_term.write(term+"|"+str(nb_doc)+"|"+str(pos_term)+"\n")
            pos_term += nb_doc
        file_index.close()
        file_term.close()

    def getParams(self,param):
        self.docsFolder=param[2] #répertoire contient les fichiers docs (latimes)
        self.indexFolder=param[3] #répertoire à écrire les fichiers indexs
        self.mapFile = param[4] #fichier à écrire les correspondances des nouveaux docids
        self.termFolder = self.indexFolder+'term/' #répertoire à écrire les fichiers de vocabulaires (taille de postingslist et offset dans les fichiers indexs)
        if not exists(self.indexFolder):
            makedirs(self.indexFolder)
        if not exists(self.termFolder):
            makedirs(self.termFolder)

    def createBinaryIndex(self,param):
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
            with open(docs_path+file,'r') as f_read:
                self.file_data = f_read
                doc_dict=self.getDoc()
                while doc_dict != {}:
                    doc_content = doc_dict['content']
                    doc_text = ''
                    doc_id += 1
                    for p_content in doc_content.values():
                        doc_text += p_content
                    docID = doc_dict['doc_id'].strip()
                    print >> mapFile_write, str(doc_id) + ":" + file_name + "-" + docID
                    terms = self.getTerms(doc_text)
                    #construire index pour le doc courant
                    for term in terms:
                    #ajouter index du document courant à l'index global
                        try:
                            #incrémenter le nombre d'occurences
                            self.index[term][doc_id] += 1
                        except KeyError:
                            #initialiser le nombre d'occurences pour le terme "term" dans le doc "doc_id"
                            self.index[term][doc_id] = 1
                        #Verifier si la taille de l'index dépasse 1mo
                        if sys.getsizeof(self.index) > 1000000:
                            nb_index_file += 1
                            index_file = str(nb_index_file)
                            self.writeBinaryFileIndex(index_file)
                    doc_dict = self.getDoc()
        if self.index:
            nb_index_file += 1
            index_file = str(nb_index_file)
            self.writeBinaryFileIndex(index_file)
        self.mergeBinaryIndex()

#mergeIndex Blocked sort-based indexing
    def mergeBinaryIndex(self):
        #le répertoire contient les fichiers indexs
        index_folder = self.indexFolder
        #le répertoire contient les fichiers de vocabulaires (la taille de postingslist et l'offset
        term_folder = self.termFolder
        #Nom du fichier index global
        index_file = index_folder+"index"
        #Nom du fichier de vocabulaires global
        term_file = term_folder+"term.txt"
        term_files = [f for f in listdir(term_folder) if isfile(join(term_folder,f)) and splitext(f)[0].isdigit()]
        term_files = sorted(term_files,key = lambda item:int(splitext(item)[0]))
        list_term_f = []
        open(index_file, 'wb').close()
        open(term_file, 'w').close()
        sorted_term_dict = sorteddict(defaultdict())
        pos_term_f = 0
        for term_f in term_files:
            pos_last_line = 0
            list_term_f.append([term_f,pos_last_line])
            with open(term_folder+term_f,"r") as f_term:
                with open(index_folder+splitext(term_f)[0],"rb") as f_index:
                    while True:
                        term_line = self.getTermLine(f_term, f_index, list_term_f[pos_term_f][1])
                        if not term_line:
                            break
                        pos_last_line = f_term.tell()
                        list_term_f[pos_term_f][1] = pos_last_line
                        term = term_line[0]
                        nb_doc = term_line[1]
                        posting_list = term_line[2]
                        try:
                            sorted_term_dict[term][1][pos_term_f] = (nb_doc,posting_list)
                        except KeyError:
                            sorted_term_dict[term] = [pos_term_f,sorteddict({pos_term_f:(nb_doc, posting_list)})]
                            break
            pos_term_f += 1
        pos_postinglist = 0
        while sorted_term_dict:
            term_elem = sorted_term_dict.items()[0]
            term = term_elem[0]
            pos_term_f = term_elem[1][0]
            posting_list_arr = term_elem[1][1]
            nb_doc = 0
            posting_list_bytes = ""
            for posting_list in posting_list_arr.items():
                nb_doc += posting_list[1][0]
                posting_list_bytes += posting_list[1][1]
            with open(term_folder+"term.txt", 'a') as f_term_write:
                print>>f_term_write,term+"|"+str(nb_doc)+"|"+str(pos_postinglist)
            with open(index_file, 'a') as f_index_write:
                f_index_write.write(posting_list_bytes)
            pos_postinglist += nb_doc
            term_f = list_term_f[pos_term_f][0]
            del sorted_term_dict[term]
            with open(term_folder+term_f,"r") as f_term:
                with open(index_folder+splitext(term_f)[0],"rb") as f_index:
                   while True:
                        term_line = self.getTermLine(f_term, f_index, list_term_f[pos_term_f][1])
                        if not term_line:
                            break
                        pos_last_line = f_term.tell()
                        list_term_f[pos_term_f][1] = pos_last_line
                        term = term_line[0]
                        nb_doc = term_line[1]
                        posting_list = term_line[2]
                        try:
                            #ajouter un element du postingslist du terme
                            sorted_term_dict[term][1][pos_term_f] = (nb_doc,posting_list)
                        except KeyError:
                            #initialiser le postingslist pour le terme
                            sorted_term_dict[term] = [pos_term_f,sorteddict({pos_term_f:(nb_doc, posting_list)})]
                            break
        for term_f in term_files:
            term_f_name =splitext(term_f)[0]
            remove(self.termFolder+term_f)
            remove(self.indexFolder+term_f_name)

    #Lire une ligne du fichier de vocabulaire f_term et récupérer le postingslist correspondant dans le f_index
    def getTermLine(self, f_term, f_index, pos_last_line):
        f_term.seek(pos_last_line)
        line = f_term.readline()
        line = line.rstrip()
        if not line:
            return []
        term_arr = line.split("|")
        term = term_arr[0]
        nb_doc = int(term_arr[1])
        pos_postingslist = int(term_arr[2])*8
        f_index.seek(pos_postingslist)
        posting_list = f_index.read(nb_doc*8)
        return [term,nb_doc,posting_list]

def writeTextIndexFromBinaryIndex (b_index_file, term_file, t_index_file):
    open(t_index_file,"w").close()
    with open(term_file,"r") as term_f:
        while True:
            term_line = term_f.readline()
            if not term_line:
                break
            with open(t_index_file,"a") as t_index_f_write:
                term_arr = term_line.rstrip().split("|")
                t_index_f_write.write(term_arr[0]+"|"+term_arr[1])
                with open(b_index_file,"rb") as b_index_f:
                    b_index_f.seek(int(term_arr[2])*8)
                    for i in range(int(term_arr[1])):
                        doc_id = str(struct.unpack("i",b_index_f.read(4))[0])
                        nb_occ = str(struct.unpack("i",b_index_f.read(4))[0])
                        t_index_f_write.write("||" + doc_id + "|" + nb_occ)
                    t_index_f_write.write("\n")

if __name__== "__main__":
    param=sys.argv
    if len(param) == 5:
        if param[1] == 'b_index':
            start_time = time.time()
            index = IndexInverse()
            index.createBinaryIndex(param)
            print "Temps d'execution en secondes: "+ str((time.time() - start_time))
        elif param[1] == 'b_to_t_index':
            writeTextIndexFromBinaryIndex(param[2], param[3], param[4])
        else:
            print "Erreur"
    else:
        print "Erreur"


