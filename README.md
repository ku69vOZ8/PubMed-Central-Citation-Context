# PubMed-Central-Citation-Context

To use this Python program to generate the citation context datasets from the PubMed Central full text, the users should setup up the environment with the following steps:

1. git clone this repository to your local disk
2. in the terminal, use command "pip3 install pipenv" to install pipenv
3. use command "pipenv shell"
4. use command "pipenv install"
5. change the variable "rootDir" in manage.py to the directory of the PMC papers on your disk
6. run the program by the command "python3 manage.py"