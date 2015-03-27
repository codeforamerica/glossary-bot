from . import gloss as app
from . import db

@app.route('/', methods=['GET', 'POST'])
def index():
    return 'Glossary Bot Reporting for Duty!'
