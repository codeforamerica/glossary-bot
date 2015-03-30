from . import db

class Definition(db.Model):
    ''' Records of term definitions, along with some metadata
    '''
    __tablename__ = 'definitions'
    # Columns
    id = db.Column(db.Integer, primary_key=True)
    term = db.Column(db.Unicode())
    definition = db.Column(db.Unicode())
    defined_date = db.Column(db.DateTime())
    defined_user = db.Column(db.Unicode())

    def __repr__(self):
        return '<Term: {}, Definition: {}>'.format(self.term, self.definition)

class Exchange(db.Model):
    ''' Records of interactions with Glossary Bot
    '''
    __tablename__ = 'exchanges'
    # Columns
    id = db.Column(db.Integer, primary_key=True)
    exchange_date = db.Column(db.DateTime())
    exchange_user = db.Column(db.Unicode())
    exchange_term = db.Column(db.Unicode())
    action = db.Column(db.Unicode())

    def __repr__(self):
        return '<Action: {}, Date: {}>'.format(self.action, self.exchange_date)
