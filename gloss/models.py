from . import db
from sqlalchemy.dialects.postgresql import TSVECTOR
from datetime import datetime

class Definition(db.Model):
    ''' Records of term definitions, along with some metadata
    '''
    __tablename__ = 'definitions'
    # Columns
    id = db.Column(db.Integer, primary_key=True)
    creation_date = db.Column(db.DateTime(), default=datetime.utcnow)
    term = db.Column(db.Unicode(), index=True)
    definition = db.Column(db.Unicode())
    user_name = db.Column(db.Unicode())
    tsv_search = db.Column(TSVECTOR)

    def __repr__(self):
        return '<Term: {}, Definition: {}>'.format(self.term, self.definition)

class Interaction(db.Model):
    ''' Records of interactions with Glossary Bot
    '''
    __tablename__ = 'interactions'
    # Columns
    id = db.Column(db.Integer, primary_key=True)
    creation_date = db.Column(db.DateTime(), default=datetime.utcnow)
    user_name = db.Column(db.Unicode())
    term = db.Column(db.Unicode())
    action = db.Column(db.Unicode(), index=True)

    def __repr__(self):
        return '<Action: {}, Date: {}>'.format(self.action, self.creation_date)
