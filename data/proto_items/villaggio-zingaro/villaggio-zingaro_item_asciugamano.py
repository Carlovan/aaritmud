# -*- coding: utf-8 -*-

#=DESCRIZIONE===================================================================

# CLOSE -> se l'asciugamano è vuoto si inibisce la chiusura
# PUT   -> se è la prima volta che si inserisce qualcosa si finge un insaccottamento
#          poi si mette la flag CONTAINER.CLOSED
# GET   -> se è l'ultimo item rimasto si finge di disfare la saccoccia e si toglie 
#          la flag CONTAINER.CLOSED
#

#=TO DO=========================================================================

#WEAR = è container?
#GET = se uno fa get è già container.. quante cose ci sono ancora solo 1 o più?
#WIELD = è container? contiene qualcosa? 
#EAT da definire.
#sul remove controllare i messaggi di svestizione (wield o mantel o marsupien)


#= IMPORT ======================================================================

import random
import math

from src.enums import CONTAINER, TO, PART, WEAPON
from src.part  import check_if_part_is_already_weared, get_part_descriptions #questa ultima cambia interfacciamento nella r111

from src.entitypes.wear import send_wear_messages


#= FUNZIONI ====================================================================

#def before_closed(player, asciugamano, reverse_target, container_only, behavioured):
#    if not asciugamano.is_empty():
#         return
#
#    player.act("Cerchi di chiudere $N, ma non trovi modo di farlo..", TO.ENTITY, asciugamano)
#    player.act("$n cerca di chiuderti, ma non sembra trovare modo di farlo.", TO.TARGET, asciugamano)
#    player.act("$n fa gesto di voler chiudere $N, ma gli è impossibile.", TO.OTHERS, asciugamano)
#    return True

def before_putting(player, target, asciugamano, direction, behavioured):
    print "asciugamano, before_putted trigger"
    if PART.BACK in asciugamano.wear_mode:
        player.act("Cerchi di %s $N %s $a, ma quest'ultimo non ti sembra un contenitore." % ("mettere", "in"), TO.ENTITY, target, asciugamano)
        player.act("$n cerca di %s $N %s $a, ma non riesce a trovare modo per farlo non essendo un contenitore." % ("mettere", "in"), TO.OTHERS, target, asciugamano)
        player.act("$n cerca di %s $a, ma avrà ben poca fortuna visto che non sei un contenitore." % "metterti", TO.TARGET, asciugamano, target)
        return True

    if (PART.WIELD or PART.HOLD) in asciugamano.wear_mode:
        player.act("Cerchi di %s $N %s $a, ma hai le $hands occupate." % ("mettere", "in"), TO.ENTITY, target, asciugamano)
        player.act("$n cerca di %s $N %s $a, ma non riesce a trovare modo per farlo non essendo un contenitore." % ("mettere", "in"), TO.OTHERS, target, asciugamano)
        player.act("$n cerca di %s $a, ma avrà ben poca fortuna visto che non sei un contenitore." % "metterti", TO.TARGET, asciugamano, target)
        return True

    if not asciugamano.is_empty():
        return

    asciugamano.weapon_type.category = WEAPON.MACE
    print ">>>asciugamano category: ", asciugamano.weapon_type.category
    player.act("Pieghi $N formando una saccoccia.", TO.ENTITY, asciugamano)
    player.act("$n ti maltratta conferendoti una forma poco naturale.", TO.TARGET, asciugamano)
    player.act("$n piega $N creando una saccoccia.", TO.OTHERS, asciugamano)


##def after_putting(player, target, asciugamano, behavioured):
##    if CONTAINER.CLOSED not in asciugamano.container_type.flags:
##        asciugamano.container_type.flags += CONTAINER.CLOSED


def before_get_from_location(player, item, asciugamano, behavioured):
    if (PART.WIELD or PART.HOLD) in asciugamano.wear_mode:
        player.act("Cerchi di %s $N %s $a, ma hai le $hands occupate." % ("prendere", "da"), TO.ENTITY, item, asciugamano)
        player.act("$n cerca di %s $N %s $a, ma non riesce a trovare modo per farlo non essendo un contenitore." % ("prendere", "da"), TO.OTHERS, item, asciugamano)
        player.act("$n cerca di %s $a, ma avrà ben poca fortuna visto che non sei un contenitore." % "prenderti", TO.TARGET, asciugamano, item)
        return True


def after_get_from_location(player, item, asciugamano, behavioured):
    if not asciugamano.is_empty():
        return

    asciugamano.weapon_type.category = WEAPON.WHIP    
    print ">>>asciugamano category: ", asciugamano.weapon_type.category

    player.act("Sciogli $N.", TO.ENTITY, asciugamano)
    player.act("$n ti riporta alla tua forma originaria.", TO.TARGET, asciugamano)
    player.act("$n scioglie $N.", TO.OTHERS, asciugamano)

    ##asciugamano.container_type.flags -= CONTAINER.CLOSED
    if PART.WAIST in asciugamano.wear_mode:
        asciugamano.wear_mode -= PART.WAIST


def before_weared(player, asciugamano, chosen_part, chosen_mode, behavioured):
    for content in asciugamano.iter_contains(use_reversed = True):
        already_weared_part, already_weared_possession = check_if_part_is_already_weared(player, PART.WAIST)
        if already_weared_part:
            player.act("Cerchi di %s $N %s ma hai già indosso $a." % ("indossare", already_weared_part), TO.ENTITY, asciugamano, already_weared_possession)
            player.act("$n cerca di %s $N %s ma ha già indosso $a." % ("indossare", already_weared_part), TO.OTHERS, asciugamano, already_weared_possession)
            return True

        asciugamano.wear_mode += PART.WAIST
        part_descriptions = {TO.TARGET: "alla vita", TO.OTHERS: "alla vita", TO.ENTITY: "alla vita"}
        player.act("%s $N %s." % ("Annodi", part_descriptions[TO.ENTITY]), TO.ENTITY, asciugamano)
        player.act("$n ti %s %s." % ("annoda", part_descriptions[TO.TARGET]), TO.TARGET, asciugamano)
        player.act("$n %s $N %s." % ("annoda", part_descriptions[TO.OTHERS]), TO.OTHERS, asciugamano)
        return True
    #asciugamano.wear_mode += PART.BACK
    #return True


def after_wielded(player, asciugamano, hands, behavioured):
    if asciugamano.weapon_type.category == WEAPON.WHIP:
        return

    total_wielded_weight = asciugamano.get_total_weight()
    print "asciugamano peso: ", total_wielded_weight
    damage = math.log(total_wielded_weight)
    print "asciugamano danno: ", damage
    damage = random.randint(damage / 1.5, damage * 1.5)
    print "asciugamano randanno: ", damage
    asciugamano.weapon_type.damage = damage
    print "wear_mode", asciugamano.wear_mode
