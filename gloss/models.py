from . import db

class Definition(db.Model):
    ''' Records of term definitions, along with some metadata.
    '''
    # Columns
    id = db.Column(db.Integer, primary_key=True)
    term = db.Column(db.Unicode())
    definition = db.Column(db.Unicode())
    defined_date = db.Column(db.DateTime())
    defined_user = db.Column(db.Unicode())

    def __repr__(self):
        return '<Term: {}, Definition: {}>'.format(self.term, self.definition)
