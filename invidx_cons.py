from lxml import etree
import re
import os
#import tqdm
from copy import deepcopy
from math import sqrt, log2
import argparse
import time
from bpetoken import merges, merge_vocab, make_vocab

aparser = argparse.ArgumentParser(description="Process filenames and flags")
aparser.add_argument("input_directory", nargs=1)
aparser.add_argument("binfilenames", nargs=1)
aparser.add_argument("compression_flag", nargs=1)
aparser.add_argument("tokeniser_flag", nargs=1)
args = aparser.parse_args()

input_directory = args.input_directory[0]
binfilenames = args.binfilenames[0]
compression_flag = int(args.compression_flag[0])
tokeniser_flag = int(args.tokeniser_flag[0])

print("Input  Directory is = "+input_directory)
print("Index and Dict files will have the prefix = "+ binfilenames)
print("0 means No Compression and 1 means VBE compression = "+ str(compression_flag))
print("0 means Standard tokeniser and 1 means BPE tokeniser = "+ str(tokeniser_flag))


## Creates the dictionary that stores (tokens -> pointers) + (Length), the docID length and 
## Creates the Inv Postings list
def no_compression_standard():
    start_time = time.time()
    parser = etree.XMLParser(strip_cdata=False)
    tokens= {}

    # addr1 = "f1copy"
    # addr2 = "f2copy"
    # document_list_1 = [os.path.join(addr1, file) for file in os.listdir(addr1)]
    # document_list_2 = [os.path.join(addr2, file) for file in os.listdir(addr2)]
    # document_list_list = [document_list_1, document_list_2]
    print("First pass on documents has begun!")
    total_docs = 0
    files_in_directory = os.listdir(input_directory)
    document_list = [(input_directory + "/" + file) for file in files_in_directory]
    for document in document_list:
        with open(document, 'r') as docUnAppended:
            docs_string = docUnAppended.read()
        
        #tree = etree.parse(document, parser)
        tree = etree.fromstring("<INIT>\n"+ docs_string + "</INIT>", parser)
        docids = tree.xpath(".//DOC/DOCID/text()")
        total_docs += len(docids)
        titles = tree.xpath(".//DOC/TITLE/text()")
        titles = []
        for enclosing_tag in tree.findall("DOC/TITLE"): # Extract the text content within the enclosing tag
            enclosing_tag_text = ' '.join(text.strip() for text in enclosing_tag.itertext())
            titles.append(enclosing_tag_text)

        contents = []
        for multiline_tag in tree.findall(".//DOC/CONTENT"):
            multiline_text = ''.join(multiline_tag.itertext()).strip()
            contents.append(multiline_text)

        assert (len(docids) == len(titles) and len(contents)==len(titles)), "Spurious input at %s" % document
        for i in range(len(docids)):
            tokens_per_document = set()
            lines = contents[i].splitlines()
            for line in lines:
                for word in line.split():
                    word = word.lower()
                    word = re.sub(r'\W+', '', word)
                    tokens_per_document.add(word)
                    
            lines = titles[i].splitlines()
            for line in lines:
                for word in line.split():
                    word = word.lower()
                    word = re.sub(r'\W+', '', word)
                    tokens_per_document.add(word)
            
            for token in tokens_per_document:
                if token not in tokens:
                    tokens[token] = 1
                else:
                    tokens[token] += 1
        print("Document processed = " + document )
                
    tokens_copy = deepcopy(tokens)
    token_keys = sorted(tokens.keys())
    ## tokens now contains mapping tokens -> the number of documents it occurs in
    ## which is basically the idf values for these numbers

    tf_length = 4
    print(str(total_docs) + " = total documents parsed")
    max_bytes = len(str(total_docs)) + tf_length # the 4 is for storing tf information

    print("We need %s number of bytes to store each docnum" % str(max_bytes-tf_length))
    print("For each doc in a term, we need %s number of bytes to store (docID, tf) pair" % str(max_bytes))

    pointers={}
    curr_pointer = 0
    for term in token_keys:
        pointers[term] = curr_pointer
        curr_pointer += max_bytes*(tokens[term])


    # now, take care that each number that represents that document would have to be represented by 
    # exactly max_bytes number of bytes. Pad with appropriate amount of leading 0s
    # the last tf_length bytes for each doc represent tf

    map_num_to_doc = {} # store the number to doc name mapping
    map_num_to_docScore = {} # map docnum to doc_normalising_score

    #dict_file = "dictionary.txt"
    dict_file =  binfilenames + ".dict" 
    with open(dict_file, "wb") as df_file:
        string_to_write = ("pointerToIntToDocMapsBeginsAt " + str(curr_pointer) + " andAreLines " + str(total_docs)  + "\n").encode()
        df_file.write(string_to_write)
        string_to_write = ("sizeOfDocIDsIs " + str(max_bytes) + " sizeOftf " + str(tf_length)+ " compression 0 tokeniser 0" + "\n").encode()
        df_file.write(string_to_write)
        for token in token_keys:
            string_to_write = (token + " " + str(tokens[token]) +  " " + str(pointers[token]) + "\n").encode()
            df_file.write(string_to_write)

    ## We have now written the dictionary , containing metadata, pointers and idf data
    print("Second pass on documents has begun, now writing the postings list!")
    postings_list = binfilenames + ".idx"
    num_curr_doc = 0
    with open(postings_list, 'wb') as pl_file:
        for document in document_list:
            with open(document, 'r') as docUnAppended:
                docs_string = docUnAppended.read()
        
            #tree = etree.parse(document, parser)
            tree = etree.fromstring("<INIT>\n"+ docs_string + "</INIT>", parser)
            #tree = etree.parse(document, parser)
            docids = tree.xpath(".//DOC/DOCID/text()")
            titles = []
            for enclosing_tag in tree.findall("DOC/TITLE"): # Extract the text content within the enclosing tag
                enclosing_tag_text = ' '.join(text.strip() for text in enclosing_tag.itertext())
                titles.append(enclosing_tag_text)
            
            contents = []
            for multiline_tag in tree.findall(".//DOC/CONTENT"):
                multiline_text = ''.join(multiline_tag.itertext()).strip()
                contents.append(multiline_text)
        
            assert (len(docids) == len(titles) and len(contents)==len(titles)), "Spurious input"
            for i in range(len(docids)):
                words_found_in_this_document = {}
                map_num_to_doc[num_curr_doc] = docids[i]
                lines = contents[i].splitlines()
                for line in lines:
                    for word in line.split():
                        word = word.lower()
                        word = re.sub(r'\W+', '', word)
                        if word not in words_found_in_this_document:
                            words_found_in_this_document[word] = 1
                        else:
                            words_found_in_this_document[word] += 1
                        
                        
                lines = titles[i].splitlines()
                for line in lines:
                    for word in line.split():
                        word = word.lower()
                        word = re.sub(r'\W+', '', word)
                        if word not in words_found_in_this_document:
                            words_found_in_this_document[word] = 1
                        else:
                            words_found_in_this_document[word] += 1
                        
                # now that we have collected tokens in this document and their tf, time to write to bin file
                # also calculate the per document weighing factor
                score_for_this_doc = 0.0
                for word in words_found_in_this_document.keys():
                    idfi = log2(1 + (total_docs/tokens_copy[word]))
                    tfi = log2(1 + words_found_in_this_document[word])
                    score_for_this_doc += idfi*tfi

                    start_pointer = pointers[word]
                    offset = start_pointer + (tokens[word] -1)*max_bytes
                    tokens[word] -= 1 #indicating that this word has been written for one of the documents it occurs in
    
                    # write num_curr_doc at offset position
                    pl_file.seek(offset)
                    padding_required = ("0"*(max_bytes-tf_length - len(str(num_curr_doc)))).encode() # had to update w -tf_length because padding here is only for docID 
                    docid_string = padding_required + str(num_curr_doc).encode()
                    
                    tf_for_this_doc_token = str(min(9999, words_found_in_this_document[word])) #fixed to length 4 for now
                    padded_tf = ("0"*(tf_length - len(tf_for_this_doc_token)) + tf_for_this_doc_token).encode()
                    string_to_write = docid_string + padded_tf
                    pl_file.write(string_to_write)
                    
                map_num_to_docScore[num_curr_doc] = sqrt(score_for_this_doc)
                num_curr_doc += 1


    ## We have the mapping from tokens to pointers & df_i(used for idf calculation later)
    print("Writing the docNum -> docID mapping into the postings list now!")
    with open(postings_list, "ab") as pl_file:
        for i in sorted(map_num_to_doc.keys()):
            string_to_write = (str(i) + " " + map_num_to_doc[i] + " " + str(map_num_to_docScore[i])+ "\n").encode()
            pl_file.write(string_to_write)
    end_time = time.time()
    print("No compression, Standard index constructed in = " + str(end_time - start_time) +" seconds")
    return 

