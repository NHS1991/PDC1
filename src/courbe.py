#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'NHS'
import sys
import matplotlib.pyplot as pyplot
import math
from os import listdir
from os.path import isfile, join, splitext

def getKey(item):
    return item[2]

if __name__ == '__main__':
    if len(sys.argv)==5:
        f_read = open(sys.argv[1],"r")
        f_write_freq = open(sys.argv[2],"w")
        f_write_tfidf = open(sys.argv[3],"w")
        doc_id_tfidf = sys.argv[4]
        list_fr = []  # liste de fréquence trié par le nombre d'occurences
        list_fr_sort = [] #liste des termes avec leur fréquence et leur nombre de documents d'apparition, trié par le nombre d'occurences de terme
        list_tfidf_sort = []
        docs_path = "../../latimes/"
        files = [f for f in listdir(docs_path) if isfile(join(docs_path,f)) and splitext(f)[1]=='' and 'la' in splitext(f)[0]]
        nb_DOCs = 0 #nombre de l'élément DOC dans tous les fichiers
        for file in files:
            file_read = open(docs_path+file,"r")
            file_data = file_read.read()
            file_read.close()
            nb_DOCs += file_data.count("<DOC>")
        nb_terms = 0
        for term_line in f_read:
            nb_terms += 1
            term_arr = term_line.split("||")
            term = term_arr[0].split("|")[0] # le terme
            nb_doc = int(term_arr[0].split("|")[1]) #le nombre de document contient ce terme
            freq = 0 #le nombre d'occurences de ce terme dans tous les fichiers
            i = 1
            freq_in_doctfidf=0
            while i<len(term_arr):
                doc_arr = term_arr[i].split("|")
                if doc_arr[0] == doc_id_tfidf:
                    freq_in_doctfidf = int(doc_arr[1])
                freq += int(doc_arr[1])
                i += 1
            idf_term = math.log10(nb_DOCs/nb_doc)
            tfidf_term = freq_in_doctfidf * idf_term
            list_fr_sort.append([term,nb_doc,freq])
            list_tfidf_sort.append([term,nb_doc,tfidf_term,freq_in_doctfidf,freq])
        list_fr_sort = sorted(list_fr_sort,key=getKey,reverse=True)
        list_tfidf_sort = sorted(list_tfidf_sort,key=getKey,reverse=True)
        pos = 0
        list_fr_zipf = []
        sum = 0
        for word in list_fr_sort:
            list_fr.append(word[2])
            f_write_freq.write(word[0]+"|"+str(word[1])+"|"+str(word[2])+"\n")
            pos +=1
            list_fr_zipf.append((list_fr_sort[0][2])/pos)
        f_write_freq.close()
        list_tfidf = []
        for word in list_tfidf_sort:
            f_write_tfidf.write(word[0]+"|"+str(word[1])+"|"+str(word[4])+"|"+str(word[3])+"|"+str(word[2])+"\n")
            list_tfidf.append(word[2])
        f_write_tfidf.close()
        x = [math.log(i) for i in range(1,nb_terms+1)]
        pyplot.figure(1)
        pyplot.subplot(3,1,1)
        pyplot.subplots_adjust(hspace = 1)
        pyplot.plot(x,list_fr)#list_rang,list_fr)
        pyplot.title("Courbe de la frequence en fonction du rang")
        pyplot.subplot(3,1,2)
        pyplot.plot(x,list_fr_zipf)
        pyplot.title("Loi de Zipf")
        pyplot.subplot(3,1,3)
        pyplot.plot(x,list_tfidf)
        pyplot.title("Term frequency-Inverse document frequency")
        pyplot.savefig("frequency.png")
        f_read.close()
    else:
        print('Erreur!')