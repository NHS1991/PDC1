#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'NHS'
import sys
import matplotlib.pyplot as pyplot
import math

if __name__ == '__main__':
    if len(sys.argv) == 5:
        s = float(sys.argv[2]) #Le parametre s de la loi de Zipf
        img_out_path = sys.argv[4] #Le nom du fichier d'image sorti
        with open(sys.argv[3],"w") as f_write_freq: #Créer un fichier sorti avec les termes triés par leur fréquence (nombre d'occurrences), chaque ligne contient le terme, le nombre de document contient ce terme,le nombre d'occurences de ce terme dans tous les fichiers
            #Lire le fichier index texte
            with open(sys.argv[1],"r") as f_read:
                list_fr = []  # liste de fréquence trié par le nombre d'occurences
                list_fr_sort = [] #liste des termes avec leur fréquence et leur nombre de documents d'apparition, trié par le nombre d'occurences de terme
                nb_terms = 0
                for term_line in f_read:
                    nb_terms += 1
                    #Calculer le nombre harmonique
                    term_arr = term_line.split("||")
                    term = term_arr[0].split("|")[0] # le terme
                    nb_doc = int(term_arr[0].split("|")[1]) #le nombre de document contient ce terme
                    freq = 0.0 #le nombre d'occurences de ce terme dans tous les fichiers
                    i = 1
                    while i<len(term_arr):
                        doc_arr = term_arr[i].split("|")
                        freq += int(doc_arr[1])
                        i += 1
                    list_fr_sort.append([term,nb_doc,freq])
                list_fr_sort = sorted(list_fr_sort,key=lambda item:item[2],reverse=True)
                pos = 0
                list_fr_zipf = []
                for term_arr in list_fr_sort:
                    list_fr.append(term_arr[2])
                    #Écrire une ligne avec le terme, le nombre de docs contient le terme et le nombre d'occurrences
                    f_write_freq.write(term_arr[0]+"|"+str(term_arr[1])+"|"+str(term_arr[2])+"\n")
                    pos +=1
                    list_fr_zipf.append(list_fr_sort[0][2]/(math.pow(pos,s)))
                x = [i for i in range(1,nb_terms+1)]
                pyplot.figure(1)
                pyplot.subplots_adjust(hspace = 1)
                c1 = pyplot.subplot(2,1,1)
                c1.set_xlabel('rang')
                c1.set_ylabel(u'fréquence')
                c1.set_title(u"En expérience")
                c1.loglog(x,list_fr) #Trace une courbe avec une échelle log-log
                c2 = pyplot.subplot(2,1,2)
                c2.set_title(u"En théorie")
                c2.set_xlabel('rang')
                c2.set_ylabel(u'fréquence')
                c2.loglog(x,list_fr_zipf) #Loi de Zipf en théorie dont la courbe avec une échelle log-log
                pyplot.savefig(img_out_path)
    else:
        print('Erreur!')