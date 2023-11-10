## To read queries from test_query.txt, process them and generate keywords for searching
from readers_00 import getMapping, getVals, pointers_to_post
from process_query00 import processQ
from lxml import etree
import re
import time

qtest = "test_query.txt"
intm_file = "intm_queries.xml"
outfile = "output.txt"

def q00(queryfile, outputfile,indexfile, dictfile):
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


    query_titles = list(map(prune, query_titles_pp))
    query_desc = list(map(prune, query_desc_pp))

    pointers = pointers_to_post(dictfile)
    mapToDocs = getMapping(indexfile, dictfile)
    [_, numdocs, docIDsize, tf_length, _, _] = getVals(dictfile)

    total_time = 0.0
    for i in range(len(query_nums)):
        start_time = time.time()
        top_100 = processQ(query_titles[i] + query_desc[i], indexfile, pointers, docIDsize, tf_length, numdocs, mapToDocs)
        with open(outputfile, 'a') as of_file:
            for key, val in top_100:
                of_file.write(query_nums[i] + " 0 " + key + " " + str(val) + "\n")
        end_time = time.time()
        total_time += end_time - start_time
        print("Time to process docID = " + query_nums[i] + " is " + str(end_time-start_time))

    print("Average time for processing a Query is = " + str(total_time/100.0))