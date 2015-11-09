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

def getTerms(query):
    stop_words=stopwords.words('english')
    query=query.lower()
    query=re.sub(r"[^a-z0-9 ]",' ',query) #remplacer les caractères non-alphabetiques par espace
    words=[x for x in query.split() if x not in stop_words]  #eliminer les mots vides
    terms=[porter_stemmer.stem(word) for word in words]
    return terms

def term_frequency_query(terms):
    term_freq_dict = sorteddict({})
    for term in terms:
        try:
            term_freq_dict[term] += 1
        except KeyError:
            term_freq_dict[term] = 1
    return term_freq_dict

def inverse_document_frequency(nb_docs_containing, nb_docs):
    return math.log10(nb_docs/nb_docs_containing)

def topScores(query,f_index,f_term,f_docID,f_result, nb_scores):
    terms = getTerms(query)
    set_terms = set(terms)
    term_freq_query_dict = term_frequency_query(terms)
    term_weight_query_dict = {}
    score_doc_dict = {}
    norm_doc_dict = {}
    nb_docs = 0
    with open(f_docID) as f_docID_read:
        for doc_line in f_docID_read:
            nb_docs += 1
            doc_line_arr = doc_line.split(":")
            doc_id = int(doc_line_arr[0])
            norm_doc = float(doc_line_arr[1].split("|")[3])
            norm_doc_dict[doc_id] = norm_doc
            score_doc_dict[doc_id] = 0.0
    count_found_term = 0
    with open(f_index,"rb") as f_index_read:
        with open(f_term,"r") as f_term_read:
            for term_line in f_term_read:
                term_line_arr = term_line.split("|")
                term = term_line_arr[0]
                if term in set_terms:
                    count_found_term +=1
                    nb_docs_containing_term = int(term_line_arr[1])
                    idf_term = inverse_document_frequency(nb_docs_containing_term,nb_docs)
                    term_weight_query_dict[term] = term_freq_query_dict[term]*idf_term
                    pos_postingslist_term = int(term_line_arr[2])
                    f_index_read.seek(pos_postingslist_term*8)
                    for i in range(nb_docs_containing_term):
                        docid_term = struct.unpack("i",f_index_read.read(4))[0]
                        nb_occs_term = struct.unpack("i",f_index_read.read(4))[0]
                        score_doc_dict[docid_term] += term_weight_query_dict[term]*nb_occs_term
                if count_found_term == len(set_terms):
                    break
    for doc_id in score_doc_dict:
        score_doc_dict[doc_id] /= norm_doc_dict[doc_id]
    score_doc_list = sorted(score_doc_dict.items(), key=lambda item:item[1],reverse = True)
    nb_lines = 0
    if nb_scores == 0:
        nb_scores = nb_docs
    with open(f_result,"w") as f_result_write:
        for doc_tuple in score_doc_list:
            if nb_lines<nb_scores:
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


