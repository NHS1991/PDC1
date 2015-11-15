#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'NHS'

import sys
import re
import struct
import time
import math
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
from os import listdir, makedirs, remove
from os.path import isfile, join, splitext, exists
from collections import defaultdict
from blist import sorteddict

porter_stemmer = PorterStemmer()

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
        #Lire le fichier ligne par ligne
        for line in self.file_data:
            doc.append(line)
            if line=='</DOC>\n':#faire un break si on rencontre cette ligne (la fin d'un doc)
                break
        #Construire le contenu de doc
        curr_doc = ''.join(doc)
        doc_id=re.search(r"<DOCID>(.*?)</DOCID>", curr_doc, re.DOTALL)
        listP=re.finditer(r"<P>(.*?)</P>", curr_doc, re.DOTALL)
        doc_text = {}
        pos_p = 1
        for p in listP:
            p_content = p.group(1)
            doc_text[pos_p] = p_content
            pos_p += 1
        doc_dict = {}
        #Vérifie si le docid existe et le contenu de doc n'est pas vide
        if doc_id is not None and doc_text:
            doc_dict['doc_id']= doc_id.group(1)
            doc_dict['content']= doc_text
        return doc_dict

    #écire les petits fichiers index quand la taille de l'index dépasse 1mo
    def writeBinaryFileIndex(self,index_file):
        with open(self.indexFolder+index_file, 'wb') as file_index:
            with open(self.termFolder+index_file+'.txt','w') as file_term:
                #Trier l'indexe par terme
                inverse_index = sorteddict(self.index)
                self.index.clear()
                pos_term = 0
                #Lire l'indexe par terme
                for elem in inverse_index.items():
                    term = elem[0]
                    nb_doc = 0
                    #Trier la postingslist par docID
                    docs_list = sorteddict(elem[1])
                    #Lire la postingslist par docID
                    for doc in docs_list.items():
                        nb_doc += 1
                        doc_id = doc[0]
                        nb_occur = doc[1]
                        #Écrire en binaire le docID et le nombre d'occurences
                        file_index.write(struct.pack('ii',doc_id,nb_occur))
                    #Écire une ligne correspondante dans le fichier de vocabulaire avec le terme (vocabulaire), le nombre de doc contenant ce terme et la position débute de sa postingslist dans le fichier binaire
                    file_term.write(term+"|"+str(nb_doc)+"|"+str(pos_term)+"\n")
                    pos_term += nb_doc #La position débute du terme suivant

    def getParams(self,param):
        self.docsFolder=param[2] #répertoire contient les fichiers docs (latimes)
        self.indexFolder=param[3] #répertoire à écrire les fichiers indexes
        self.mapFile = param[4] #fichier à écrire les correspondances des nouveaux docids
        self.termFolder = self.indexFolder+'term/' #répertoire à écrire les fichiers de vocabulaires (taille de postingslist et offset dans les fichiers indexes)
        if not exists(self.indexFolder):
            makedirs(self.indexFolder) #Créer le répertoire contenant les fichiers indexes s'il n'existe pas
        if not exists(self.termFolder):
            makedirs(self.termFolder) #Créer le répertoire contenant les fichiers vocabulaires s'il n'existe pas

    #Créer l'index global
    def createBinaryIndex(self,param):
        self.getParams(param)
        self.getStopwords()
        docs_path = self.docsFolder
        files = [f for f in listdir(docs_path) if isfile(join(docs_path,f)) and splitext(f)[1]=='' and 'la' in splitext(f)[0]]
        files = sorted(files)
        nb_index_file = 0
        doc_id =0 #doc id recompté par rapport à l'ordre d'apparaître
        with open(self.mapFile,"w") as mapFile_write:
            for file in files:
                file_name = splitext(file)[0]
                print 'En cours '+file_name
                with open(docs_path+file,'r') as f_read:
                    self.file_data = f_read
                    #Lire un nouveau doc dans le fichier texte courant
                    doc_dict=self.getDoc()
                    while doc_dict != {}:
                        doc_content = doc_dict['content']
                        doc_text = ''
                        doc_id += 1
                        for p_content in doc_content.values():
                            doc_text += p_content#regrouper le contenu de chaque paragraphe
                        terms = self.getTerms(doc_text) #Récupérer les termes du doc
                        docID = doc_dict['doc_id'].strip()
                        #construire index pour le doc courant
                        for term in terms:
                            try:
                                #incrémenter le nombre d'occurences
                                self.index[term][doc_id] += 1
                            except KeyError:
                                #initialiser le nombre d'occurences pour le terme "term" dans le doc "doc_id"
                                self.index[term][doc_id] = 1
                        norm_vector_doc = 0
                        set_terms = set(terms)
                        #Calculer la norme du vecteur construit par les fréquences de chaque terme dans le doc courant
                        for term_elem in set_terms:
                            norm_vector_doc += math.pow(self.index[term_elem][doc_id],2)
                        print >> mapFile_write, str(doc_id) + ":" + file_name + "|" + docID + "|"+ str(len(terms))+"|"+str(math.sqrt(norm_vector_doc)) #Écrire une ligne dans le fichier contenant la réindexation de docID avec le nombre de terme de ce doc et sa nomre du vecteur construit par les fréquences de chaque terme
                        #Vérifier si la taille de l'index dépasse 1mo et écrire dans le disque un petit fichier indexé binaire et un fichier de vocabulaire correspondant
                        if sys.getsizeof(self.index) > 1000000:
                            nb_index_file += 1
                            index_file = str(nb_index_file)
                            self.writeBinaryFileIndex(index_file)
                        #Lire un nouveau document dans le fichier texte courant
                        doc_dict = self.getDoc()
            #Écrire le dernier fichier indexé binaire au cas ou la taille de l'index ne dépasse pas encore 1mo
            if self.index:
                nb_index_file += 1
                index_file = str(nb_index_file)
                self.writeBinaryFileIndex(index_file)
            #Faire un merge les petits fichiers indexes binaires
            self.mergeBinaryIndex()