def compression_standard():
    ## Dictionary's first two lines are metadata
    ## all subsequent lines are (token, df, Pointer, BytesToRead)

    ## Postings lists  starts with the doc_num -> [docID, Score] pointer
    ## Then all subsequents are listed as doc_num<space>tf<?>
    start_time = time.time()
    parser = etree.XMLParser(strip_cdata=False)
    tokens= {}
    total_docs = 0
    map_num_to_doc = {} # store the number to doc name mapping
    doc_num = 0
    files_in_directory = os.listdir(input_directory)
    document_list = [(input_directory + "/" + file) for file in files_in_directory]
    print("First pass beginning!")
    for document in document_list:
        with open(document, 'r') as docUnAppended:
            docs_string = docUnAppended.read()
        tree = etree.fromstring("<INIT>\n"+ docs_string + "</INIT>", parser)

        docids = tree.xpath(".//DOC/DOCID/text()")
        total_docs += len(docids)
        titles = tree.xpath(".//DOC/TITLE/text()")
        titles = []
        for enclosing_tag in tree.findall("DOC/TITLE"):
            enclosing_tag_text = ' '.join(text.strip() for text in enclosing_tag.itertext())
            titles.append(enclosing_tag_text)

        contents = []
        for multiline_tag in tree.findall(".//DOC/CONTENT"):
            multiline_text = ''.join(multiline_tag.itertext()).strip()
            contents.append(multiline_text)

        assert (len(docids) == len(titles) and len(contents)==len(titles)), "Spurious input at %s" % document
        for i in range(len(docids)):
            tokens_per_document = {} # term -> tf mapping in this document
            map_num_to_doc[doc_num] = docids[i]
            lines = contents[i].splitlines()
            for line in lines:
                for word in line.split():
                    word = word.lower()
                    word = re.sub(r'\W+', '', word)
                    if word in tokens_per_document:
                        tokens_per_document[word] += 1
                    else:
                        tokens_per_document[word] = 1
                    
            lines = titles[i].splitlines()
            for line in lines:
                for word in line.split():
                    word = word.lower()
                    word = re.sub(r'\W+', '', word)
                    if word in tokens_per_document:
                        tokens_per_document[word] += 1
                    else:
                        tokens_per_document[word] = 1
            
            for token in tokens_per_document.keys():
                if token not in tokens:
                    tokens[token] = {}
                tokens[token][doc_num] = tokens_per_document[token]
                
            doc_num += 1
        print("Pass 1 successful for Document = " + document )
                
    token_keys = sorted(tokens.keys())
    ## tokens now contains mapping tokens -> {document -> tf}
    ## which is basically the idf values for these numbers

    ## VBE this time!
    map_num_to_docScore = {}

    ## We have now written the dictionary , containing metadata, pointers and idf data

    num_curr_doc = 0
    
    for document in document_list:
        with open(document, 'r') as docUnAppended:
            docs_string = docUnAppended.read()
        tree = etree.fromstring("<INIT>\n"+ docs_string + "</INIT>", parser)

        docids = tree.xpath(".//DOC/DOCID/text()")
        titles = []
        for enclosing_tag in tree.findall("DOC/TITLE"): # Extract the text content within the enclosing tag
            enclosing_tag_text = ' '.join(text.strip() for text in enclosing_tag.itertext())
            titles.append(enclosing_tag_text)
        
        contents = []
        for multiline_tag in tree.findall(".//DOC/CONTENT"):
            multiline_text = ''.join(multiline_tag.itertext()).strip()
            contents.append(multiline_text)
    
        assert (len(docids) == len(titles) and len(contents)==len(titles)), "Spurious input"
        for i in range(len(docids)):
            words_found_in_this_document = set()
            map_num_to_doc[num_curr_doc] = docids[i]
            lines = contents[i].splitlines()
            for line in lines:
                for word in line.split():
                    word = word.lower()
                    word = re.sub(r'\W+', '', word)
                    words_found_in_this_document.add(word)
                    # if word not in words_found_in_this_document:
                    #     words_found_in_this_document[word] = 1
                    # else:
                    #     words_found_in_this_document[word] += 1
                    
                    
            lines = titles[i].splitlines()
            for line in lines:
                for word in line.split():
                    word = word.lower()
                    word = re.sub(r'\W+', '', word)
                    words_found_in_this_document.add(word)
                    # if word not in words_found_in_this_document:
                    #     words_found_in_this_document[word] = 1
                    # else:
                    #     words_found_in_this_document[word] += 1
                    
            # now that we have collected tokens in this document and their tf, time to write to bin file
            # also calculate the per document weighing factor
            score_for_this_doc = 0.0
            for word in words_found_in_this_document:
                idfi = log2(1 + (total_docs/len(tokens[word])))
                tfi = log2(1 + tokens[word][num_curr_doc])
                score_for_this_doc += idfi*tfi

                # start_pointer = pointers[word]
                # offset = start_pointer + (tokens[word] -1)*max_bytes
                # tokens[word] -= 1 #indicating that this word has been written for one of the documents it occurs in

                # # write num_curr_doc at offset position
                # pl_file.seek(offset)
                # padding_required = ("0"*(max_bytes-tf_length - len(str(num_curr_doc)))).encode() # had to update w -tf_length because padding here is only for docID 
                # docid_string = padding_required + str(num_curr_doc).encode()
                # #pl_file.write(string_to_write)
                
                # tf_for_this_doc_token = str(min(tf_length_comparator, words_found_in_this_document[word])) ##BE CAREFUL HERE
                # padded_tf = ("0"*(tf_length - len(tf_for_this_doc_token)) + tf_for_this_doc_token).encode()
                # string_to_write = docid_string + padded_tf
                # pl_file.write(string_to_write)
                #print("wrote word = " + word + " at pos = " + str(offset) + " for doc = " + str(num_curr_doc) + " with tf = " + padded_tf.decode() + " wrote str = " + string_to_write.decode())
                
            map_num_to_docScore[num_curr_doc] = sqrt(score_for_this_doc)
            num_curr_doc += 1
        print("Document processed pass2= " + document )

    
    dict_file = binfilenames + ".dict"
    idxfile = binfilenames + ".idx"
    with open(dict_file, "wb") as df_file:
        with open(idxfile, 'wb') as if_file:
            for i in range(total_docs):
                string_to_write = (str(i) + " " + map_num_to_doc[i] + " " + str(map_num_to_docScore[i])+ "\n").encode()
                if_file.write(string_to_write)
            line1 = ("pointerToPS " + str(if_file.tell()) + " andAreLines " + str(total_docs)  + "\n").encode()
            line2 = string_to_write = ("sizeOfDocIDsIs " + str(0) + " sizeOftf " + str(0)+ " compression 1 tokeniser 0" + "\n").encode()
            df_file.write(line1)
            df_file.write(line2)
            # for m in merges:
            #   df_file.write((m[0] + " " + m[1] + "?").encode())
            #df_file.write("\n".encode())
            curr_pointer = if_file.tell()
            for token in token_keys:
                cur_token_len = 0
                for file_num in tokens[token].keys():
                    string_to_write = (str(file_num) + " " + str(tokens[token][file_num]) + "?").encode()
                    cur_token_len += len(string_to_write)
                    if_file.write(string_to_write)
                    #print("PS token = " + token + " found in file = " + str(file_num) + " with tf = " + str(tokens[token][file_num]))
                string_df = (token + " " + str(len(tokens[token])) + " " + str(curr_pointer) + " " + str(cur_token_len) + "\n").encode()
                curr_pointer += cur_token_len
                df_file.write(string_df)
                #print("wrote token " + string_df.decode())

    ## We have the mapping from tokens to pointers & df_i(used for idf calculation later)            
    # Note that we still have all the space available from curr_pointer to write in postings list
    end_time = time.time()
    print("Compression, Standard tokenisation in = " + str(end_time - start_time) + " seconds")
    return

