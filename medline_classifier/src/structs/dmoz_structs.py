from lxml import etree


DMOZ_DEFAULT_NS = 'http://dmoz.org/rdf/'
DMOZ_RDF_NS = 'http://www.w3.org/TR/RDF/'
DMOZ_ELEMENTS_NS = 'http://purl.org/dc/elements/1.0/'

DMOZ_DEFAULT = '{%s}' % DMOZ_DEFAULT_NS
DMOZ_RDF = '{%s}' % DMOZ_RDF_NS
DMOZ_ELEMENTS = '{%s}' % DMOZ_ELEMENTS_NS

DMOZ_NS_MAP = {
    None: DMOZ_DEFAULT_NS,
    'r': DMOZ_RDF_NS,
    'd': DMOZ_ELEMENTS_NS
}


class DMozPage:

    def __init__(self, url, title, description, topic_id, topic_name):
        self.url = url
        self.title = title
        self.description = description
        self.topic_id = str(topic_id)
        self.topic_name = topic_name

    def writeToXml(self, root):
        root.append(self.getXml())

    def getXml(self):
        page_el = etree.Element('ExternalPage', about=self.url)

        title_el = etree.Element(DMOZ_ELEMENTS + 'Title', nsmap=DMOZ_NS_MAP)
        title_el.text = self.title
        page_el.append(title_el)

        desc_el = etree.Element(DMOZ_ELEMENTS + 'Description', nsmap=DMOZ_NS_MAP)
        desc_el.text = self.description
        page_el.append(desc_el)

        topic_el = etree.Element('topic')
        topic_el.text = self.topic_name
        page_el.append(topic_el)

        return page_el


class DMozTopic:

    def __init__(self, topic_id, title, path_name, output_name, description):
        self.topic_id = str(topic_id)
        self.title = title
        self.path_name = path_name
        self.output_name = output_name
        self.description = description
        self.pages = []

        self._subtopic_map = {}

    def addSubtopic(self, subtopic):
        self._subtopic_map[subtopic.title] = subtopic

    def getSubtopicByTitle(self, title):
        if title not in self._subtopic_map:
            raise ValueError('Subtopic ' + title + ' doesn\'t exist!')
        return self._subtopic_map[title]

    def addPage(self, page):
        self.pages.append(page)

    def writeContentToXml(self, root):
        topic_el = etree.Element('Topic')
        topic_el.set(DMOZ_RDF + 'id', self.output_name)

        catid_el = etree.Element('catid')
        catid_el.text = self.topic_id

        topic_el.append(catid_el)

        root.append(topic_el)
        for i, page in enumerate(self.pages):
            link = etree.Element('link')
            link.set(DMOZ_RDF + 'resource', page.url)

            topic_el.append(link)
            page_el = page.getXml()

            if i == 0:
                priority_el = etree.Element('priority')
                priority_el.text = '1'
                page_el.append(priority_el)

            root.append(page_el)

        for subtopic in self._subtopic_map.values():
            subtopic.writeContentToXml(root)

    def writeStructureToXml(self, root):
        should_write = len(self.pages) > 0
        wrote_child_arr = []
        # write all the subtopics
        for subtopic in self._subtopic_map.values():
            wrote_child = subtopic.writeStructureToXml(root)
            should_write |= wrote_child
            wrote_child_arr.append(wrote_child)

        # if we wrote at least one subtopic then insert yourself at the begining
        if should_write:
            topic_el = etree.Element('Topic')
            topic_el.set(DMOZ_RDF + 'id', self.output_name)

            catid_el = etree.Element('catid')
            catid_el.text = self.topic_id
            topic_el.append(catid_el)

            title_el = etree.Element(DMOZ_ELEMENTS + 'Title', nsmap=DMOZ_NS_MAP)
            title_el.text = self.title
            topic_el.append(title_el)

            desc_el = etree.Element(DMOZ_ELEMENTS + 'Description', nsmap=DMOZ_NS_MAP)
            desc_el.text = self.description if self.description is not None else ''
            topic_el.append(desc_el)

            for subtopicN, subtopic in enumerate(self._subtopic_map.values()):
                if not wrote_child_arr[subtopicN]:
                    continue
                narrow_el = etree.Element('narrow')
                narrow_el.set(DMOZ_RDF + 'resource', subtopic.path_name)
                narrow_el.text = ''
                topic_el.append(narrow_el)
            # insert yourself at the beginning
            root.insert(0, topic_el)

        # return whether we wrote ourself
        return should_write


class DMozOntology:

    def __init__(self):
        self._topic_map = {}
        self._root_topic = DMozTopic(1, '', '', '', '')

        self._root_topic.addSubtopic(DMozTopic(2, 'Top', 'Top', 'Top/World', ''))

    def addPage(self, page):
        topic_id = page.topic_id
        topic_name = page.topic_name

        if not self.topicExists(topic_id):
            raise ValueError('Topic `' + topic_name + '` with ID `' + topic_id + '` does not exist!')

        topic = self.getTopic(topic_id)
        if topic.output_name != topic_name:
            raise ValueError('Invalid name of topic with ID `' + topic_id + '` should be `' + topic.output_name + '` but page has: ' + page.topic_name)

        topic.addPage(page)

    def getTopic(self, topic_id):
        return self._topic_map[str(topic_id)]

    def topicExists(self, topic_id):
        return str(topic_id) in self._topic_map

    def defineTopic(self, topic_id, topic_name, description):
        if self.topicExists(topic_id):
            return

        topic_id = str(topic_id)
        topic_path = topic_name.split('/')

        parent_topic = self._root_topic
        for subtopic_title in topic_path[0:-1]:
            parent_topic = parent_topic.getSubtopicByTitle(subtopic_title)

        topic = DMozTopic(topic_id, topic_path[-1], topic_name, topic_name, description)
        parent_topic.addSubtopic(topic)
        self._topic_map[topic_id] = topic

    def getContentXml(self):
        root = etree.Element('RDF', nsmap=DMOZ_NS_MAP)

        topic = self._root_topic
        topic.writeContentToXml(root)

        # for topic in self.topics:
        #     topic.writeContentToXml(root)
        return root

    def getStructureXml(self):
        root = etree.Element('RDF', nsmap=DMOZ_NS_MAP)

        topic = self._root_topic
        topic.writeStructureToXml(root)

        return root
