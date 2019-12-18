import get_info_from_pmc
import os
import re
# from models import Literature
# from models import Session
# from models import Cite
# from models import CitationContext
# from models import CitationContextText
from models import User
import pandas as pd
import en_core_web_md

nlp = en_core_web_md.load()


def build_citation_index(rootDir):
    # This is the method that runs the background task to store
    # the data from pmc articles to database

    print("Running...")
    count = 0

    for dirName, subdirList, fileList in os.walk(rootDir):
        for fname in fileList:
            fname_is_PMC = re.match("^PMC\d{4,}\.n?xml$", fname) is not None
            if fname_is_PMC:
                print(fname)
                pmc_uid = re.sub(r'\D', "", fname)
                full_path = os.path.join(dirName, fname)
                absolute_path = os.path.abspath(full_path)
                infile = os.path.normpath(absolute_path)
                get_info_from_pmc.build_citation_index_for_each_pmc(infile, pmc_uid)
                count = count + 1
                print(count)


def add_non_pmc_pm_references_for_coword_paper(csv_filename):
    # Input is the collections of cited ids
    # Output is the pmc id list

    print("Running...")
    session = Session()
    literature_query = session.query(Literature)
    cite_query = session.query(Cite)

    dataframe = pd.read_csv(csv_filename)

    for pmc_uid in dataframe['pmc_uid']:

        pmc_uid = str(pmc_uid)
        print(pmc_uid)
        literature = literature_query.filter_by(pmc_uid=pmc_uid).first()
        print(literature)
        if literature:
            # To obtain the reference info
            target_tag = 'ref'
            infile = literature.local_path
            get_info_from_pmc.get_general_method(target_tag, infile, get_info_from_pmc.get_reference, literature)

        session.commit()


#
# def get_localpath(csv_filename):
#     # This method is used only once
#     # to add the local path for pmc literatures
#     # Some of the pmc literatures lack local path
#     # And the program has been corrected
#     print("Running...")
#     count = 0
#     session = Session()
#     literature_query = session.query(Literature)
#
#     dataframe = pd.read_csv(csv_filename)
#     len_dataframe = len(dataframe['pmc_uid'])
#     # print(dataframe['pmc_uid'])
#     # print('2737492' in dataframe['pmc_uid'])
#     for pmc_uid in dataframe['pmc_uid']:
#         fname = "PMC" + str(pmc_uid) + ".nxml"
#         for dirName, subdirList, fileList in os.walk(rootDir):
#             if fname in fileList:
#                 full_path = os.path.join(dirName, fname)
#                 absolute_path = os.path.abspath(full_path)
#                 infile = os.path.normpath(absolute_path)
#                 count = count + 1
#                 print(count)
#
#                 literature = literature_query.filter_by(pmc_uid=pmc_uid).first()
#                 literature.local_path = infile
#                 print(infile)
#                 session.add(literature)
#
#     session.commit()


def get_citation_contexts(csv_filename):
    # Input is the cited_id
    # Output is the built database

    print("Running...")
    get_info_from_pmc.get_citation_contexts_by_cited_list(csv_filename)


# def add_citation_contexts():
#     # To make sure every cite has citationcontext
#     # This method is to solve the problem like 3-10 when 4..9
#     # has no ID in the content
#     # And this method is used only once
#     print("Running")
#     get_info_from_pmc.add_citation_contexts(csv_filename)

def get_citememes():
    # Not finished yet.

    print("Running...")
    session = Session()
    citation_context_text_query = session.query(CitationContextText)

    for citation_context_text in citation_context_text_query.all():
        text = citation_context_text.text
        text = re.sub(r"\([^\(]*(~~\d+~~)[^\)]*\)", "", text)
        doc = nlp(text)
        print(doc)
        chunks = list(doc.noun_chunks)
        print(chunks)
        pass


def get_citer_text(csv_filename):
    # Input is the collections of pubmed record id (pmid)
    # Output is the citer's citation context for pubmed record

    print("Running...")
    session = Session()
    literature_query = session.query(Literature)
    cite_query = session.query(Cite)
    citationcontext_query = session.query(CitationContext)
    citationcontexttext_query = session.query(CitationContextText)

    dataframe = pd.read_csv(csv_filename)

    with open('./data/output.txt', 'wt', encoding='utf-8') as f:

        for pmid in dataframe['pmid']:
            pmid = str(pmid)
            cite_length = 0
            citationcontext_length = 0
            # print(pmid)
            # print(pmid, file=f)
            literature = literature_query.filter_by(pmid=pmid).first()
            if literature:
                cited_id = literature.id
                # print(cited_id)
                cites = cite_query.filter_by(cited_id=cited_id).all()
                cite_length = len(cites)
                for cite in cites:
                    cite_id = cite.id
                    citationcontexts = citationcontext_query.filter_by(cite_id=cite_id).all()
                    citationcontext_length = citationcontext_length + len(citationcontexts)
                    for citationcontext in citationcontexts:
                        citationcontexttext_id = citationcontext.citationcontexttext_id
                        citationcontexttext = citationcontexttext_query.filter_by(id=citationcontexttext_id).first()
                        text = citationcontexttext.text
                        text = re.sub(r'~~\d+~~', "", text)

                        print(text, file=f, end="")

            print(pmid, cite_length, citationcontext_length, sep=",")
            print("", file=f)


def get_cited_id_list(csv_filename):
    # Input is the collections of pubmed id (pmid)
    # Output is the cited id list
    # In other word, to get the cited ids of those pubmed records
    # which are cited in the citation database
    print("Running...")
    session = Session()
    literature_query = session.query(Literature)
    cite_query = session.query(Cite)

    dataframe = pd.read_csv(csv_filename)

    for pmid in dataframe['pmid']:
        pmid = str(pmid)
        literature = literature_query.filter_by(pmid=pmid).first()
        if literature:
            cited_id = literature.id
            print(cited_id)
            # cites = cite_query.filter_by(cited_id=cited_id).all()
            # # print(len(cites))
            # for cite in cites:
            #     citer_id = cite.citer_id
            #     pmc_literature = literature_query.filter_by(id=citer_id).first()
            #     if pmc_literature:
            #         print(pmc_literature.pmc_uid)


def temp_creat_user():
    ross = User(email='ross@example.com', first_name='Ross', last_name='Lawley').save()
    print(ross.email)


if __name__ == '__main__':
    # rootDir = 'G:/articles'
    # rootDir = '/Volumes/Seagate Expansion Drive/articles'
    # rootDir = './xml_files'
    # rootDir = '../non_comm_use.I-N.xml'
    # rootDir = 'D:/oa_bulk 20181124'
    # rootDir = 'D:/non_comm_use.A-B.xml'
    # rootDir = 'D:/articles'
    # build_citation_index(rootDir)

    temp_creat_user()

    # csv_filename = './data/pmc_uid list 9398.csv'
    # add_non_pmc_pm_references_for_coword_paper(csv_filename)

    # csv_filename = './data/pubmed id list 2489.csv'
    # get_cited_id_list(csv_filename)temp_creat_user

    # csv_filename = './data/cited ids 1376.csv'
    # get_citation_contexts(csv_filename)

    # csv_filename = './data/pubmed id list 2489.csv'
    # get_citer_text(csv_filename)

    # # To test in a single pmc file
    # pmc_uid = '6129088'
    # get_info_from_pmc.get_citation_contexts_by_pmc_uid(pmc_uid)

    # get_citememes()

    # Used only once, to add localpath to literatures, when the original program fails to
    # add localpath for some literatures
    # get_localpath()
    pass
