import get_info_from_pmc
import os
import re


# The users need to change rootDir for their own PMC data directory
rootDir = '...'


def build_citation_context_database(rootDir):
    print("Running...")
    count = 0
    for dirName, subdirList, fileList in os.walk(rootDir):

        infiles = []
        for fname in fileList:

            fname_is_PMC = re.match("^PMC\d{4,}\.n?xml$", fname) is not None
            if fname_is_PMC:
                count = count + 1
                print(fname)
                print(count)
                full_path = os.path.join(dirName, fname)
                absolute_path = os.path.abspath(full_path)
                infile = os.path.normpath(absolute_path)
                get_info_from_pmc.build_citation_index_for_each_pmc(infile)


if __name__ == '__main__':
    build_citation_context_database(rootDir)
    pass
