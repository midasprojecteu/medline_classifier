import sys, traceback
from lxml import etree
from structs.medline_structs import MedlineArticle


class MedlineFileParser:

    def __init__(self, only_major_topics=False):
        self._articles = []
        self._only_major_topics = only_major_topics

    def getArticles(self):
        return self._articles

    def parse(self, fname):
        print 'parsing file: ' + fname

        tree = etree.parse(fname)
        # article_set = tree.getroot()
        articles = tree.findall('PubmedArticle')
        for article_el in articles:
            article = self._parseArticle(article_el)
            if article is not None:
                self._articles.append(article)

    def _parseArticle(self, article_el):
        pmid = None

        try:
            # URL is determined by PMID
            # e.g. https://www.ncbi.nlm.nih.gov/pubmed/$PMID
            # PMID is in MedlineCitation/PMID
            pmid_el = article_el.find('MedlineCitation/PMID')
            pmid = pmid_el.text

            # TITLE
            # title is in MedlineCitation/Article/ArticleTitle
            title_el = article_el.find('MedlineCitation/Article/ArticleTitle')
            title = title_el.text

            # ABSTRACT
            # there are multiple abstracts located in
            # MedlineCitation/Article/Abstract/AbstractText or
            # MedlineCitation/Article/OtherAbstract/AbstractText
            abstract_el = article_el.find('MedlineCitation/Article/Abstract')
            if (abstract_el is None):
                abstract_el = article_el.find('MedlineCitation/OtherAbstract')
            # abstract_el = getFirstElement(abstract_els)
            if abstract_el is None:
                return None
                # raise ValueError('Could not find the abstract of article:\n' + etree.tostring(article_el))

            abstract = ' '.join([text_el.text for text_el in abstract_el.iterchildren('AbstractText')
                                 if text_el.text is not None])

            if len(abstract) == 0:
                return None

            # TOPIC INFORMATION
            topic_ids = []
            mesh_heading_els = article_el.findall('MedlineCitation/MeshHeadingList/MeshHeading')

            if mesh_heading_els is None or len(mesh_heading_els) == 0:
                return None

            for heading_el in mesh_heading_els:
                descriptor_el = heading_el.find('DescriptorName')
                descriptor_attrs = descriptor_el.attrib
                major_indicator = descriptor_attrs['MajorTopicYN']

                if self._only_major_topics and major_indicator == 'N':
                    continue

                if self._only_major_topics and major_indicator != 'Y':
                    raise ValueError('Invalid major topic indicator: ' + major_indicator)

                topic_id = descriptor_attrs['UI']
                topic_ids.append(topic_id)

            return MedlineArticle(pmid, title, abstract, topic_ids)
        except:
            print 'exception while parsing MEDLINE article with PMID: ' + str(pmid)
            traceback.print_exc(file=sys.stdout)
            exit(1)
