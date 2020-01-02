from io import BytesIO
from lxml import etree
import re
import os
import html
# import en_core_web_md

from models import Literature
from models import Cite
from models import CiteParagraph
from models import CiteParagraphText
# from models import Citance
# from models import CitanceText

import manage

rootDir = manage.rootDir

# from models import CitationAnchorPosition
# from models import CiteMeme
# import pandas as pd

# basedir = os.path.abspath(os.path.dirname(__file__))
article_namespace = ""


# nlp = en_core_web_md.load()

# 'etc.' can be at the end of Sentence
# citation_context_abbreviations = ['cf.', 'e.g.', 'i.e.', 'viz.',
#                                   'vs.', 'et al.', 's.v.', 'v.', 'vs.',
#                                   'p.', 'pp.', 'Fig.', 'No.',
#                                   'ca.', 'N.B.', 'q.v.', 'sc.',
#                                   'c.', 'et seq.', 'ibid.', 'id.',
#                                   'op. cit.', 'loc. cit.']
# end_of_sentence_punctuation = ['.', '?', "!", "~~"]


def build_citation_index_for_each_pmc(infile):
    fname = os.path.basename(infile)
    pmc_uid = re.sub(r'\D', "", fname)

    temp_literature_with_pmc_uid = Literature.objects(pmc_uid=pmc_uid).first()

    if temp_literature_with_pmc_uid:
        if temp_literature_with_pmc_uid.fully_updated:
            print("Added and fully updated. Continue!")
            return
        else:
            print("Not fully updated. Update it.")
            temp_literature_with_pmc_uid.delete()

    literature = Literature()

    # start_time = time.time()

    try:
        with open(infile, "rb") as f:
            xml = f.read()
    except OSError:
        print(f"OSError for pmc_uid: {pmc_uid}.")
        return

    # end_time = time.time()
    # print(f"Open file {end_time - start_time} seconds.")

    # start_time = time.time()
    parser = etree.XMLParser(ns_clean=True)
    try:
        tree = etree.parse(BytesIO(xml), parser)
    except etree.XMLSyntaxError as e:
        print(e)

        return
    # end_time = time.time()
    # print(f"XMLParser {end_time - start_time} seconds.")

    root = tree.getroot()

    # To find the pmid (or pubmed id)
    pmid = article_id_find(root, "pmid")
    # print(pmid)

    # start_time = time.time()
    if pmid:
        # start_time_temp_literature_by_pmid = time.time()
        temp_literature_by_pmid = Literature.objects(pmid=pmid).first()
        # end_time_temp_literature_by_pmid = time.time()
        # f"if pmid {end_time_temp_literature_by_pmid - start_time_temp_literature_by_pmid} seconds."
        if temp_literature_by_pmid:
            literature = temp_literature_by_pmid
        else:
            literature.pmid = pmid
    # end_time = time.time()
    # print(f"if pmid {end_time - start_time} seconds.")

    literature.pmc_uid = pmc_uid
    literature.local_path = infile.replace(rootDir, "")
    literature.save()

    # start_time = time.time()
    # To get the reference info
    target_tag = 'ref'
    get_general_method(target_tag, infile, get_reference, literature)
    # end_time = time.time()
    # print(f"get_reference {end_time - start_time} seconds.")

    # start_time = time.time()
    # To get the citation context
    target_tag = 'p'
    get_general_method(target_tag, infile, get_citation_contexts_for_each_pmc, literature)
    # end_time = time.time()
    # print(f"get_citation_contexts_for_each_pmc {end_time - start_time} seconds.")

    # literature.fully_updated = True
    # literature.save()


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

    para_count = 0
    for event, elem in context:  # Iterate each paragraph.

        # start_time = time.time()
        para_count = para_count + 1
        bibr_list = bibr_xpath(elem)
        if len(bibr_list) == 0:
            bibr_list = ref_xpath(elem)
            if len(bibr_list) == 0:
                # print("len(bibr_list) is 0, maybe there are other bibr(ref)_xpath")
                continue

        # print(para_count)
        # print(len(bibr_list))

        tag_citation_anchor(bibr_list, citer)

        process_para_text(elem, citer)

        # end_time = time.time()
        # print(f"The {para_count} iterator costs {end_time - start_time} seconds.")

    del context  # end for
    # session.commit()


