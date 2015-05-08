﻿# -*- coding: utf-8 -*-

"""
Modulo per la gestione del comando unbolt.
"""

#= IMPORT ======================================================================

from src.command    import get_command_syntax
from src.config     import config
from src.enums      import CONTAINER, DIR, DOOR, OPTION, TO
from src.exit       import get_destination_room_from_door
from src.gamescript import check_trigger
from src.log        import log


#= COSTANTI ====================================================================

VERBS = {"infinitive" : "[darkolivegreen]svincolare[close]",
         "you2"       : "[darkolivegreen]svincolarti[close]",
         "you"        : "[darkolivegreen]svincoli[close]",
         "it"         : "[darkolivegreen]svincola[close]"}


#= FUNZIONI ====================================================================

def command_unbolt(entity, argument="", verbs=VERBS, behavioured=False, container_only=False):
    if not verbs:
        log.bug("verbs non è un parametro valido: %r" % verbs)
        return False

    # -------------------------------------------------------------------------

    # È possibile se il comando è stato deferrato
    if not entity:
        return False

    entity = entity.split_entity(1)

    if not argument:
        entity.send_output("Che cosa vorresti %s?" % verbs["infinitive"])
        if entity.IS_PLAYER and OPTION.NEWBIE in entity.account.options:
            syntax = get_command_syntax(entity, "command_unbolt")
            entity.send_output(syntax)
        return False

    target = entity.find_entity_extensively(argument, inventory_pos="last")
    if not target or (target.is_secret_door() and len(argument) < config.min_secret_arg_len):
        entity.act("Cerchi di %s %s che però non riesci a trovare." % (verbs["infinitive"], argument), TO.ENTITY)
        entity.act("$n cerca qualcosa che non sembra riuscire a trovare.", TO.OTHERS)
        return False

    # Nel caso che la porta, nel lato della stanza in cui si trova entity, sia
    # già aperta prova a controllare l'eventuale porta dall'altro lato, ma solo
    # se si tratta di una porta asincrona
    if (target.door_type and DOOR.CLOSED not in target.door_type.flags
    and DOOR.ASYNCHRONOUS in target.door_type.flags):
        reverse_target = entity.find_entity_extensively(argument, direct_search=False)
        if reverse_target:
            target = reverse_target

    if not target.door_type and not target.container_type:
        if entity == target:
            entity.act("Cerchi di %s te stess$o, senza molto successo..." % verbs["infinitive"], TO.ENTITY)
            entity.act("$n cerca di %s sé stess$o, senza molto successo..." % verbs["infinitive"], TO.OTHERS)
        else:
            entity.act("Cerchi di %s $N, ma non trovi modo di farlo." % verbs["infinitive"], TO.ENTITY, target)
            entity.act("$n cerca di %s $N, ma non sembra trovare modo di farlo." % verbs["infinitive"], TO.OTHERS, target)
            entity.act("$n cerca di %s, ma non sembra trovare modo di farlo." % verbs["you2"], TO.TARGET, target)
        return False

    if container_only and not target.container_type and target.door_type:
        entity.act("Cerchi di %s $N, ma non sembra essere un contenitore." % verbs["infinitive"], TO.ENTITY, target)
        entity.act("$n cerca di %s $N, ma non sembra essere un contenitore." % verbs["infinitive"], TO.OTHERS, target)
        entity.act("$n cerca di %s, ma non sembra essere un contenitore." % verbs["you2"], TO.TARGET, target)
        return False

    if container_only:
        entitype_priority = "container"
    else:
        entitype_priority = target.get_open_close_priority()
    if entitype_priority != "door" and entitype_priority != "container":
        log.bug("entitype_priority è un valore errato: %s" % entitype_priority)
        return False

    if entitype_priority == "door":
        if not target.is_hinged():
            entity.act("Come puoi %s $N se si trova fuori dai cardini?" % verbs["infinitive"], TO.ENTITY, target)
            entity.act("$n cerca di %s $N, sarà un po' dura visto che non si trova sui cardini." % verbs["infinitive"], TO.OTHERS, target)
            entity.act("$n cerca di %s, sarà un po' dura visto che non ti trovi sui cardini..." % verbs["you2"], TO.TARGET, target)
            return False

        if DOOR.BASHED in target.door_type.flags:
            entity.act("Cerchi di %s $N, ma l$O trovi sfondat$O." % verbs["infinitive"], TO.ENTITY, target)
            entity.act("$n cerca di %s $N, ma l$O trova sfondat$O." % verbs["infinitive"], TO.OTHERS, target)
            entity.act("$n cerca di %s, ma ti trova sfondat$O." % verbs["you2"], TO.TARGET, target)
            return False

        entitype = target.door_type
        # (TD) queste flag spostarle nei vari entitype
        closed_flag   = DOOR.CLOSED
        locked_flag   = DOOR.LOCKED
        boltable_flag = DOOR.BOLTABLE
        bolted_flag   = DOOR.BOLTED

        destination, direction = get_destination_room_from_door(entity, target)
        if destination:
            reverse_destination = destination.get_destination(direction.reverse_dir)
            if reverse_destination:
                reverse_destination_room = reverse_destination.get_room()
                if entity.location != reverse_destination_room:
                    destination = None
                    direction = DIR.NONE
    else:
        entitype = target.container_type
        closed_flag   = CONTAINER.CLOSED
        locked_flag   = CONTAINER.LOCKED
        boltable_flag = CONTAINER.BOLTABLE
        bolted_flag   = CONTAINER.BOLTED
        destination = None  # (TD) supportarlo
        direction = None

    if entitype_priority == "container" and CONTAINER.BOLTABLE  not in entitype.flags:
        entity.act("Cerchi di %s $N, ma ti è impossibile." % verbs["infinitive"], TO.ENTITY, target)
        entity.act("$n cerca di %s $N, ma $gli è impossibile" % verbs["infinitive"], TO.OTHERS, target)
        if destination:
            entity.act("Qualcuno, dall'altra parte, cerca di %s $N, ma gli è impossibile." % (
                verbs["infinitive"]), TO.OTHERS, target, send_to_location=destination)
        entity.act("$n cerca di %s, ma $gli è impossibile." % verbs["you2"], TO.TARGET, target)
        return False

    if boltable_flag in entitype.flags and bolted_flag not in entitype.flags:
        entity.act("Cerchi di %s $N, ma l$O trovi già svincolat$O." % verbs["infinitive"], TO.ENTITY, target)
        entity.act("$n cerca di %s $N, ma l$O trova già svincolat$O." % verbs["infinitive"], TO.OTHERS, target)
        if destination:
            entity.act("Qualcuno, dall'altra parte, cerca di %s $N %s, ma l$O trova già svincolat$O." % (
                verbs["infinitive"], direction.reverse_dir.to_dir2), TO.OTHERS, target, send_to_location=destination)
        entity.act("$n cerca di %s, ma ti trova già svincolat$O." % verbs["you2"], TO.TARGET, target)
        return False

