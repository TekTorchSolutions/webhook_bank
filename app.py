from flask import Flask
from flask_pymongo import PyMongo
from flask import request
from flask import make_response
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from stop_words import get_stop_words
import string
from textblob import Word
import json
import os


app = Flask(__name__)

app.config['MONGO_DBNAME'] = 'bankfaq'
app.config["MONGO_URI"] = "mongodb://admin:admin@ds111204.mlab.com:11204/bankfaq"
mongo = PyMongo(app)
with app.app_context():
    credit_card_faqs = mongo.db["context_faqs"]
    context_record=mongo.db["context"]


es=Elasticsearch(['https://elastic:26DOr8LJ0c4DUTAk23gb698j@159c3a26cdeb89d7f37b2ccce76a9e21.us-east-1.aws.found.io:9243/'])
#constants
INDEX_NAME="bank_data"
TYPE="faqs"

def check_db():
    for faq in credit_card_faqs.find():

        doc={
            '_op_type':'update',
            '_index':INDEX_NAME,
            '_type':TYPE,
            '_id': str(faq["_id"]),

            "doc":{
                'text': faq['question']
            },
            "doc_as_upsert":True



        }
        yield (doc)
bulk(es,check_db(),stats_only=True,raise_on_error=False)


@app.route('/webhook', methods=['POST'])
def webhook():



    context=retrieve_context()

    possible_contexts=["common","internet banking",'mobile banking app','home loan','credit card','everyday transaction account','online savings account','term deposit','interestme savings','personal loans','insurance','business term deposit','travel','securecode','mobile banking manager','mistaken internet payment','pin select service','debit mastercard reissue']




    req = request.get_json(silent=True, force=True)
    print('Request:', json.dumps(req, indent=4))
    # context=req.get("contexts").get("name")
    result = req.get("result")
    parameters = result.get("parameters")
    query = ""
    for key, value in parameters.items():
        query = query + " " + value
    #query to lowercase
    query = query.lower()

    #remove punctuation and stop words
    query=remove_punctuation_and_stop_words(query)
    #spell check query
    final_query=spell_check(query)
    #splitted_query=final_query.split()
    was_there=False
    for q in possible_contexts:
        if q in final_query:
            set_context(q)
            was_there=True
            break
    if was_there==False:
        final_query=final_query+" " +context

    print(final_query)


    result = es.search(index=INDEX_NAME, doc_type=TYPE, body={"query": {"match": {"text": final_query.strip()}}})

    if result.get('hits') is not None and len(result['hits'].get('hits')) is not 0:
        print(result.get('hits'))
        print(result['hits'].get('hits'))
        response_q=(result['hits']['hits'][0]['_source']['text'])
        doc=credit_card_faqs.find_one({"question":response_q})

        response=doc["answer"] + " ["+doc["context"]+"] "

        #response=doc['context']

    else:
        response="I could not quite comprehend it!Could you be any more vague?!!!"



    #response = tf_idf_score(query, documents)
    print(response)

    res = {
        "speech": response,
        "displayText": response,
        # "data": data,
        # "contextOut": [],
        "source": "bank_webhook"
    }
    res = json.dumps(res, indent=4)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r

def spell_check(query):
    #split query
    splitted_query=query.split()
    #empty list for spell checked query
    corrected_query=[]
    #searching freq_dict in db
    dict_collection=mongo.db["context_dict_collection"]
    freq_dict=dict_collection.find_one({"name":"freq_dict"})["freq_dict"]
    #stop words
    stop_words=get_stop_words("en")
    stop_words.append("can")
    #for each word in splitted query
    for word in splitted_query:
        #convert to testblob word
        blob_word=Word(word)
        #all the possible corrections to word
        possible_corrections=blob_word.spellcheck()
        #initial counter
        freq_counter = 1
        #for the case when spelling is incorrected but no word in document to correct it
        at_least_one = False
        #in case the spelling is correct
        corrected_word = blob_word
        #for each possible correction in the word
        for p in possible_corrections:
            #p[0]'s are the corrections and p[1] scores
            if p[0] in freq_dict.keys():
                #signifies at least one correction is present in dictionary so frequency based correction
                at_least_one = True
                #frequency of p[0]
                frequency = freq_dict[p[0]]
            else:
                frequency = 0
            #keeping highest frequency and corresponding word in record
            if frequency >= freq_counter and p[0] not in stop_words:
                freq_counter = frequency
                corrected_word = p[0]
        #no correction was present in dictionary
        if at_least_one is False:
            #return correction with highest score
            corrected_word = blob_word.correct()
        corrected_query.append(corrected_word)
    return " ".join(corrected_query)


def remove_punctuation_and_stop_words(query):
    #remove punctuations
    query = query.translate({ord(c): None for c in string.punctuation})
    #tokenize query
    tokenized_query = query.split()
    #get stop words
    stop_words = get_stop_words("en")
    #for each stop word
    for i in range(len(stop_words)):
        #remove punctuation from it
        stop_words[i] = stop_words[i].translate({ord(c): None for c in string.punctuation})
        #remove stop word
        if stop_words[i] in tokenized_query:
            # query=query.replace(stop_words[i],"")
            tokenized_query.remove(stop_words[i])
    query = " ".join(tokenized_query)
    return query


def retrieve_context():
    document = context_record.find_one({'purpose': "context_record"})
    print(document)
    if document == None:
        print("hi")
        context = ""
    else:
        print("bye")
        context = document["context"]
    return context


def set_context(context):
    doc=context_record.find_one({'purpose':"context_record"})
    if doc==None:
        info={'purpose':"context_record",
               "context":context

        }
        context_record.insert_one(info)
    else:
        doc["context"]=context



if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print("Starting app on port %d" % port)

    app.run(debug=False, port=port, host='0.0.0.0')