#mergeIndex Blocked sort-based indexing
    def mergeBinaryIndex(self):
        #le répertoire contient les fichiers indexes
        index_folder = self.indexFolder
        #le répertoire contient les fichiers de vocabulaires (la taille de postingslist et l'offset
        term_folder = self.termFolder
        #Nom du fichier index global
        index_file = index_folder+"index"
        #Nom du fichier de vocabulaires global
        term_file = term_folder+"term.txt"
        #La liste des petits fichiers de vocabulaires (leur nom sans extension)
        term_files = [f for f in listdir(term_folder) if isfile(join(term_folder,f)) and splitext(f)[0].isdigit()]
        term_files = sorted(term_files,key = lambda item:int(splitext(item)[0])) #
        list_term_f = [] #la liste a les éléments qui sont un couple avec le nom du fichier de vocabulaires et sa position de lecture courante
        #Vider si les fichiers index et vocabulaire existent ou créer les nouveaux sinon
        open(index_file, 'wb').close()
        open(term_file, 'w').close()
        #Un dictionnaire dont la clé est le terme (vocabulaire) et la valeur est un couple de la position du premier fichier de vocabulaire qui contient ce terme et la postingslist est toujour trié par terme
        sorted_term_dict = sorteddict(defaultdict())
        pos_term_f = 0 #la position du fichier de vocabulaires à lire, le premier fichier commence par 0
        for term_f in term_files:
            pos_last_line = 0 #La dernière position de lecture du fichier
            list_term_f.append([term_f,pos_last_line]) #Ajoute un couple avec le nom du fichier (sans extension) et sa dernière position de lecture
            with open(term_folder+term_f,"r") as f_term:
                with open(index_folder+splitext(term_f)[0],"rb") as f_index:
                    while True:
                        term_line = self.getTermLine(f_term, f_index, list_term_f[pos_term_f][1]) #Lire une ligne du fichier vocabulaire et récuperer les informations nécessaires
                        if not term_line:
                            break #Si c'est la fin du fichier de vocabulaires, on fait un break
                        pos_last_line = f_term.tell() #La position de la dernière ligne qu'on lit dans le fichier courant
                        list_term_f[pos_term_f][1] = pos_last_line #Enregistrer cette position dans la liste
                        term = term_line[0] #Le terme
                        nb_doc = term_line[1] #Le nombre de doc contient le terme
                        posting_list = term_line[2] #La postingslist du temre
                        try:
                            sorted_term_dict[term][1][pos_term_f] = (nb_doc,posting_list) #Merger la postingslist si elle est déjà initialisée
                        except KeyError:
                            #Ajouter la position du premier fichier contenant le terme et initialiser la postingslist 
                            sorted_term_dict[term] = [pos_term_f,sorteddict({pos_term_f:(nb_doc, posting_list)})]
                            break #Faire un break pour lire un autre fichier de vocabulaires
            pos_term_f += 1 #incrémenter la position du fichier de vocabulaires à lire
        pos_postinglist = 0
        # Écrire le premier élément du dictionnaire dans le fichier index global et ajoute un nouvel élément si possible (on n'atteint pas encore la fin de tous les fichiers de vocabulaires)
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
                        term_line = self.getTermLine(f_term, f_index, list_term_f[pos_term_f][1]) #Lire une ligne du fichier vocabulaire et récuperer les informations nécessaires
                        if not term_line:
                            break #Si c'est la fin du fichier de vocabulaires, on fait un break
                        pos_last_line = f_term.tell() # lire la position de lecture courante du fichier de vocabulaires
                        list_term_f[pos_term_f][1] = pos_last_line #La position de la dernière ligne qu'on lit dans le fichier courant
                        term = term_line[0] #Le terme
                        nb_doc = term_line[1] #Le nombre de doc contient le terme
                        posting_list = term_line[2] #La postingslist du temre
                        try:
                            #Merger la postingslist si elle est déjà initialisée
                            sorted_term_dict[term][1][pos_term_f] = (nb_doc,posting_list)
                        except KeyError:
                            #Ajouter la position du premier fichier contenant le terme et initialiser la postingslist 
                            sorted_term_dict[term] = [pos_term_f,sorteddict({pos_term_f:(nb_doc, posting_list)})]
                            break #Faire un break pour écrire le premier élément du dictionnaire dans le fichier index
        #Supprimer tous les fichier de vocabulaires et d'indexs intermédiaires (les petits fichiers)
        for term_f in term_files:
            term_f_name =splitext(term_f)[0]
            remove(self.termFolder+term_f)
            remove(self.indexFolder+term_f_name)

    #Lire une ligne du fichier de vocabulaire f_term et récupérer le postingslist correspondant dans le f_index
    def getTermLine(self, f_term, f_index, pos_last_line):
        f_term.seek(pos_last_line)
        line = f_term.readline()
        line = line.rstrip()
        if not line: #La fin du fichier
            return []
        term_arr = line.split("|")
        term = term_arr[0] #Le terme
        nb_doc = int(term_arr[1]) #Le nombre de doc contient le terme
        pos_postingslist = int(term_arr[2])*8
        f_index.seek(pos_postingslist) #Pointer au début de la postinslist du terme dans le fichier pour lire
        posting_list = f_index.read(nb_doc*8) #la postingslist correspond au terme
        return [term,nb_doc,posting_list]