###    if locked_flag in entitype.flags:
###        entity.act("Cerchi di %s $N, ma scopri che è già chius$O a chiave." % verbs["infinitive"], TO.ENTITY, target)
###        entity.act("$n cerca di %s $N, scoprendo che è già chius$O a chiave." % verbs["infinitive"], TO.OTHERS, target)
###        if destination:
###            entity.act("Qualcuno, dall'altra parte, cerca di %s $N %s, scoprendo che è già chius$O a chiave." % (
###                verbs["infinitive"], direction.reverse_dir.to_dir2), TO.OTHERS, target, send_to_location=destination)
###        entity.act("$n cerca di %s , scoprendo che sei già chius$O a chiave." % verbs["you2"], TO.TARGET, target)
###        return False

##
##    if bolted_flag in entitype.flags:
##        entity.act("Cerchi di %s $N, ma scopri che è chius$O con $a." % verbs["infinitive"], TO.ENTITY, target, entitype.bolt)
##        entity.act("$n cerca di %s $N, scoprendo che è chius$O con $a." % verbs["infinitive"], TO.OTHERS, target, entitype.bolt)
##        if destination:
##            entity.act("Qualcuno, dall'altra parte, cerca di %s $N %s, scoprendo che è chius$O con $a." % (
##                verbs["infinitive"], direction.reverse_dir.to_dir2), TO.OTHERS, target, entitype.bolt, send_to_location=destination)
##        entity.act("$n cerca di %s, scoprendo che sei chius$O con $a." % verbs["you2"], TO.TARGET, target, entitype.bolt)
##        return False

