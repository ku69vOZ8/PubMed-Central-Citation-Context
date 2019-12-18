from lxml import etree
# from models import Literature
# from models import Cite
# from models import CitationContext
# from models import CitationContextText
# from models import Session
# from models import CitationAnchorPosition
import re
import os
import html
import en_core_web_md
import pandas as pd

basedir = os.path.abspath(os.path.dirname(__file__))
article_namespace = ""
nlp = en_core_web_md.load()

citation_context_abbreviations = ['cf.', 'e.g.', 'i.e.', 'etc.', 'viz.', 'vs.', 'et al.', 'p.', 'pp.', 'Fig.', 'No.']

end_of_sentence_punctuation = ['.', '?', "!", "~~"]


# def add_citation_contexts(csv_filename):
#     # To make sure every cite has citationcontext
#     # This part is to solve the problem like 3-10 when 4..9
#     # has no ID in the content
#
#     session = Session()
#     literature_query = session.query(Literature)
#     cite_query = session.query(Cite)
#     citationcontext_query = session.query(CitationContext)
#
#     dataframe = pd.read_csv(csv_filename)
#     for count, cited_id in enumerate(dataframe['cited_id']):
#         cites = cite_query.filter_by(cited_id=cited_id)
#         print(count + 1)
#         former_cite = None
#         for cite in cites:
#             citationcontexts = citationcontext_query.filter_by(cite=cite).all()
#             if citationcontexts is None:
#                 citationcontext = CitationContext(cite=cite,
#                                                   citationcontext=former_cite.citationcontexttext)
#                 session.add(citationcontext)
#             former_cite = cite
#         session.commit()

def get_citation_contexts_by_pmc_uid(pmc_uid):
    session = Session()
    literature_query = session.query(Literature)
    literature = literature_query.filter_by(pmc_uid=pmc_uid).first()
    if literature:
        infile = literature.local_path
        print(literature.pmc_uid)
        print(infile)
        target_tag = 'p'
        get_general_method(target_tag, infile, get_citation_contexts_for_each_pmc, literature)


def get_citation_contexts_by_cited_list(csv_filename):
    session = Session()
    literature_query = session.query(Literature)
    cite_query = session.query(Cite)

    dataframe = pd.read_csv(csv_filename)
    for count, cited_id in enumerate(dataframe['cited_id']):
        cites = cite_query.filter_by(cited_id=cited_id).all()
        print(count + 1)
        for cite in cites:
            literature = literature_query.filter_by(id=cite.citer_id).first()

            if (literature is None) or (
                    literature.if_citation_context_gotten is True):
                continue

            literature.if_citation_context_gotten = True
            session.add(literature)
            print(literature.pmc_uid)
            infile = literature.local_path
            # print(infile)

            target_tag = 'p'
            get_general_method(target_tag, infile, get_citation_contexts_for_each_pmc, literature)


def build_citation_index_for_each_pmc(infile, pmc_uid):
    # # To find the pmc_id
    # pmc_uid = article_id_find(root, "pmc")
    #
    # if pmc_uid is None:
    #     # print("Can not find the pmc_uid, the program will not proceed.")
    #     return

    session = Session()
    literature_query = session.query(Literature)

    literature = Literature()
    temp_literature_with_pmc_uid = literature_query.filter_by(pmc_uid=pmc_uid).first()
    if temp_literature_with_pmc_uid:
        literature = temp_literature_with_pmc_uid
    else:
        parser = etree.XMLParser(ns_clean=True)
        try:
            tree = etree.parse(infile, parser)
        except etree.XMLSyntaxError as e:
            print(e)
            return

        root = tree.getroot()

        # To find the pmid (or pubmed id)
        pmid = article_id_find(root, "pmid")
        # print(pmid)
        # Literature already been added as a reference.
        # The task next is to update the info for the original reference.
        if pmid:
            temp_literature_by_pmid = literature_query.filter_by(pmid=pmid).first()
            if temp_literature_by_pmid:
                literature = temp_literature_by_pmid
            else:
                literature.pmid = pmid

        literature.pmc_uid = pmc_uid
        literature.local_path = infile

    session.add(literature)

    # To obtain the reference info
    target_tag = 'ref'
    get_general_method(target_tag, infile, get_reference, literature)


