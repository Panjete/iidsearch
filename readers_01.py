## For no compression, but tokenisation

## Use to reclaim dictionary from dict_file
## returns a dict called pointers
## for token t, pointers[t] -> [pointerAddressFor t, numberOfFilesThatHave t]
def pointers_to_post(dict_file):
    pointers = {}
    with open(dict_file, "rb") as binary_file:
        file_content = binary_file.read()

    lines = file_content.split(b'\n')
    for line in lines:
        line = line.decode()
        words = line.split()
        if len(words) == 3:
            pointers[words[0]] = [int(words[2]), int(words[1])]
        
    # TO_DO: optionally, house idf instead of df here

    # for key in pointers.keys():
    #     print(key + " occurs at " + str(pointers[key][0]) + " for length = " + str(pointers[key][1]))
    return pointers


## returns the pointer to the start of
## the int -> filename mapping int the postings list
## and the number of documents 
## and the size of each docID identifier
## and the size of tf_string in postings
## and compression 0 - none 1- yes
## and tokeniser 0 - standard 1 - BPE 
## these were saved in the first 2 lines of the dictionary
def metaData(dict_file):

    with open(dict_file, "rb") as binary_file:
        lineA = b""
        while True:
            char = binary_file.read(1)
            if char == b'\n' or not char:
                break
            lineA += char
    
        line1 = lineA.decode()
        words1 = line1.split()
        lineB = b""
        while True:
            char = binary_file.read(1)
            if char == b'\n' or not char:
                break
            lineB += char
    
    line2 = lineB.decode()
    words2 = line2.split()
    return [int(words1[1]), int(words1[3]), int(words2[1]), int(words2[3]), int(words2[5]), int(words2[7])]
    #return [int(words1[1]), int(words1[3]), int(words2[1]), int(words2[3]), 0, 0]

#metaData("dictionary.txt")
#pointers_to_post("dictionary.txt")
## gives [mapPointerStart, numDocs, sizeID]
def getVals(dict_file):
    return metaData(dict_file)


## generates map from docID -> docName, docScore
def getMapping(postings_file, dict_file):
    map_docID_to_doc = {}
    [map_pointers_begin_at, num_docs, _, _, _, _]  = getVals(dict_file)
    
    with open(postings_file, 'rb') as pf:
        pf.seek(map_pointers_begin_at)
        for i in range(num_docs):
            lineB = b""
            while True:
                char = pf.read(1)
                if char == b'\n':
                    break
                lineB += char
            lineA = lineB.decode()
            words = lineA.split()
            map_docID_to_doc[int(words[0])] = [words[1].strip(), float(words[2])]
        
    # for token in map_docID_to_doc.keys():
    #     print(str(token) + " maps to document = " + map_docID_to_doc[token])

    return map_docID_to_doc


def getDocs(term, pointers, postings_file, id_size, tf_length):
    if term in pointers.keys():
        [pointer_start, num_docs] = pointers[term]
    else:
        [pointer_start, num_docs] = pointers["a"]
    with open(postings_file, 'rb') as pf:
        pf.seek(pointer_start)
        line = pf.read(id_size * num_docs)
        docIDs = [line[i:i + id_size] for i in range(0, len(line), id_size)]
        doc_numbers = [int(id[0:id_size-tf_length]) for id in docIDs]
        doc_tfs = [int(id[id_size-tf_length:]) for id in docIDs]
    return doc_numbers, doc_tfs


#getVals("dictionary.txt")
#getMapping("postings_list.txt", "dictionary.txt")

## default ifile here = merges_bpe_non_compressed.txt
def get_merges(ifile):
    merges = []
    with open(ifile, 'rb') as ifi:
        while True:
            char = ifi.read(1)
            if char == b'\n':
                break

        while True:
            char = ifi.read(1)
            if char == b'\n':
                break

        lineB = b""
        while True:
            char = ifi.read(1)
            if char == b'\n':
                break
            lineB += char

        lineA = lineB.decode()
        words = lineA.split("?")
        for word in words[:-1]:
            wordi = word.split()
            merges.append((wordi[0], wordi[1]))
    return merges
