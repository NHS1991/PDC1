#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'NHS'

import sys
import re
import math
import struct
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
from blist import sorteddict

porter_stemmer = PorterStemmer()

#Récupérer les termes dans la requete (faire le stemming et enlever les mots vides)
def getTerms(query):
    stop_words=stopwords.words('english')
    query=query.lower()
    query=re.sub(r"[^a-z0-9 ]",' ',query) #remplacer les caractères non-alphabetiques par espace
    words=[x for x in query.split() if x not in stop_words]  #eliminer les mots vides
    terms=[porter_stemmer.stem(word) for word in words]
    return terms

# Retourne un dictionnaire dont la clé est le terme et la valeur est la fréquence de chaque terme dans la requete
def term_frequency_query(terms):
    term_freq_dict = sorteddict({})
    for term in terms:
        try:
            term_freq_dict[term] += 1
        except KeyError:
            term_freq_dict[term] = 1
    return term_freq_dict

#Calculer idf du terme
def inverse_document_frequency(nb_docs_containing, nb_docs):
    return math.log10(nb_docs/nb_docs_containing)

#Récuperer le résultat trié par le score en ordre décroissant (utiliser l'algorithme cosinus)
def topScores(query,f_index,f_term,f_docID,f_result, nb_scores):
    terms = getTerms(query) #Récuperer les termes dans la requete
    set_terms = set(terms) #Convertir la liste en set
    term_freq_query_dict = term_frequency_query(terms) # Récuperer les fréquences de chaque terme dans la requete
    term_weight_query_dict = {} #Le tf-idf de chaque terme dans la requete
    score_doc_dict = {} #Le score de chaque fichier
    norm_doc_dict = {} #La norme du vecteur construit par les fréquences de chaque terme dans chaque doc
    nb_docs = 0
    #Ouvrir le fichier de réindexation des docID et lire ligne par ligne et stocker les valeurs de norme de chaque doc
    with open(f_docID) as f_docID_read:
        for doc_line in f_docID_read:
            nb_docs += 1
            doc_line_arr = doc_line.split(":")
            doc_id = int(doc_line_arr[0])
            norm_doc = float(doc_line_arr[1].split("|")[3])#La norme du vecteur construit par les fréquences de chaque terme dans le doc dont l'id est doc_id
            norm_doc_dict[doc_id] = norm_doc #Stocker la norme dans le dictionnaire dont la clé est le docid
            score_doc_dict[doc_id] = 0.0
    count_found_term = 0 #Le nombre de terme dont la postingslist est déjà trouvée
    #Ouvrir le fichier index binaire en mode lecture en binaire
    with open(f_index,"rb") as f_index_read:
        #Ouvrir le fichier de vocabulaires
        with open(f_term,"r") as f_term_read:
            #Lire le fichier de vocabulaires ligne par ligne (autrement dit terme par terme)
            for term_line in f_term_read:
                term_line_arr = term_line.split("|")
                term = term_line_arr[0]
                #Si on trouve un terme, récupérer sa postingslist et calculer les valeurs
                if term in set_terms:
                    count_found_term +=1
                    nb_docs_containing_term = int(term_line_arr[1]) #Le nombre de docs contient le terme
                    idf_term = inverse_document_frequency(nb_docs_containing_term,nb_docs) #Calculer idf du terme
                    term_weight_query_dict[term] = term_freq_query_dict[term]*idf_term #Calculer tf-idf du terme dans la requete
                    pos_postingslist_term = int(term_line_arr[2]) #Le début de la postingslist du terme dans le fichier index
                    f_index_read.seek(pos_postingslist_term*8) #Pointer au début de la postingslist du terme dans le fichier index pour lire
                    for i in range(nb_docs_containing_term):
                        docid_term = struct.unpack("i",f_index_read.read(4))[0] #L'id du doc
                        nb_occs_term = struct.unpack("i",f_index_read.read(4))[0] #Le nombre d'occurences du terme dans le doc
                        score_doc_dict[docid_term] += term_weight_query_dict[term]*nb_occs_term #Augmenter le score du doc pour la requete
                if count_found_term == len(set_terms):
                    break #Si on trouve déjà toutes la postingslist de chaque terme, arrête la lecture
    for doc_id in score_doc_dict:
        score_doc_dict[doc_id] /= norm_doc_dict[doc_id] #Calculer le vrai score (l'agorithme cosinus)
    score_doc_list = sorted(score_doc_dict.items(), key=lambda item:item[1],reverse = True) #Trier les scores en ordre décroissant
    nb_lines = 0
    if nb_scores == 0: #Si le parametre de nombre de scores égale à 0, on récupère tous les scores de tous les docs
        nb_scores = nb_docs
    with open(f_result,"w") as f_result_write:
        for doc_tuple in score_doc_list:
            if nb_lines<nb_scores: #Écrire le score correspondant à un doc dans le fichier de résultat
                print>>f_result_write,str(doc_tuple[0])+"||"+str(doc_tuple[1])
                nb_lines += 1
            else:
                break


if __name__ == "__main__":
    if len(sys.argv) == 6:
        params = sys.argv
        f_index = params[1] #fichier d'index
        f_term = params[2] #fichier des termes (vocabulaires)
        f_docID = params[3] #fichier des docIDs réindexés
        f_result = params[4] #fichier de résultat sorti
        nb_scores = int(params[5]) #nombre de résultat retourné
        query = raw_input("Recherche:")
        topScores(query,f_index,f_term,f_docID,f_result,nb_scores)
    else:
        print "Erreur"