def no_compression_bpe():
    start_time = time.time()
    parser = etree.XMLParser(strip_cdata=False)
    tokens= {}
    total_docs = 0
    files_in_directory = os.listdir(input_directory)
    document_list = [(input_directory + "/" + file) for file in files_in_directory]
    ms = merges(input_directory, 2000) ##HYPER-PARAMETER
    print("Merges Done!")
    for document in document_list:
        with open(document, 'r') as docUnAppended:
            docs_string = docUnAppended.read()
        tree = etree.fromstring("<INIT>\n"+ docs_string + "</INIT>", parser)
        
        docids = tree.xpath(".//DOC/DOCID/text()")
        total_docs += len(docids)
        titles = tree.xpath(".//DOC/TITLE/text()")
        titles = []
        # Extract the text content within the enclosing tag
        for enclosing_tag in tree.findall("DOC/TITLE"):
            enclosing_tag_text = ' '.join(text.strip() for text in enclosing_tag.itertext())
            titles.append(enclosing_tag_text)

        contents = []
        for multiline_tag in tree.findall(".//DOC/CONTENT"):
            multiline_text = ''.join(multiline_tag.itertext()).strip()
            contents.append(multiline_text)

        assert (len(docids) == len(titles) and len(contents)==len(titles)), "Spurious input at %s" % document
        for i in range(len(docids)):
            lines = (titles[i] + contents[i])
            lines = lines.lower()
            lines = re.sub(r'\W+', '', lines)
            vocab = make_vocab(lines)
            for m in ms:
                vocab = merge_vocab(m, vocab)

            tokens_in_this_doc = set() # this ensures that each gets added just once per document
            for eltuple in vocab.keys():
                for token in eltuple:
                    tokens_in_this_doc.add(token)
            
            for token in tokens_in_this_doc:
                if token not in tokens:
                    tokens[token] = 1
                else:
                    tokens[token] += 1
        print("Document processed = " + document )
                
    tokens_copy = deepcopy(tokens)
    token_keys = sorted(tokens.keys())
    ## tokens now contains mapping tokens -> the number of documents it occurs in
    ## which is basically the idf values for these numbers

    tf_length = 4
    print(str(total_docs) + " = total documents parsed")
    max_bytes = len(str(total_docs)) + tf_length #the 4 is for storing tf information

    print("We need %s number of bytes to store docnums" % str(max_bytes-tf_length))
    print("For each doc in a term, we need %s number of bytes to store docID + tf" % str(max_bytes))

    pointers={}
    curr_pointer = 0
    for term in token_keys:
        pointers[term] = curr_pointer
        curr_pointer += max_bytes*(tokens[term])

    print("Pointers allocated!")
    # now, take care that each number that represents that document would have to be represented by 
    # exactly max_bytes number of bytes. Pad with appropriate amount of leading 0s
    # the last tf_length bytes for each doc represent tf

    map_num_to_doc = {} # store the number to doc name mapping
    map_num_to_docScore = {}

    
    dict_file = binfilenames + ".dict"
    with open(dict_file, "wb") as df_file:
        string_to_write = ("pointerToIntToDocMapsBeginsAt " + str(curr_pointer) + " andAreLines " + str(total_docs)  + "\n").encode()
        df_file.write(string_to_write)
        string_to_write = ("sizeOfDocIDsIs " + str(max_bytes) + " sizeOftf " + str(tf_length)+ " compression 0 tokeniser 1" + "\n").encode()
        df_file.write(string_to_write)
        for m in ms:
            df_file.write((m[0] + " " + m[1] + "?").encode())
        df_file.write("\n".encode())
        for token in token_keys:
            string_to_write = (token + " " + str(tokens[token]) +  " " + str(pointers[token]) + "\n").encode()
            df_file.write(string_to_write)

    print("Dict file written!")
    ## We have now written the dictionary , containing metadata, pointers and idf data

    postings_list = binfilenames + ".idx"
    num_curr_doc = 0
    with open(postings_list, 'wb') as pl_file:
        for document in document_list:
            with open(document, 'r') as docUnAppended:
                docs_string = docUnAppended.read()
            tree = etree.fromstring("<INIT>\n"+ docs_string + "</INIT>", parser)

            docids = tree.xpath(".//DOC/DOCID/text()")
            titles = []
            for enclosing_tag in tree.findall("DOC/TITLE"): # Extract the text content within the enclosing tag
                enclosing_tag_text = ' '.join(text.strip() for text in enclosing_tag.itertext())
                titles.append(enclosing_tag_text)
            
            contents = []
            for multiline_tag in tree.findall(".//DOC/CONTENT"):
                multiline_text = ''.join(multiline_tag.itertext()).strip()
                contents.append(multiline_text)
        
            assert (len(docids) == len(titles) and len(contents)==len(titles)), "Spurious input"
            for i in range(len(docids)):
                map_num_to_doc[num_curr_doc] = docids[i]
                lines = (titles[i] + contents[i])
                lines = lines.lower()
                lines = re.sub(r'\W+', '', lines)
                vocab = make_vocab(lines)
                for m in ms:
                    vocab = merge_vocab(m, vocab)
                        
                # now that we have collected tokens in this document and their tf, time to write to bin file
                # also calculate the per document weighing factor
                
                words_found_in_this_document = {}
                for eltuple, freq in vocab.items():
                    for word in eltuple:
                        if word in words_found_in_this_document:
                            words_found_in_this_document[word] += freq
                        else:
                            words_found_in_this_document[word] = freq

                score_for_this_doc = 0.0
                for word in words_found_in_this_document:
                    idfi = log2(1 + (total_docs/tokens_copy[word]))
                    tfi = log2(1 + words_found_in_this_document[word])
                    score_for_this_doc += idfi*tfi

                    start_pointer = pointers[word]
                    offset = start_pointer + (tokens[word] -1)*max_bytes
                    tokens[word] -= 1 #indicating that this word has been written for one of the documents it occurs in
    
                    # write num_curr_doc at offset position
                    pl_file.seek(offset)
                    padding_required = ("0"*(max_bytes-tf_length - len(str(num_curr_doc)))).encode() # had to update w -tf_length because padding here is only for docID 
                    docid_string = padding_required + str(num_curr_doc).encode()
                    #pl_file.write(string_to_write)
                    
                    tf_for_this_doc_token = str(min(9999, words_found_in_this_document[word])) ##BE CAREFUL HERE
                    padded_tf = ("0"*(tf_length - len(tf_for_this_doc_token)) + tf_for_this_doc_token).encode()
                    string_to_write = docid_string + padded_tf
                    pl_file.write(string_to_write)
                    #print("wrote word = " + word + " at pos = " + str(offset) + " for doc = " + str(num_curr_doc) + " with tf = " + padded_tf.decode() + " wrote str = " + string_to_write.decode())
                    
                map_num_to_docScore[num_curr_doc] = sqrt(score_for_this_doc)
                num_curr_doc += 1
            print("Postings list written for doc = " + document)

    ## We have the mapping from tokens to pointers & df_i(used for idf calculation later)

    # map num -> name in indexfile as well into the postings_list
    with open(postings_list, "ab") as pl_file:
        for i in sorted(map_num_to_doc.keys()):
            string_to_write = (str(i) + " " + map_num_to_doc[i] + " " + str(map_num_to_docScore[i])+ "\n").encode()
            pl_file.write(string_to_write)

    print("All done!")
    end_time = time.time()
    print("No Compression, BPE index constructed in " + str(end_time - start_time) + " seconds")

