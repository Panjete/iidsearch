## To read queries from test_query.txt, process them and generate keywords for searching
from readers_11 import getMapping, getVals, pointers_to_post, get_merges
from process_query11 import processQ
from bpetoken import make_vocab, merge_vocab
from lxml import etree
import re
import time

qtest = "test_query.txt"
intm_file = "intm_queries.xml"
outfile = "output.txt"

def q11(queryfile, outputfile,indexfile, dictfile):
    with open(queryfile, 'r') as file:
        lines = file.readlines()
    processed_lines = ['<INIT>\n']
    for line in lines:
        if line.startswith('<title>'):
            processed_lines.append('</num>\n')
        elif line.startswith('<desc>'):
            processed_lines.append('</title>\n')
        elif line.startswith('<narr>'):
            processed_lines.append('</desc>\n')
        elif line.startswith('</top>'):
            processed_lines.append('</narr>\n')

        line = line.replace("&", "&amp;")
        processed_lines.append(line)
    processed_lines.append('</INIT>\n')
    with open(intm_file, 'w') as pf:
        pf.writelines(processed_lines)


    parser = etree.XMLParser()
    tree = etree.parse(intm_file, parser)
    query_nums_pp = tree.xpath(".//top/num/text()")
    query_titles_pp = tree.xpath(".//top/title/text()")
    query_desc_pp = tree.xpath(".//top/desc/text()")
    query_narr_pp = tree.xpath(".//top/narr/text()")

    query_nums = []
    for qn in query_nums_pp:
        pattern = r'\d+(\d+)?'
        match = re.search(pattern, qn)
        if match:
            query_nums.append(match.group())

    query_titles = []
    query_desc = []
    query_narr = []

    # prune content for processing
    translation_table = str.maketrans("", "", "(),?.:" )
    # prunes full sentences
    def prune(istr):
        istr = istr.lower()
        istr = istr.split()
        outistr = []
        for issstr in istr:
            outistr.append(issstr.translate(translation_table))
        return outistr

    merges = get_merges(dictfile)

    query_titles = list(map(prune, query_titles_pp))
    query_desc = list(map(prune, query_desc_pp))

    pointers = pointers_to_post(dictfile)
    mapToDocs = getMapping(indexfile, dictfile)
    [_, numdocs, docIDsize, tf_length, _, _] = getVals(dictfile)

    times = 0.0
    for i in range(len(query_nums)):
        start_time = time.time()
        terms_non_tokenised = query_titles[i] + query_desc[i]
        terms_split = " ".join(terms_non_tokenised)
        vocab_q = make_vocab(terms_split)
        for m in merges:
            vocab_q = merge_vocab(m, vocab_q)
        terms_tokenised = []
        for key, freq in vocab_q.items():
            for el in key:
                for _ in range(freq):
                    terms_tokenised.append(el)

        top_100 = processQ(terms_tokenised, indexfile, pointers, numdocs, mapToDocs)
        with open(outputfile, 'a') as of_file:
            for key, val in top_100:
                of_file.write(query_nums[i] + " 0 " + key + " " + str(val) + "\n")
        end_time = time.time()
        times += (end_time - start_time)
    
        print("Time to process docID = " + query_nums[i] + " is " + str(end_time-start_time))
    print("Average time to process a query is = " + str(times/100))


