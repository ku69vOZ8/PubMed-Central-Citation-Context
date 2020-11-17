import get_info_from_pmc
import os
import re

# The users need to change rootDir for their own PMC data directory
rootDir = 'E:\\pmc 20191208\\oa_bulk'

def test_count(rootDir):
    print("Running...")

    count = 0
    for dirName, subdirList, fileList in os.walk(rootDir):

        infiles = []
        for fname in fileList:

            fname_is_PMC = re.match("^PMC\d{4,}\.n?xml$", fname) is not None
            if fname_is_PMC:
                count = count + 1
                # print(fname)
                print(count)


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
                # start_time = time.time()
                get_info_from_pmc.build_citation_index_for_each_pmc(infile)
                # end_time = time.time()
                # print(f"build_citation_index_for_each_pmc {end_time - start_time} seconds.")


def process_dir():
    # To do process the path name /articles and  /oa_bulk
    # upper_path = "/articles"
    # upper_path = "/oa_bulk"
    from models import Literature

    count = 0
    for literature in Literature.objects:
        # print(l.local_path)
        if literature.local_path:
            literature.local_path = literature.local_path.replace("articles", "")
            print(literature.local_path)
            literature.save()
            count += 1
            print(count)

    pass


if __name__ == '__main__':
    build_citation_context_database(rootDir)

    # process_dir()

    # test_count(rootDir)

    pass