def compression_bpe():
    start_time = time.time()
    parser = etree.XMLParser(strip_cdata=False)
    tokens= {}
    total_docs = 0
    files_in_directory = os.listdir(input_directory)
    document_list = [(input_directory + "/" + file) for file in files_in_directory]
    ms = merges(input_directory, 2000)
    print("Merges Done!")
    doc_num = 0
    map_num_to_doc = {}
    for document in document_list:
        with open(document, 'r') as docUnAppended:
            docs_string = docUnAppended.read()
        tree = etree.fromstring("<INIT>\n"+ docs_string + "</INIT>", parser)

        docids = tree.xpath(".//DOC/DOCID/text()")
        total_docs += len(docids)
        titles = tree.xpath(".//DOC/TITLE/text()")
        titles = []
        for enclosing_tag in tree.findall("DOC/TITLE"):
            enclosing_tag_text = ' '.join(text.strip() for text in enclosing_tag.itertext())
            titles.append(enclosing_tag_text)

        contents = []
        for multiline_tag in tree.findall(".//DOC/CONTENT"):
            multiline_text = ''.join(multiline_tag.itertext()).strip()
            contents.append(multiline_text)

        assert (len(docids) == len(titles) and len(contents)==len(titles)), "Spurious input at %s" % document
        for i in range(len(docids)):
            map_num_to_doc[doc_num] = docids[i]
            lines = contents[i] + "\n" + titles[i]
            vocab_for_this_doc = make_vocab(lines)
            
            for m in ms:
                vocab_for_this_doc = merge_vocab(m, vocab_for_this_doc)
            
            for tuple_tokens, freq in vocab_for_this_doc.items():
                for token in tuple_tokens:
                    if token not in tokens:
                        tokens[token] = {}
                    if doc_num in tokens[token].keys():
                        tokens[token][doc_num] += freq
                    else:
                        tokens[token][doc_num] = freq
                
            doc_num += 1
        print("Pass 1 successful for Document = " + document )
                
    token_keys = sorted(tokens.keys())
    ## tokens now contains mapping tokens -> {document -> tf}
    ## which is basically the idf values for these numbers

    ## VBE this time!
    map_num_to_docScore = {}
    num_curr_doc = 0
    for document in document_list:
        with open(document, 'r') as docUnAppended:
            docs_string = docUnAppended.read()
        tree = etree.fromstring("<INIT>\n"+ docs_string + "</INIT>", parser)

        docids = tree.xpath(".//DOC/DOCID/text()")
        titles = []
        for enclosing_tag in tree.findall("DOC/TITLE"): # Extract the text content within the enclosing tag
            enclosing_tag_text = ' '.join(text.strip() for text in enclosing_tag.itertext())
            titles.append(enclosing_tag_text)
        
        contents = []
        for multiline_tag in tree.findall(".//DOC/CONTENT"):
            multiline_text = ''.join(multiline_tag.itertext()).strip()
            contents.append(multiline_text)
    
        assert (len(docids) == len(titles) and len(contents)==len(titles)), "Spurious input"
        for i in range(len(docids)):
            words_found_in_this_document = set()
            map_num_to_doc[num_curr_doc] = docids[i]
            lines = contents[i] + "\n" + titles[i]
            vocab_for_this_doc = make_vocab(lines)
            for m in ms:
                vocab_for_this_doc = merge_vocab(m, vocab_for_this_doc)
                    
            for eltuple in vocab_for_this_doc:
                for token in eltuple:
                    words_found_in_this_document.add(token)
            # now that we have collected tokens in this document and their tf, time to write to bin file
            # also calculate the per document weighing factor
            score_for_this_doc = 0.0
            for word in words_found_in_this_document:
                idfi = log2(1 + (total_docs/len(tokens[word])))
                tfi = log2(1 + tokens[word][num_curr_doc])
                score_for_this_doc += idfi*tfi
                
            map_num_to_docScore[num_curr_doc] = sqrt(score_for_this_doc)
            num_curr_doc += 1
        print("Document processed pass2= " + document )

    
    dict_file = binfilenames + ".dict"
    idxfile = binfilenames + ".idx"
    with open(dict_file, "wb") as df_file:
        with open(idxfile, 'wb') as if_file:
            for i in range(total_docs):
                string_to_write = (str(i) + " " + map_num_to_doc[i] + " " + str(map_num_to_docScore[i])+ "\n").encode()
                if_file.write(string_to_write)
            line1 = ("pointerToPS " + str(if_file.tell()) + " andAreLines " + str(total_docs)  + "\n").encode()
            line2 = string_to_write = ("sizeOfDocIDsIs " + str(0) + " sizeOftf " + str(0)+ " compression 1 tokeniser 1" + "\n").encode()
            df_file.write(line1)
            df_file.write(line2)
            for m in ms:
                df_file.write((m[0] + " " + m[1] + "?").encode())
            df_file.write("\n".encode())
            # for m in merges:
            #   df_file.write((m[0] + " " + m[1] + "?").encode())
            #df_file.write("\n".encode())
            curr_pointer = if_file.tell()
            for token in token_keys:
                cur_token_len = 0
                for file_num in tokens[token].keys():
                    string_to_write = (str(file_num) + " " + str(tokens[token][file_num]) + "?").encode()
                    cur_token_len += len(string_to_write)
                    if_file.write(string_to_write)
                    #print("PS token = " + token + " found in file = " + str(file_num) + " with tf = " + str(tokens[token][file_num]))
                string_df = (token + " " + str(len(tokens[token])) + " " + str(curr_pointer) + " " + str(cur_token_len) + "\n").encode()
                curr_pointer += cur_token_len
                df_file.write(string_df)
                #print("wrote token " + string_df.decode())

    ## We have the mapping from tokens to pointers & df_i(used for idf calculation later)            
    # Note that we still have all the space available from curr_pointer to write in postings list
    end_time = time.time()
    print("Compression, BPE tokenisation in = " + str(end_time - start_time) + " seconds")
    return



if compression_flag == 0 and tokeniser_flag == 0:
    no_compression_standard()
elif compression_flag == 1 and tokeniser_flag == 0:
    compression_standard()
elif compression_flag == 0 and tokeniser_flag == 1:
    no_compression_bpe()
else:
    compression_bpe()