#    key = None
#    if entitype.key_code:
#        for generic_key in entity.iter_contains():
#            if not entity.can_see(generic_key):
#                continue
#            if generic_key.prototype.code == entitype.key_code:
#                key = entitype.key_code
#
#    if not entitype.key_code or not key:
#        entity.act("Cerchi di %s $N, ma non riesci a trovarne la chiave." % verbs["infinitive"], TO.ENTITY, target)
#        entity.act("$n cerca di %s $N, armeggindo inutilmente." % verbs["infinitive"], TO.OTHERS, target)
#        entity.act("$n cerca di %s, ma non vi riesce perché non ha la chiave." % verbs["you2"], TO.TARGET, target)
#        if destination:
#            entity.act("Qualcuno, dall'altra parte, armeggia inutilmente sulla serratura ma non riesce a %s $N %s." % (
#                verbs["infinitive"], direction.reverse_dir.to_dir2), TO.OTHERS, target, send_to_location=destination)
#        return False

    reverse_target = None
    if destination and entitype_priority == "door" and DOOR.ASYNCHRONOUS not in entitype.flags:
        reverse_target = target.location.get_door(direction, direct_search=False)

    force_return = check_trigger(entity, "before_unbolt", entity, target, reverse_target, behavioured)
    if force_return:
        return True
    force_return = check_trigger(target, "before_unbolted", entity, target, reverse_target, behavioured)
    if force_return:
        return True

    entitype.send_unbolt_messages(entity, target, verbs, direction, destination)
    entitype.flags -= bolted_flag
    if reverse_target and reverse_target.door_type:
        reverse_target.door_type.flags -= bolted_flag

    # Serve a cambiare lo status della porta o del contenitore tramite il
    # meccanismo di repop allo stato originario
    if target.repop_later:
        target.deferred_repop = target.repop_later.defer_check_status()
    if reverse_target and reverse_target.repop_later:
        reverse_target.deferred_repop = reverse_target.repop_later.defer_check_status()

    # Dona un po' di esperienza ai giocatori che hanno svincolato per la prima
    # volta l'entità
    if entity.IS_PLAYER:
        if target.prototype.code in entity.unbolted_entities:
            entity.unbolted_entities[target.prototype.code] += 1
        else:
            entity.unbolted_entities[target.prototype.code] = 1
            reason = "per aver svincolato per la prima volta %s" % target.get_name(looker=entity)
            entity.give_experience(target.level*10, reason=reason)

    force_return = check_trigger(entity, "after_unbolt", entity, target, reverse_target, behavioured)
    if force_return:
        return True
    force_return = check_trigger(target, "after_unbolted", entity, target, reverse_target, behavioured)
    if force_return:
        return True

    return True
#- Fine Funzione -


def get_syntax_template(entity):
    if not entity:
        log.bug("entity non è un parametro valido: %r" % entity)
        return ""

    # -------------------------------------------------------------------------

    return "unbolt <porta o contenitore a cui aprire il chiavistello>\n"
#- Fine Funzione -