def build_citation_index_for_each_pmc_with_pubmed_ref(infile, pmc_uid):
    # # To find the pmc_id
    # pmc_uid = article_id_find(root, "pmc")
    #
    # if pmc_uid is None:
    #     # print("Can not find the pmc_uid, the program will not proceed.")
    #     return

    session = Session()
    literature_query = session.query(Literature)

    temp_literature_with_pmc_uid = literature_query.filter_by(pmc_uid=pmc_uid).first()
    if temp_literature_with_pmc_uid is not None:
        '''
        print(
            "Updated already, pmc_uid is {0}, return.".format(
                pmc_uid
            )
        )
         '''
        return
    # print(pmc_uid)

    parser = etree.XMLParser(ns_clean=True)
    try:
        tree = etree.parse(infile, parser)
    except etree.XMLSyntaxError as e:
        print(e)
        return

    root = tree.getroot()

    literature = Literature()

    # To find the pmid (or pubmed id)
    pmid = article_id_find(root, "pmid")
    # print(pmid)
    # Literature already been added as a reference.
    # The task next is to update the info for the original reference.
    if pmid is not None:
        temp_literature_by_pmid = literature_query.filter_by(pmid=pmid).first()
        if temp_literature_by_pmid is not None:
            literature = temp_literature_by_pmid
        else:
            pass
    else:
        literature.pmid = pmid

    literature.pmc_uid = pmc_uid
    literature.local_path = infile

    # To obtain the reference info
    target_tag = 'ref'
    get_general_method(target_tag, infile, get_reference_with_pmid, literature)


def article_id_find(root, article_id_type):
    # The method to find the id

    path = "//" + article_namespace + \
           "article-id[@pub-id-type=\'" + article_id_type + "\']"
    # print(path)
    temp_list = root.xpath(path)
    if temp_list:
        article_id = temp_list[0].text
    else:
        article_id = None
    return article_id


# This the general method to obtain data (e.g. citationcontext, reference, author)
def get_general_method(target_tag, infile, get_method, *arguments):
    tag = target_tag
    # print(tag)
    context = etree.iterparse(infile, events=('end',), tag=tag)
    get_method(context, *arguments)


