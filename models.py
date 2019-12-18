from mongoengine import connect
from mongoengine import Document
from mongoengine import StringField

connect('citememe')


class User(Document):
    email = StringField(required=True)
    first_name = StringField(max_length=50)
    last_name = StringField(max_length=50)

# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from sqlalchemy.orm import scoped_session
# from sqlalchemy import (Column, Integer, String, Text, ForeignKey, Boolean, Date)
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import relationship, backref
# import os
#
# basedir = os.path.abspath(os.path.dirname(__file__))
# # SQLALCHEMY_DATABASE_URI = 'postgresql://text:1@localhost/text'
# # SQLALCHEMY_DATABASE_URI = 'postgresql://text:1@localhost/text'
# SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'citememe.sqlite')
# # SQLALCHEMY_DATABASE_URI = 'postgresql://citememe:VojuGumo6%Vuve@localhost/citememe'
#
# engine = create_engine(SQLALCHEMY_DATABASE_URI)
# session_factory = sessionmaker(bind=engine)
# Session = scoped_session(session_factory)
# session = Session()
#
# Base = declarative_base()
#
#
# class Cite(Base):
#     __tablename__ = 'cites'
#     id = Column(Integer, primary_key=True)
#     citer_id = Column(Integer, ForeignKey('literatures.id'))
#     cited_id = Column(Integer, ForeignKey('literatures.id'), index=True)
#     # The local_reference_id is the local reference id for the cited literature
#     # in the citer
#     # e.g. #B16
#     local_reference_id = Column(String(256))
#     reference_sequence = Column(Integer)
#     # timestamp is replaced by the pub_date from the citer
#
#     citation_contexts = relationship('CitationContext',
#                                      backref='cite',
#                                      lazy='dynamic',
#                                      cascade='all,delete-orphan')
#     citememes = relationship('Citememe', backref='cite', lazy='dynamic')
#
#     def __repr__(self):
#         return '<Cite %r>' % self.id
#
#
# # class CitationAnchorPosition(Base):
# #     __tablename__ = 'citationanchorpositions'
# #     id = Column(Integer, primary_key=True)
# #     position = Column(Integer)
# #     citationcontext_id = Column(Integer, ForeignKey('citationcontexts.id'))
# #     citationcontexttext_id = Column(Integer, ForeignKey('citationcontexttexts.id'))
#
#
# class CitationContext(Base):
#     __tablename__ = 'citationcontexts'
#     id = Column(Integer, primary_key=True)
#     cite_id = Column(Integer, ForeignKey('cites.id'))
#     citationcontexttext_id = Column(Integer, ForeignKey('citationcontexttexts.id'))
#     # citation_anchor_positions = relationship('CitationAnchorPosition',
#     #                                          backref='citationanchorposition',
#     #                                          lazy='dynamic',
#     #                                          cascade='all,delete-orphan')
#
#
# class CitationContextText(Base):
#     __tablename__ = 'citationcontexttexts'
#     id = Column(Integer, primary_key=True)
#     text = Column(Text)
#     citation_contexts = relationship('CitationContext',
#                                      backref='citationcontexttext',
#                                      lazy='dynamic',
#                                      cascade='all,delete-orphan')
#     # citation_anchor_positions = relationship('CitationAnchorPosition',
#     #                                          backref='citationanchorposition',
#     #                                          lazy='dynamic',
#     #                                          cascade='all,delete-orphan')
#
#     # citememes = relationship('Citememe', backref='citationcontexttext', lazy='dynamic')
#
#     # def __repr__(self):
#     #     return '<CitationContextText %r>' % self.id
#
#
# class Citememe(Base):
#     __tablename__ = 'citememes'
#     id = Column(Integer, primary_key=True)
#     text = Column(String(1024))
#
#     cite_id = Column(Integer, ForeignKey('cites.id'))
#
#     # citationcontexttext_id = Column(Integer, ForeignKey('citationcontexttexts.id'))
#
#     def __repr__(self):
#         return '<Citememe %r>' % self.text
#
#
# class Literature(Base):
#     __tablename__ = 'literatures'
#     id = Column(Integer, primary_key=True)
#     pmc_uid = Column(String(50), unique=True)
#     pmid = Column(String(50), index=True, unique=True)
#     doi = Column(String(50), unique=True)
#     # research_gate_publication_id = Column(String(50), unique=True)
#     local_path = Column(String(512))
#     # title = Column(Text)
#     # pub_date = Column(Date)
#     # pub_year = Column(String(50))
#     # The @updated_by_pmc = True means the info in the literature has been updated_by_pmc
#     # from pmc or pubmed
#     # updated_by_pmc = Column(Boolean)
#     # The type for the literature, for example journal, book
#     # type = Column(String(50))
#     # The source id ,and for the journal, journal id when journal-id-type =
#     # "nlm-ta"
#     source_id = Column(String(50))
#     # The source title, and for the journal, the full name for the journal
#     # title
#     source_title = Column(String(512))
#     # volume = Column(String(256))
#     # if_citation_context_gotten = Column(Boolean)
#
#     cited = relationship('Cite',
#                          foreign_keys=[Cite.citer_id],
#                          backref=backref('citer', lazy='joined'),
#                          lazy='dynamic',
#                          cascade='all,delete-orphan')
#     citer = relationship('Cite',
#                          foreign_keys=[Cite.cited_id],
#                          backref=backref('cited', lazy='joined'),
#                          lazy='dynamic',
#                          cascade='all,delete-orphan')
#
#     def cite(self, literature):
#         if not self.is_citing(literature):
#             c = Cite(citer=self, cited=literature)
#             session.add(c)
#
#     def uncite(self, literature):
#         c = self.cited.filter_by(cited_id=literature.id).first()
#         if c:
#             session.delete(c)
#
#     def is_citing(self, literature):
#         return self.cited.filter_by(
#             cited_id=literature.id).first() is not None
#
#     def is_cited_by(self, literature):
#         return self.citers.filter_by(
#             citer_id=literature.id).first() is not None
#
#     def __repr__(self):
#         return '<Literature %r>' % self.pmc_uid
#
#
# Base.metadata.create_all(engine)
