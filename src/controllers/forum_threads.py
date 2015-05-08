# -*- coding: utf-8 -*-

"""
Modulo per la lista delle discussioni di un forum.
"""


#= IMPORT ======================================================================

import string

from src.config       import config
from src.enums        import TRUST
from src.forum_db     import forum_db
from src.log          import log
from src.web_resource import WebResource


#= CLASSI ======================================================================

class ForumThreadsPage(WebResource):
    TITLE = "Discussioni"

    ACCOUNT_MUST_EXIST_IN_GET  = False
    ACCOUNT_MUST_EXIST_IN_POST = False

    MINIMUM_TRUST_ON_GET  = TRUST.PLAYER
    MINIMUM_TRUST_ON_POST = TRUST.PLAYER

    PAGE_TEMPLATE = string.Template(open("src/views/forum_threads.view").read())

    def create_square(self, request, conn):
        return ""
    #- Fine Metodo -

    def render_GET(self, request, conn):
        if not "forum_code" in request.args:
            return "Nessun forum di cui guardare le discussioni."

        forum_code = request.args["forum_code"][0]
        for forum_table in forum_db.tables:
            if forum_table.code == forum_code:
                break
        else:
            return "Non esiste nessun forum dal codice %s." % forum_code

        mapping = {"mud_name"      : config.game_name,
                   "forum_code"    : forum_table.code,
                   "forum_name"    : forum_table.name,
                   "forum_descr"   : forum_table.descr,
                   "threads"       : self.create_forum_threads(forum_code)}
        return self.PAGE_TEMPLATE.safe_substitute(mapping)
    #- Fine Metodo -

    def create_forum_threads(self, forum_code):
        threads = []

        for thread in forum_db.iter_threads(forum_code):
            thread.append('''<tr class="block_text">''')
            thread.append('''</tr>''')

        return "".join(threads)
    #- Fine Metodo -