# To get citation context
def get_citation_contexts_for_each_pmc(context, *arguments):
    # print("Start!")
    citer = arguments[0]

    session = Session()
    cite_query = session.query(Cite)

    bibr_xpath = etree.XPath(
        ".//{0}xref[@ref-type='bibr']".format(
            article_namespace
        )
    )
    # print(bibr_xpath)

    bibr_xpath = etree.XPath(
        ".//{0}xref[@ref-type='bibr']".format(
            article_namespace
        )
    )
    ref_xpath = etree.XPath(
        ".//{0}xref[@ref-type='ref']".format(
            article_namespace
        )
    )

    child_node_xpath = etree.XPath(
        "{0}child::*".format(article_namespace)
    )

    para_count = 0
    for event, elem in context:

        para_count = para_count + 1
        bibr_list = bibr_xpath(elem)
        if len(bibr_list) == 0:
            bibr_list = ref_xpath(elem)
            if len(bibr_list) == 0:
                # print("len(bibr_list) is 0, maybe there are other bibr(ref)_xpath")
                continue

        # print(para_count)
        # print(len(bibr_list))

        former_bibr = None
        former_bibr_seq = 0
        for bibr in bibr_list:

            # print("Bibr!")

            bibr_text = bibr.text
            # print(bibr_text)
            if bibr_text is None:
                bibr_text = ""

            # print(bibr.attrib["rid"])
            bibr.text = ""

            child_nodes = child_node_xpath(bibr)

            for cn in child_nodes:
                if (cn is None) or (cn.text is None):
                    cn.text = ""
                bibr_text = bibr_text + cn.text
                cn.text = ""

            # This is the block to solve problems like "2<bibr='CR2'>-5<bibr='CR5'>"
            former_bibr_is_not_none = former_bibr is not None
            former_bibr_tail_is_str = False
            former_bibr_tail_match_is_not_none = False

            if former_bibr_is_not_none is True:
                former_bibr_tail_is_str = isinstance(former_bibr.tail, str)
                if former_bibr_tail_is_str is True:
                    former_bibr.tail = html.unescape(former_bibr.tail)
                    former_bibr_tail_match_is_not_none = re.search(r"~~\d+?~~\s*[–-]\s*$", former_bibr.tail) is not None

            if former_bibr_is_not_none and \
                    former_bibr_tail_is_str and \
                    former_bibr_tail_match_is_not_none:

                former_bibr.tail = re.sub(r"[–-]", "", former_bibr.tail)
                former_bibr.tail = re.sub(r"\s+", " ", former_bibr.tail)
                end_rid = (bibr.attrib["rid"])
                # print(end_rid)

                end_cite = cite_query.filter_by(
                    citer=citer, local_reference_id=end_rid
                ).first()

                start_rid_sequence = int(former_bibr_seq)
                end_cite_sequence = 0
                if end_cite:
                    end_cite_sequence = end_cite.reference_sequence
                else:
                    # print("Can't find endcite, that must be wrong.") ADD:?
                    # Note: Since only the references with pmid are collected,
                    # which means the cites table doesn't cover some records,
                    # so this might NOT be wrong.
                    continue

                for count in range(start_rid_sequence + 1, end_cite_sequence + 1):
                    former_bibr.tail = former_bibr.tail + ",~~" + str(count) + "~~"
                # former_bibr.tail = former_bibr.tail

                former_bibr = bibr
                continue

            seqs_str = []

            bibr_text = html.unescape(bibr_text)
            # Replace the blank spaces
            bibr_text = re.sub(r"\s+", " ", bibr_text)
            # This is the block to solve problems like "2<bibr='CR2'>-5<bibr='CR5'>"
            # For example, "2<bibr='CR2'>-4" or "2<bibr='CR2'>–4"
            # It can be compared with similar problem above
            searchObj = re.search(r'(\d+)\s*[–-]\s*(\d+)', bibr_text)
            rids = re.split(r'[;,\s]\s*', bibr.attrib["rid"])
            # print(rids)
            if searchObj:
                # print("searchObj.group() : ", searchObj.group())
                # print("searchObj.group(1) : ", searchObj.group(1))
                # print("searchObj.group(1) : ", searchObj.group(2))
                start = int(searchObj.group(1))
                end = int(searchObj.group(2))
                seqs_str = [str(i) for i in range(start, end + 1)]
                bibr_text = re.sub(r"[–-]", "", bibr_text)
                bibr_text = re.sub(r"\s+", " ", bibr_text)
            else:
                for rid in rids:
                    # print(rid)
                    cite = cite_query.filter_by(
                        citer=citer, local_reference_id=rid
                    ).first()
                    if cite is not None:
                        seq_str = str(cite.reference_sequence)
                        seqs_str.append(seq_str)

            if len(seqs_str) == 0:
                # print("len(seqs) is 0, that must be wrong.") ADD:?
                # Note: Since only the references with pmid are collected,
                # which means the cites table doesn't cover some records,
                # so this might NOT be wrong.
                # print(bibr_text)
                # # print(citer.pmc_uid)
                continue

            if bibr.tail is None:
                bibr.tail = ""

            seqs_text = "~~{0}~~".format("~~~~".join(seqs_str))
            bibr.tail = seqs_text + bibr.tail

            former_bibr = bibr
            former_bibr_seq = seqs_str[-1]

        del bibr_list

        # the paragraph without outer tag
        para_text = etree.tostring(elem, encoding="unicode")
        para_text = re.sub(r"<.*?>", "", para_text)
        # Replace the blank spaces with a single blank space
        para_text = re.sub(r"\s+", " ", para_text)
        para_text = re.sub(r'~~[;,\s]\s?~~', "~~~~", para_text)
        para_text = html.unescape(para_text)
        # eliminate the outer tag
        # para_text = re.sub(r'<p.*?>|</p>\s*$', "", para_text)
        para = nlp(para_text)
        del para_text

        sentences = [sent.string.strip() for sent in para.sents]
        print(sentences)
        del para
        # length_of_sentences = len(sentences)

        while len(sentences) > 0:

            sent_str = sentences.pop(0)
            if (len(sentences) is 0) and (sent_str is ""):
                break
            sent_str = sent_str.strip()

            # print(sent_str)
            # print(next_sent)

            # regExp = r'\s?~~\d+~~[;,\s]?\s?'
            # matchObj = re.match(regExp, next_sent)
            # while matchObj:
            #     # print(matchObj.group())
            #     sent_str = sent_str + " " + matchObj.group()
            #     sent_str = sent_str.strip()
            #     # print(sent_str)
            #     next_sent = re.sub(regExp, " ", next_sent)
            #     next_sent = re.sub(r"\s+", " ", next_sent)
            #     next_sent = next_sent.strip()
            #     # print(next_sent)
            #     matchObj = re.match(regExp, next_sent)

            while 1 is 1:

                if len(sentences) > 0:
                    next_sent = sentences.pop(0)
                else:
                    break
                next_sent = re.sub(r"\s+", " ", next_sent)
                next_sent = next_sent.strip()

                sent_starts_without_uppercase_or_num = re.match(
                    r'^[A-Z]|\d|\'|\"', next_sent
                ) is None
                sent_ends_with_citation_context_abbreviations = sent_str.endswith(
                    tuple(citation_context_abbreviations)
                )
                sent_ends_without_end_of_sentence_punctuation = not sent_str.endswith(
                    tuple(end_of_sentence_punctuation)
                )
                if sent_starts_without_uppercase_or_num or \
                        sent_ends_with_citation_context_abbreviations or \
                        sent_ends_without_end_of_sentence_punctuation:
                    sent_str = sent_str + " " + next_sent
                else:
                    sentences.insert(0, next_sent)
                    break

            sent_str = re.sub(r'\s+', ' ', sent_str.strip())
            sent_str = sent_str.strip()
            # sent_str = html.unescape(sent_str)
            print(sent_str)
            citation_context_text = CitationContextText(text=sent_str)

            search_objs = re.findall(r"~~\d+?~~", sent_str)
            # print(search_objs)
            reference_sequence_list = []
            for so in search_objs:
                # print(so.strip("~~"))
                # sent_str = re.sub(r"~~.*?~~", "", sent_str)

                reference_sequence = int(so.strip("~~"))
                if reference_sequence in reference_sequence_list:
                    continue
                else:
                    reference_sequence_list.append(reference_sequence)

                # print(reference_sequence_list)
                cite = cite_query.filter_by(
                    citer=citer, reference_sequence=reference_sequence
                ).first()
                # print(cite)
                # print(reference_sequence)
                citation_context = CitationContext(
                    cite=cite,
                    citationcontexttext=citation_context_text
                )
                session.add(citation_context)

                # print("Hello!")

                # # The position for so
                # position = sent_str.find(so)
                # citation_anchor_position = CitationAnchorPosition(
                #     citationcontext_id=citation_context.id,
                #     citationcontexttext_id=citation_context_text.id,
                #     position=position
                # )
                # session.add(citation_anchor_position)
                #
                # sent_str = sent_str.replace(so, "")

            del search_objs
            del reference_sequence_list

        elem.clear()
        while elem.getprevious() is not None:
            del elem.getparent()[0]

    # print("End!")

    del context  # end for
    # session.commit()


