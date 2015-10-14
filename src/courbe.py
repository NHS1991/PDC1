#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'NHS'
import sys
import matplotlib.pyplot as pyplot
import math
from os import listdir
from os.path import isfile, join, splitext
import operator
import numpy as np

def getKey(item):
    return item[2]

if __name__ == '__main__':
    if len(sys.argv)==6:
        f_read = open(sys.argv[1],"r")
        f_write_freq = open(sys.argv[2],"w")
        f_write_tfidf = open(sys.argv[3],"w")
        doc_tfidf = sys.argv[4]
        s = float(sys.argv[5])
        list_fr = []
        list_fr_sort = []
        list_tfidf_sort = []
        docs_path = "../../latimes/"
        files = [f for f in listdir(docs_path) if isfile(join(docs_path,f)) and splitext(f)[1]=='' and 'la' in splitext(f)[0]]
        nb_files = len(files)
        for line in f_read:
            line_arr = line.split("||")
            nb_doc = len(line_arr) - 2
            freq = int(line_arr[1])
            term = line_arr[0]
            i =2
            freq_in_doctfidf = 0
            while i<len(line_arr):
                line_arr_arr = line_arr[i].split("|")
                if line_arr_arr[0] == doc_tfidf:
                    freq_in_doctfidf = int(line_arr_arr[1])
                    break
                i +=1
            idf_word = math.log10(nb_files/nb_doc)
            tfidf_word = freq_in_doctfidf* idf_word
            list_fr_sort.append([term,nb_doc,freq])
            list_tfidf_sort.append([term,nb_doc,tfidf_word,freq_in_doctfidf,freq])
        list_fr_sort = sorted(list_fr_sort,key=getKey,reverse=True)
        list_tfidf_sort = sorted(list_tfidf_sort,key=getKey,reverse=True)
        pos = 0
        list_fr_zipf = []
        sum = 0
        for i in range(1,len(list_fr_sort)):
            sum += 1/math.pow(i,s)
        for word in list_fr_sort:
            list_fr.append(word[2])
            f_write_freq.write(word[0]+"|"+str(word[1])+"|"+str(word[2])+"\n")
            pos +=1
            list_fr_zipf.append((1/pow(pos,s))/sum)
        f_write_freq.close()
        list_tfidf = []
        for word in list_tfidf_sort:
            f_write_tfidf.write(word[0]+"|"+str(word[1])+"|"+str(word[4])+"|"+str(word[3])+"|"+str(word[2])+"\n")
            list_tfidf.append(word[2])
        f_write_tfidf.close()
        pyplot.figure(1)
        pyplot.subplot(3,1,1)
        pyplot.subplots_adjust(hspace = 1)
        pyplot.plot(list_fr)#list_rang,list_fr)
        pyplot.title("Courbe de la frequence en fonction du rang")
        pyplot.subplot(3,1,2)
        pyplot.plot(list_fr_zipf)
        pyplot.title("Loi de Zipf")
        pyplot.subplot(3,1,3)
        pyplot.plot(list_tfidf)
        pyplot.title("Term frequency-Inverse document frequency")
        pyplot.savefig("frequency.png")
        f_read.close()
    else:
        print('Erreur!')