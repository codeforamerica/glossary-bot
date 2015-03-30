from . import gloss as app

@app.app_errorhandler(401)
def unauthorized(e):
    return 'Error: Unauthorized', 401

@app.app_errorhandler(404)
def page_not_found(e):
    return 'Error: Page Not Found', 404