# To get the references
# And this method excludes the title published year
# for later uses
def get_reference(context, *arguments):
    # arguments = citer(literature)
    citer = arguments[0]
    print(citer)
    session = Session()
    literature_query = session.query(Literature)
    cite_query = session.query(Cite)

    # To find the ref-id, e.g. B1, B2
    ref_id_xpath = etree.XPath(
        "@id".format(article_namespace)
    )
    pmid_xpath = etree.XPath(
        ".//{0}pub-id[@pub-id-type='pmid']".format(
            article_namespace
        )
    )

    '''
    publication_type_xpath = etree.XPath(
        "@publication-type".format(article_namespace)
    )
    article_title_xpath = etree.XPath(
        ".//{0}article-title".format(article_namespace)
    )
    source_title_xpath = etree.XPath(
        ".//{0}source".format(article_namespace
                              )
    )
    year_xpath = etree.XPath(
        ".//{0}year".format(article_namespace)
    )
    volume_xpath = etree.XPath(
        ".//{0}volume".format(article_namespace)
    )
    '''

    reference_sequence = 0
    for event, elem in context:

        reference_sequence = reference_sequence + 1

        # print(citer)
        # print(reference_sequence)
        temp_cite = cite_query.filter_by(citer=citer, reference_sequence=reference_sequence).first()
        # if temp_cite exists, then the program will continue
        if temp_cite:
            continue



        '''
        publication_type_list = publication_type_xpath(elem)
        if len(publication_type_list) is not 0:
            publication_type = publication_type_list[0]
            reference.type = publication_type

        article_titles = article_title_xpath(elem)
        if article_titles:
            article_title = article_titles[0]
            if article_title.text is not None:
                article_title_text = article_title.text
            else:
                article_title_text = ""

            for a_t in article_title:
                if a_t.text is None:
                    a_t.text = ""
                if a_t.tail is None:
                    a_t.tail = ""
                article_title_text = article_title_text + " " + a_t.text + " " + a_t.tail

            article_title_text = article_title_text.strip()
            article_title_text = re.sub(r"\s+", " ", article_title_text)
            reference.title = article_title_text
        # print(article_title)

        source_titles = source_title_xpath(elem)
        if source_titles:
            source_title = source_titles[0].text
            if source_title is None:
                source_title = ""
            source_title = source_title.strip()
            source_title = re.sub(r"\s+", " ", source_title)
            reference.source_title = source_title
        # print(source_title)

        years = year_xpath(elem)
        if years:
            year = years[0].text
            reference.pub_year = year[0:4]
        # print(year)

        volumes = volume_xpath(elem)
        if volumes:
            volume = volumes[0].text
            reference.volume = volume
        # print(volume)
        '''

        ref_id = ""
        ref_id_list = ref_id_xpath(elem)
        if ref_id_list:
            ref_id = ref_id_list[0]
        '''
        else:
            # print("ref_id_list is None, ref_id is 0, which is ridiculous.")
            continue
        '''
        pmid = ""
        pmid_list = pmid_xpath(elem)
        if pmid_list:
            pmid = pmid_list[0].text

        reference = Literature()
        temp_reference = literature_query.filter_by(pmid=pmid).first()
        if temp_reference:
            reference = temp_reference
        else:
            reference.pmid = pmid

        cite = Cite(
            citer=citer,
            cited=reference,
            local_reference_id=ref_id,
            reference_sequence=reference_sequence
        )
        session.add(cite)
        '''
        else:
            # Discard those references without pmid
            continue
        '''

        elem.clear()
        while elem.getprevious() is not None:
            del elem.getparent()[0]

    del context
    session.commit()


