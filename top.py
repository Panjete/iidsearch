import argparse
from readers_00 import metaData
from q_00 import q00
from q_10 import q10
from q_01 import q01
from q_11 import q11

## TOP file for query processing
aparser = argparse.ArgumentParser(description="Process filenames and flags")
aparser.add_argument("queryfile", nargs=1)
aparser.add_argument("resultfile", nargs=1)
aparser.add_argument("indexfile", nargs=1)
aparser.add_argument("dictfile", nargs=1)
args = aparser.parse_args()

queryfile = args.queryfile[0]
resultfile = args.resultfile[0]
indexfile = args.indexfile[0]
dictfile = args.dictfile[0]

[_, _, _, _, compression_flag, tokeniser_flag] = metaData(dictfile)


### Based on compression and encoding version, use the appropriate handler
if compression_flag == 0 and tokeniser_flag == 0:
    q00(queryfile, resultfile, indexfile, dictfile)
elif compression_flag == 1 and tokeniser_flag == 0:
    q10(queryfile, resultfile, indexfile, dictfile)
elif compression_flag == 0 and tokeniser_flag == 1:
    q01(queryfile, resultfile, indexfile, dictfile)
else:
    q11(queryfile, resultfile, indexfile, dictfile)