import collections
import re
import os
from lxml import etree


## get mapping key -> frequency mapping
## key is a tuple split on characters by default.
## for example, (l, o, w, e, s, t, _ ) -> 5
def make_vocab(text):
    vocab = {}
    words = text.split()
    words = [re.sub(r'\W+', '', word) for word in words]
    for word in words:
        chars = [ch for ch in word]
        chars.append("_")
        word_tuple = tuple(chars)
        if word_tuple in vocab:
            vocab[word_tuple] += 1
        else:
            vocab[word_tuple] = 1
    return vocab


## Gives all pairs of sequences from vocabulary, with their frequencies
def get_pairs(vocab):
    pairs = collections.defaultdict(int)
    for key, freq in vocab.items():
        for i in range(len(key)-1):
            pair = (key[i], key[i+1])
            pairs[pair] += freq
    return pairs


## Merges neighboring chars in keys that have the given pair
## for example, (l, o, w, e, s, t, _) -> (l, o, w, es, t, _) if pair == (e, s)
def merge_vocab(pair, vocab):
    keys_to_del = {}
    for key, freq in vocab.items():
        flag = False
        for i in range(len(key)-1):
            if (key[i] == pair[0] and key[i+1] == pair[1]):
                flag = True
                # pair = (key[i], key[i+1])
                # pairs[pair] += freq
        if flag:
            keys_to_del[key] = freq
    for key, freq in keys_to_del.items():
        del vocab[key]
        i = 0
        str_init = []
        boo = False
        while i < len(key)-1:
            if (key[i] == pair[0] and key[i+1] == pair[1]):
                str_init.append(key[i] + key[i+1])
                i += 2
                boo = True
            else:
                str_init.append(key[i])
                i += 1
                boo = False
        if not boo:
            str_init.append(key[-1])
        if (len(key) > 2):
            if(key[-3] == pair[0] and key[-2] == pair[1]):
                str_init.append(key[-1])

        vocab[tuple(str_init)] = freq
    #print(vocab)
    return vocab


# finds the most frequent neighbours num_merges number of times
def learn_tokens(ts, num_merges):
    print("Learning merges!")
    merges = []
    for i in range(num_merges):
        pr = get_pairs(ts)
        if len(pr) > 1:
            best = max(pr, key = pr.get)
            ts = merge_vocab(best, ts)
            merges.append(best)
    #print(merges)
    return merges

#learn_tokens(text, 8)

## returns the vocabulary for learning tokens in this folder
def vocabularise_documents(foldername):
    vocab = {}
    parser = etree.XMLParser(strip_cdata=False)
    directory_list = [os.path.join(foldername, file) for file in os.listdir(foldername)]
    for i in range(0, len(directory_list), 4):
        document = directory_list[i]
        print("Learning document = " + document)
        with open(document, 'r') as docUnAppended:
            docs_string = docUnAppended.read()
        tree = etree.fromstring("<INIT>\n"+ docs_string + "</INIT>", parser)
        #print("Reading for vocab construction, document = " + document)
        titles = []
        
        for enclosing_tag in tree.findall("DOC/TITLE"): # Extract the text content within the enclosing tag
            enclosing_tag_text = ' '.join(text.strip() for text in enclosing_tag.itertext())
            titles.append(enclosing_tag_text)

        contents = []
        for multiline_tag in tree.findall(".//DOC/CONTENT"):
            multiline_text = ''.join(multiline_tag.itertext()).strip()
            contents.append(multiline_text)

        for titl in titles:
            words = titl.split()
            for word in words:
                word = word.lower()
                word = re.sub(r'\W+', '', word)
                chars = [ch for ch in word]
                chars.append("_")
                word_tuple = tuple(chars)
                if word_tuple in vocab:
                    vocab[word_tuple] += 1
                else:
                    vocab[word_tuple] = 1

        for cont in contents:
            words = cont.split()
            for word in words:
                word = word.lower()
                word = re.sub(r'\W+', '', word)
                chars = [ch for ch in word]
                chars.append("_")
                word_tuple = tuple(chars)
                if word_tuple in vocab:
                    vocab[word_tuple] += 1
                else:
                    vocab[word_tuple] = 1
        
        
    return vocab

## Returns the top numerges mergers of pairs
def merges(foldername, numerges):
    vocab = vocabularise_documents(foldername)
    print("Reading for vocab construction for learning")
    merges = learn_tokens(vocab, numerges)
    print("Merges learnt!")
    return merges

# text = "low low low low low lower lower newest newest newest newest newest newest widest widest widest"
# vocab = make_vocab(text)
# print(vocab)
# pr = get_pairs(vocab)
# print(pr)
# best = max(pr, key = pr.get)
# print(best)
# vocab = merge_vocab(best, vocab)
# print(vocab)
# learn(text, 4)