# -*- coding: utf-8 -*-

"""
Modulo per la gestione del comando che serve a risparmiare un'entit� sconfitta.
"""

#= IMPORT ======================================================================

from src.gamescript import check_trigger
from src.log        import log


#= FUNZIONI ====================================================================

def command_spare(entity, argument="", behavioured=False):
    # � possibile se il comando � stato deferrato
    if not entity:
        return False

    entity = entity.split_entity(1)

    # (TD) da inserire il check trigger

    # (TD)
    return True
#- Fine Funzione -


def get_syntax_template(entity):
    if not entity:
        log.bug("entity non � un parametro valido: %r" % entity)
        return ""

    # -------------------------------------------------------------------------

    return "spare\n"
#- Fine Funzione -
