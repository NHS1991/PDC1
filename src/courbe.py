#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'NHS'
import sys
import matplotlib.pyplot as pyplot
import math

if __name__ == '__main__':
    if len(sys.argv) == 5:
        s = float(sys.argv[2])
        img_out_path = sys.argv[4]
        with open(sys.argv[3],"w") as f_write_freq:
            with open(sys.argv[1],"r") as f_read:
                list_fr = []  # liste de fréquence trié par le nombre d'occurences
                list_fr_sort = [] #liste des termes avec leur fréquence et leur nombre de documents d'apparition, trié par le nombre d'occurences de terme
                nb_terms = 0
                harmonic_number = 0
                for term_line in f_read:
                    nb_terms += 1
                    harmonic_number += 1/(pow(nb_terms,s))
                    term_arr = term_line.split("||")
                    term = term_arr[0].split("|")[0] # le terme
                    nb_doc = int(term_arr[0].split("|")[1]) #le nombre de document contient ce terme
                    freq = 0 #le nombre d'occurences de ce terme dans tous les fichiers
                    i = 1
                    freq_in_doctfidf=0
                    while i<len(term_arr):
                        doc_arr = term_arr[i].split("|")
                        freq += int(doc_arr[1])
                        i += 1
                    list_fr_sort.append([term,nb_doc,freq])
                list_fr_sort = sorted(list_fr_sort,key=lambda item:item[2],reverse=True)
                pos = 0
                list_fr_zipf = []
                for term_arr in list_fr_sort:
                    list_fr.append(math.log(term_arr[2]))
                    f_write_freq.write(term_arr[0]+"|"+str(term_arr[1])+"|"+str(term_arr[2])+"\n")
                    pos +=1
                    list_fr_zipf.append(math.log(list_fr_sort[0][2]/(math.pow(pos,s)*harmonic_number)))
                x = [math.log(pow(i,s)) for i in range(1,nb_terms+1)]
                pyplot.figure(1)
                pyplot.subplot(2,1,1)
                pyplot.subplots_adjust(hspace = 1)
                pyplot.plot(x,list_fr)#list_rang,list_fr)
                pyplot.title("Courbe de la frequence en fonction du rang")
                pyplot.subplot(2,1,2)
                pyplot.plot(x,list_fr_zipf)
                pyplot.title("Loi de Zipf")
                pyplot.savefig(img_out_path)
    else:
        print('Erreur!')