def tag_citation_anchor(bibr_list, citer):
    child_node_xpath = etree.XPath(
        "{0}child::*".format(article_namespace)
    )

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
                former_bibr_tail_match_is_not_none = \
                    re.search(r"~~\d+?~~\s*[–-]\s*$", former_bibr.tail) is not None

        if former_bibr_is_not_none and \
                former_bibr_tail_is_str and \
                former_bibr_tail_match_is_not_none:

            former_bibr.tail = re.sub(r"[–-]", "", former_bibr.tail)
            former_bibr.tail = re.sub(r"\s+", " ", former_bibr.tail)
            end_rid = (bibr.attrib["rid"])
            # print(end_rid)

            end_cite = Cite.objects(
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
                cite = Cite.objects(
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


def clean_para_text(para_text):
    para_text = re.sub(r"\n", " ", para_text)
    # delete the content between figure tag <fig>
    para_text = re.sub(r"<fig.*</fig>", " ", para_text)
    para_text = re.sub(r"<table-wrap.*</table-wrap>", " ", para_text)
    para_text = re.sub(r"<table.*</table>", " ", para_text)
    # delete the html tag
    para_text = re.sub(r"<.*?>", " ", para_text)
    # Replace the blank spaces with a single blank space
    para_text = re.sub(r"\s+", " ", para_text)
    # delete e.g. ~~, and ~~
    para_text = re.sub(r'~~[;,\s]*(and)?[;,\s]*~~', "~~~~", para_text)
    para_text = re.sub(r'\s?[\[(]?\s?~~', '~~', para_text)
    para_text = re.sub(r'~~\s?[\])]?', '~~', para_text)
    # para_text = para_text.replace(" .", ".")
    para_text = html.unescape(para_text)

    return para_text


def process_para_text(elem, citer):
    # the paragraph without outer tag
    para_text = etree.tostring(elem, encoding="unicode")
    para_text = clean_para_text(para_text)
    # print(para_text)

    search_objs = re.findall(r"~~\d+?~~", para_text)
    if not search_objs:
        return

    temp_text = text = re.sub(r"~~\d+?~~", "", para_text)
    cite_paragraph_text = CiteParagraphText(
        text=temp_text
    )
    cite_paragraph_text.save()

    for so in search_objs:
        reference_sequence = int(so.strip("~~"))
        cite = Cite.objects(
            citer=citer, reference_sequence=reference_sequence
        ).first()

        # The position for so
        position = para_text.find(so)
        # print(temp_text[0:position])

        cite_paragraph = CiteParagraph(
            position=position,
            cite=cite,
            citation_context_text=cite_paragraph_text
        )
        cite_paragraph.save()

        para_text = para_text.replace(so, "", 1)

    # para = nlp(para_text)
    # del para_text
    #
    # sentences = [sent.string.strip() for sent in para.sents]
    # # print(sentences)
    # del para
    # # length_of_sentences = len(sentences)
    #
    # citance_texts = []
    # while len(sentences) > 0:
    #
    #     sent_str = sentences.pop(0)
    #     if (len(sentences) is 0) and (sent_str is ""):
    #         break
    #     sent_str = sent_str.strip()
    #
    #     # The processing of next_sent
    #     # Whether to be included in the current sentence
    #     while 1 == 1:
    #
    #         if len(sentences) > 0:
    #             next_sent = sentences.pop(0)
    #         else:
    #             break
    #         next_sent = next_sent.strip()
    #
    #         sent_starts_without_uppercase_or_num = re.match(
    #             r'^[A-Z]|\d|\'|\"', next_sent
    #         ) is None
    #         sent_ends_with_citation_context_abbreviations = sent_str.endswith(
    #             tuple(citation_context_abbreviations)
    #         )
    #         sent_ends_without_end_of_sentence_punctuation = not sent_str.endswith(
    #             tuple(end_of_sentence_punctuation)
    #         )
    #         if sent_starts_without_uppercase_or_num or \
    #                 sent_ends_with_citation_context_abbreviations or \
    #                 sent_ends_without_end_of_sentence_punctuation:
    #             sent_str = sent_str + " " + next_sent
    #         else:
    #             sentences.insert(0, next_sent)
    #             break
    #
    #     # sent_str = clean_sent_str(sent_str)
    #     search_objs = re.findall(r"~~\d+?~~", sent_str)
    #
    #     citance_text = CitanceText()
    #     citance_text.save()
    #     if search_objs:
    #         # print(sent_str)
    #         # print(search_objs)
    #         reference_sequence_list = []
    #         for so in search_objs:
    #             # print(so.strip("~~"))
    #             # sent_str = re.sub(r"~~.*?~~", "", sent_str)
    #
    #             reference_sequence = int(so.strip("~~"))
    #             if reference_sequence in reference_sequence_list:
    #                 continue
    #             else:
    #                 reference_sequence_list.append(reference_sequence)
    #
    #             # print(reference_sequence_list)
    #             cite = Cite.objects(
    #                 citer=citer, reference_sequence=reference_sequence
    #             ).first()
    #             # print(cite)
    #             # print(reference_sequence)
    #             # The position for so
    #             position = sent_str.find(so)
    #             citance = Citance(
    #                 position=position,
    #                 cite=cite,
    #                 citation_context_text=citance_text
    #             )
    #             # session.add(citation_context)
    #             citance.save()
    #             # print("Hello!")
    #             sent_str = sent_str.replace(so, "")
    #
    #         del search_objs
    #         del reference_sequence_list
    #
    #     # sent_str = clean_sent_str(sent_str)
    #     citance_text.text = sent_str
    #     citance_text.save()
    #
    #     citance_texts.append(citance_text)
    #
    # cite_paragraph_text = CiteParagraphText()
    # cite_paragraph_text.citance_texts = citance_texts
    # cite_paragraph_text.save()

    elem.clear()
    while elem.getprevious() is not None:
        del elem.getparent()[0]


def clean_sent_str(sent_str):
    sent_str = re.sub(r'\[[\s|,|\d|;]*\]', ' ', sent_str.strip())
    sent_str = re.sub(r'\([\s|,|\d|;]*\)', ' ', sent_str.strip())
    sent_str = re.sub(r'\s+', ' ', sent_str.strip())
    sent_str = sent_str.replace(" .", ".")
    sent_str = sent_str.strip()

    return sent_str


# To get the references
# And this method excludes the title published year
# for later uses
def get_reference(context, *arguments):
    # arguments = citer(literature)
    citer = arguments[0]
    # print(citer)
    # session = Session()
    # literature_query = session.query(Literature)
    # cite_query = session.query(Cite)

    # To find the ref-id, e.g. B1, B2
    ref_id_xpath = etree.XPath(
        "@id".format(article_namespace)
    )
    pmid_xpath = etree.XPath(
        ".//{0}pub-id[@pub-id-type='pmid']".format(
            article_namespace
        )
    )

    reference_sequence = 0
    for event, elem in context:

        reference_sequence = reference_sequence + 1

        # print(citer)
        # print(reference_sequence)
        # start_time = time.time()
        temp_cite = Cite.objects(citer=citer, reference_sequence=reference_sequence).first()

        # if temp_cite exists, then the program will continue
        if temp_cite:
            continue

        ref_id = None
        ref_id_list = ref_id_xpath(elem)
        if ref_id_list:
            ref_id = ref_id_list[0]

        pmid = None
        pmid_list = pmid_xpath(elem)
        if pmid_list:
            pmid = pmid_list[0].text

        reference = Literature()
        if pmid:
            temp_reference = Literature.objects(pmid=pmid).first()
            if temp_reference:
                reference = temp_reference
            else:
                reference.pmid = pmid

        reference.save()

        cite = Cite(
            citer=citer,
            cited=reference,
            local_reference_id=ref_id,
            reference_sequence=reference_sequence
        )
        # session.add(cite)
        cite.save()

        elem.clear()
        while elem.getprevious() is not None:
            del elem.getparent()[0]

        # end_time = time.time()
        # print(f"The {reference_sequence} iterator costs {end_time-start_time} seconds.")

    del context
    # session.commit()
