## Evaluation file for handling

given_file = "qrels_test.txt"
my_result = "rs11.txt"
relevant_docs = {}
my_docs = {}
qnums = set()
with open(given_file, 'r') as gf:
    lines = gf.readlines()

for line in lines:
    #print(line)
    words = line.split()
    qnums.add(int(words[0]))
    #print(words)
    if(int(words[3]) > 0):
        doc_name = words[2]
        qnum = int(words[0])
        if qnum in relevant_docs.keys():
            relevant_docs[qnum].add(doc_name)
        else:
            relevant_docs[qnum] = set()
            relevant_docs[qnum].add(doc_name)
        
with open(my_result, 'r') as mr:
    lines = mr.readlines()

for line in lines:
    words = line.split()
    doc_name = words[2]
    qnum = int(words[0])
    if qnum in my_docs.keys():
        my_docs[qnum].add(doc_name)
    else:
        my_docs[qnum] = set()
        my_docs[qnum].add(doc_name)

precisions = []
recalls = []
f1s = []
numToQnum = sorted(qnums)
#print(numToQnum)

for i in range(len(qnums)):
#for i in range(2):
    a = len(relevant_docs[numToQnum[i]])/100
    precisions.append(a)
    # true and positive = 
    trueAndPositive = len(relevant_docs[numToQnum[i]] & my_docs[numToQnum[i]])
    positive = len(relevant_docs[numToQnum[i]])
    b = trueAndPositive/positive
    recalls.append(b)
    c = (2*a*b)/(a+b)
    f1s.append(c)
    # print(a)
    # print(trueAndPositive)
    # print(positive)
    print("F1 score for doc = " + str(numToQnum[i]) + " is " + str(c) )

f1init = 0.0
precisionInit = 0.0
reInit = 0.0
for i in range(len(f1s)):
    f1init += f1s[i]
    precisionInit += precisions[i]
    reInit += recalls[i]

print("Average F1 score = " + str(f1init/100))
print("Average Precision = " + str(precisionInit/100))
print("Average Recall = " + str(reInit/100))
