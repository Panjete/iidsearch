## Inverted Index Construction, and BPE Tokenisation

For implementational and algorithmic details, please refer the report "algorithmic_details.pdf"

Note that the reader files have been constructed for the TREC-like datasets and queryfiles, and may need to be adopted for different file formats. Signatures of functions have been commented to facilitate this.


To create the index and the dictionary file:

1. Call  `bash invidx.sh [directoryname] [indexfile] [compressionFlag] [tokenizerFlag]`
2. Calls `invidx_cons.py`, which reads the input files, learns BPE (if asked) and constructs the dictionay and the postings list.
3. Compression Flag (0/1) denotes Variable Byte Encoding On/Off and BPE Tokeniser flag (0/1) denotes BPE Tokenisation On/Off
4. `[directoryname]` is the directory path to the dataset whose index is being constructed, and `[indexfile]` is the name that will be generated for the output files.


To search the built index:

1. Call `bash tf_idf_search.sh [queryfile] [resultfile] [indexfile] [dictionary]`
2. Calls `top.py`, which uses a reader to figure out the compression and encoding strategies used in the `[indexfile]` and `[dictionary]`.
3. Based on this, uses the relevant reader and query processing file to process and retrieve the queries.

To compute the F1 scores:
   
1. Call `python retrieval_efficiency.py`  (edit the filenames in retrieval_efficiency.py)
2. The outputs are already TREC_EVAL compatible, and further metrics can be computed by configuring trec eval if the need be.

The build file just checks lxml availability, and installs it if not present.

Files in the `files` folder are samples of the formats of files the present code is compatible with.

## Computation 

The Vanilla No Compression, No Encoding framework is able to construct the index of around a 2GB Corpus in just 982.55 seconds, and boasts an Average Query Retrieval Time of 1.276 seconds, with an Average Precision of 0.611!