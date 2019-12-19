from mongoengine import connect
from mongoengine import CASCADE
from mongoengine import BooleanField
from mongoengine import Document
from mongoengine import StringField
from mongoengine import ReferenceField
from mongoengine import IntField
from mongoengine import ListField

connect('citememe')


class Literature(Document):
    pmc_uid = StringField()
    pmid = StringField()
    local_path = StringField()
    fully_updated = BooleanField()

    meta = {
        'indexes': [
            {
                'fields': ['pmc_uid']
            },
            {
                'fields': ['pmid']
            }
        ]
    }


class Cite(Document):
    citer = ReferenceField('Literature', reverse_delete_rule=CASCADE)
    cited = ReferenceField('Literature', reverse_delete_rule=CASCADE)
    # The local_reference_id is the local reference id for the cited literature
    # in the citer e.g. #B16
    local_reference_id = StringField()
    reference_sequence = IntField()

    meta = {
        'indexes': [
            {
                'fields': ['citer']
            }
        ]
    }


class CitationContextText(Document):
    text = StringField()
    meta = {
        'allow_inheritance': True,
        'index_cls': False
    }


class CitanceText(CitationContextText):
    pass


class CiteParagraphText(Document):
    citance_texts = ListField(ReferenceField("CitanceText"))
    pass


class CitationContext(Document):
    # One CitationContext maps to only one Cite
    # And one Cite maps to many CitationContext
    position = IntField()
    cite = ReferenceField("Cite", reverse_delete_rule=CASCADE)
    citation_context_text = ReferenceField("CitationContextText", reverse_delete_rule=CASCADE)

    meta = {
        'allow_inheritance': True,
        'index_cls': False
    }


class Citance(CitationContext):
    pass

