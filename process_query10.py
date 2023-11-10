from readers_10 import getDocs
from math import log2
import heapq

#dict_file = "dictionary.txt"
#postings_file = "postings_list.txt"

#doc_numbers, doc_tfs = getDocs("site", pointers, postings_file, docIDsize, tf_length)
#print(doc_numbers)
#
# print(doc_tfs)
# doc_numbers = [int(id[0:docIDsize-tf_length]) for id in docids]
# doc_tfs = [int(id[docIDsize-tf_length:]) for id in docids]
#docnames = [mapToDocs[id][0] for id in doc_numbers]
#print(docnames)

def perQscore(term, postings_file, pointers, numdocs, accumulators):
    # accumulators is a dictionary Num->score that is initialised to empty
    # one iteration of this function updates scores for each document already present, else adds it
    docnums_for_this_term, tfs = getDocs(term, pointers, postings_file)
    if term not in pointers.keys():
        term = "the"
    for i in range(len(docnums_for_this_term)):
        doc = docnums_for_this_term[i] ## is an integer
        tf_i = 1 + log2(tfs[i]) #term does occur here, tf_i > 0
        idfi_term = log2(1 + (numdocs/pointers[term][1])) ##correct here
        score_to_be_added = tf_i * idfi_term
        if doc in accumulators:
            accumulators[doc] += score_to_be_added
        else:
            accumulators[doc] = score_to_be_added
    return accumulators

def acc_query(terms, postings_file, pointers, numdocs):
    accumulators = {}
    for term in terms:
        perQscore(term, postings_file, pointers, numdocs, accumulators)
    return accumulators

def normalise_documents(maptoDocs, accumulators):
    for doc in accumulators.keys():
        accumulators[doc] = (accumulators[doc]/maptoDocs[doc][1])
    return accumulators

def rank_results(accumulators, mapIDtoDoc):
    heap = [(value, key) for key, value in accumulators.items()]
    top_100_keys_with_values = heapq.nlargest(100, heap)
    top_100_docs = [(mapIDtoDoc[key][0], value) for value, key in top_100_keys_with_values]
    return top_100_docs

def processQ(terms, postings_file, pointers, numdocs, maptoDocs):
    accumulators = acc_query(terms, postings_file, pointers, numdocs)
    accumulators = normalise_documents(maptoDocs, accumulators)
    top_100 = rank_results(accumulators, maptoDocs)
    # print("Ranking for query Q = " + str(terms) + " is :>")
    # for key, val in top_100:
    #     print(key + " " + str(val))
    return top_100

terms = "issuance of general exclusion order".split()

#processQ(terms, postings_file, pointers, docIDsize, tf_length, numdocs, mapToDocs)