# Convertir l'index binaire en texte
def writeTextIndexFromBinaryIndex (b_index_file, term_file, t_index_file):
    with open(t_index_file,"w") as t_index_f_write:
        with open(b_index_file,"rb") as b_index_f:
            with open(term_file,"r") as term_f:
                for term_line in term_f:
                    term_arr = term_line.rstrip().split("|")
                    term = term_arr[0]
                    nb_docs_containing = term_arr[1]
                    t_index_f_write.write(term+"|"+nb_docs_containing)
                    nb_docs_containing = int(term_arr[1])
                    for i in range(nb_docs_containing):
                        doc_id = struct.unpack("i",b_index_f.read(4))[0]
                        nb_occ = struct.unpack("i",b_index_f.read(4))[0]
                        t_index_f_write.write("||" + str(doc_id) + "|" + str(nb_occ))
                    t_index_f_write.write("\n")

if __name__== "__main__":
    param=sys.argv
    if len(param) == 5:
        # Créer l'index global en binaire
        if param[1] == 'b_index':
            start_time = time.time()
            index = IndexInverse()
            index.createBinaryIndex(param)
            print "Temps d'execution en secondes: " + str((time.time() - start_time))
        # Convertir l'index binaire en texte
        elif param[1] == 'b_to_t_index':
            #parametres : fichier indexé binaire, le fichier text des termes (vocabulaires), le fichier index texte sorti
            writeTextIndexFromBinaryIndex(param[2], param[3], param[4])
        else:
            print "Erreur"
    else:
        print "Erreur"


