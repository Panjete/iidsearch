## Inverted Index Construction, and Variable Byte Encoding

For implementational and algorithmic details, please refer the report "algorithmic_details.pdf"

Note that the reader files have been constructed for the TREC-like datasets and queryfiles, and may need to be adopted for different file formats 
To create the index and the dictionary file:

    bash invidx.sh <directoryname> <indexfile> <compressionFlag> <tokenizerFlag>

To search the built index:

    bash tf_idf_search.sh <queryfile> <resultfile> <indexfile> <dictionary>

To compute the F1 scores:
    # edit the filenames in retrieval_efficiency.py and 
    python retrieval_efficiency.py


* The build file just checks lxml availability, and installs it if not present.

* The script file "invidx.sh" runs the appropriate function for the compression and tokenizer modes.

* The script file "tf_idf_search.sh" invoked "top.py", which further checks the metaData and infers the compression and tokenizer modes.
* Then, it redirects the control flow to the appropriate reader that parses the index file as required and computes the top100 for each query.