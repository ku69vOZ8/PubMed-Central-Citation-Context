# PubMed-Central-Citation-Context
by Joseph (Fengjun) Sun
## How to use the program

To use this Python program to generate the citation context datasets from the PubMed Central full text, the users should setup up the environment with the following steps with Python 3.7:

1. git clone this repository to your local disk
2. in the terminal, use command "pip3 install pipenv" to install pipenv if you do not have pipenv installed
3. use command "pipenv shell"
4. use command "pipenv install"
5. change the variable "rootDir" in manage.py to the directory of the PMC papers on your disk
6. run the program by the command "python3 manage.py"

## Dataset usage notes
The data can be accessed freely with the DOI: www.dx.doi.org/10.11922/sciencedb.00393. The users should apply the command mongorestore to load data from the downloaded binary database directory to MongoDB database (see https://docs.mongodb.com/database-tools/mongorestore/). The database directory contains the following files:
-	citation_context.bson
-	citation_context.metadata.json
-	citation_context_text.bson
-	citation_context_text.metadata.json
-	cite.bson
-	cite.metadata.json
-	literature.bson
-	literature.metadata.json

After the data is loaded in MongoDB by the command mongorestore, the users can then use tools provided by MongoDB to analyze the data. 
