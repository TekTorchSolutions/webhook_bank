import numpy as np
import re

#from pymongo import MongoClient


#client=MongoClient("mongodb://admin:admin@ds111204.mlab.com:11204/bankfaq")

#db=client["bankfaq"]

#credit_card_faq=db["credit_card_faqs"]

#documents=[]
#for faq in credit_card_faq.find():
#    documents.append(faq["answer"])

#print(documents)


#number_of_docs=len(documents)
#query="credit card account pay"




def normalize_dict(diction):
    sum_square=0
    for key,value in diction.items():
        sum_square=sum_square+value*value
    divisor=np.sqrt(sum_square)
    for key,value in diction.items():
        value=value/divisor
        diction[key]=value
    return diction

def multiply_dict(master_diction,slave_diction):
    out_diction={}
    for key,value in master_diction.items():
        if key in slave_diction.keys():
            out_diction[key]=master_diction[key]*slave_diction[key]
        else:
            out_diction[key]=0
    return out_diction

def get_sum_diction(diction):
    sum=0
    for key,value in diction.items():
        sum=sum+value
    return sum



def find_term_frequency(text):
    term_frequency = {}
    splitted_text = re.split('\.|, |\*|\n| ', text)
    for word in splitted_text:
        if word in term_frequency:
            term_frequency[word] = term_frequency[word] + 1
        else:
            term_frequency[word] = 1
    return term_frequency



def find_term_frequency_weight(text,term_frequency):
    encountered_word=[]
    term_frequency_weight={}
    splitted_text=re.split('\.|, |\*|\n| ', text)
    for word in splitted_text:
        if word in encountered_word:
            continue
        else:
            if term_frequency[word]!=0 :
                term_frequency_weight[word]=1+np.log10(term_frequency[word])
            else:
                term_frequency_weight[word]=0
    return term_frequency_weight



def find_document_frequncy(text,documents):
    document_frequency = {}

    splitted_text = re.split('\.|, |\*|\n| ', text)
    for word in splitted_text:
        document_frequency[word] = 0
    for document in documents:
        for word in splitted_text:
            if word in document:
                document_frequency[word] = document_frequency[word] + 1
            else:
                continue
    return document_frequency

def find_inverse_document_frequency(text,document_frequency,documents):
    splitted_text = re.split('\.|, |\*|\n| ', text)
    inverse_document_frequency={}
    encountered_word=[]
    for word in splitted_text:
        if word in encountered_word:
            continue
        else:
            inverse_document_frequency[word]=np.log10(len(documents)/document_frequency[word])

    return inverse_document_frequency


def tf_idf_score(query,documents):
    query_term_frequency=find_term_frequency(query)
    print(query_term_frequency)
    query_term_frequency_weight=find_term_frequency_weight(query,query_term_frequency)
    print(query_term_frequency_weight)
    query_document_frequency=find_document_frequncy(query,documents)
    print(query_document_frequency)
    #query_document_frequency={"best":50000,"car":10000,"insurance":1000}
    query_inverse_document_frequency=find_inverse_document_frequency(query,query_document_frequency,documents)
    query_tf_idf=multiply_dict(query_term_frequency_weight,query_inverse_document_frequency)
    query_tf_idf_norm=normalize_dict(query_tf_idf)
    angles=[]
    for document in documents:
        document_term_frequency=find_term_frequency(document)
        document_term_frequency_weight=find_term_frequency_weight(document,document_term_frequency)
        document_term_frequency_weight_norm=normalize_dict(document_term_frequency_weight)
        angle=get_sum_diction(multiply_dict(query_tf_idf_norm,document_term_frequency_weight_norm))
        angles.append(angle)
    return documents[np.argmax(angles)]