# To get the references with pmid
def get_reference_with_pmid(context, *arguments):
    # arguments = citer(literature)
    citer = arguments[0]

    session = Session()
    literature_query = session.query(Literature)

    # To find the ref-id, e.g. B1, B2
    ref_id_xpath = etree.XPath(
        "@id".format(article_namespace)
    )
    pmid_xpath = etree.XPath(
        ".//{0}pub-id[@pub-id-type='pmid']".format(
            article_namespace
        )
    )

    '''
    publication_type_xpath = etree.XPath(
        "@publication-type".format(article_namespace)
    )
    article_title_xpath = etree.XPath(
        ".//{0}article-title".format(article_namespace)
    )
    source_title_xpath = etree.XPath(
        ".//{0}source".format(article_namespace
                              )
    )
    year_xpath = etree.XPath(
        ".//{0}year".format(article_namespace)
    )
    volume_xpath = etree.XPath(
        ".//{0}volume".format(article_namespace)
    )
    '''

    reference_sequence = 0
    for event, elem in context:

        reference_sequence += 1
        reference = Literature()

        '''
        publication_type_list = publication_type_xpath(elem)
        if len(publication_type_list) is not 0:
            publication_type = publication_type_list[0]
            reference.type = publication_type

        article_titles = article_title_xpath(elem)
        if article_titles:
            article_title = article_titles[0]
            if article_title.text is not None:
                article_title_text = article_title.text
            else:
                article_title_text = ""

            for a_t in article_title:
                if a_t.text is None:
                    a_t.text = ""
                if a_t.tail is None:
                    a_t.tail = ""
                article_title_text = article_title_text + " " + a_t.text + " " + a_t.tail

            article_title_text = article_title_text.strip()
            article_title_text = re.sub(r"\s+", " ", article_title_text)
            reference.title = article_title_text
        # print(article_title)

        source_titles = source_title_xpath(elem)
        if source_titles:
            source_title = source_titles[0].text
            if source_title is None:
                source_title = ""
            source_title = source_title.strip()
            source_title = re.sub(r"\s+", " ", source_title)
            reference.source_title = source_title
        # print(source_title)

        years = year_xpath(elem)
        if years:
            year = years[0].text
            reference.pub_year = year[0:4]
        # print(year)

        volumes = volume_xpath(elem)
        if volumes:
            volume = volumes[0].text
            reference.volume = volume
        # print(volume)
        '''

        ref_id = ""
        ref_id_list = ref_id_xpath(elem)
        if len(ref_id_list) is not 0:
            ref_id = ref_id_list[0]
        '''
        else:
            # print("ref_id_list is None, ref_id is 0, which is ridiculous.")
            continue
        '''

        pmid_list = pmid_xpath(elem)
        if len(pmid_list) is not 0:
            pmid = pmid_list[0].text
            temp_reference = literature_query.filter_by(pmid=pmid).first()
            if temp_reference is not None:
                reference = temp_reference
            else:
                reference.pmid = pmid

            cite = Cite(
                citer=citer,
                cited=reference,
                local_reference_id=ref_id,
                reference_sequence=reference_sequence
            )
            session.add(cite)
        '''
        else:
            # Discard those references without pmid
            continue
        '''

        elem.clear()
        while elem.getprevious() is not None:
            del elem.getparent()[0]

    del context
    session.commit()
