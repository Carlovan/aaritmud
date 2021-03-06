# -*- coding: utf-8 -*-

#= IMPORT ======================================================================

import random
import re

from src.database import database
from src.defer    import defer, defer_random_time, defer_if_possible
from src.enums    import ENTITYPE, RACE, SECTOR, TO
from src.log      import log
from src.utility  import is_same

from src.commands.command_drop    import command_drop
from src.commands.command_eat     import command_eat
from src.commands.command_emote   import command_emote
from src.commands.command_look    import command_look
from src.commands.command_murmur  import command_murmur
from src.commands.command_say     import command_say
from src.commands.command_yell    import command_yell
from src.commands.command_whisper import command_whisper


#= COSTANTI ====================================================================

# Questo regex pattern serve a rimuovere tutti i caratteri non alfabetici
# o spazi da una stringa e la vocale accentata 'ì' di un eventuale "sì"
ALFA_ONLY_PATTERN = re.compile("[^a-zA-Zì ]+")


#= FUNZIONI ====================================================================

def on_booting(idrusa):
    print "on_booting dell'idrusa", idrusa

    # Concettualmente al riavvio del gioco è meglio raddoppiare i tempi di
    # reset in maniera tale che il giocatore abbia il tempo di "riprendersi"
    deferred_reset = defer_random_time(400, 600, reset_farfalla_quest, idrusa)
    idrusa.specials["deferred_reset"] = deferred_reset
    idrusa.specials["before_lookeding_me"] = True
#- Fine Funzione -


def on_shutdown(idrusa):
    # Cancella i valori di specials da non rendere persistenti
    delete_deferred_reset(idrusa)
#- Fine Funzione -


def before_looked(entity, idrusa, descr, detail, use_examine, behavioured):
    if "before_lookeding_me" not in idrusa.specials or idrusa.specials["before_lookeding_me"] == True:
        idrusa.specials["before_lookeding_me"] = False
        defer(100, reset_look, idrusa)
        start_idrusa_farfalla_quest(entity, detail, idrusa)
#- Fine Funzione


def reset_look(idrusa):
    # E' normale visto che la funzione è deferrata
    if not idrusa:
        return
    idrusa.specials["before_lookeding_me"] = True
#- Fine Funzione


def start_idrusa_farfalla_quest(player, to_room, idrusa):
    # La quest deve iniziare solo per i giocatori
    if not player.IS_PLAYER:
        idrusa.specials["before_lookeding_me"] = True
        return

    # Idrusa tra qualche secondo proporrà al giocatore di aiutarla
    defer_if_possible(2, 4, idrusa, player, beg_the_player, idrusa, player)
#- Fine Funzione -


def beg_the_player(idrusa, player):
    idrusa.specials["before_lookeding_me"] = False
    idrusa.specials["quest_status"] = "domanda"
    idrusa.specials["player_code"] = player.code

    to_say = "a %s *supponente* sei qui forse per accedere al regno di Klirbe?" % player.code
    command_say(idrusa, to_say)
    
    # Dopo un po' chiede nuovamente al giocatore di rispondere alla sua
    # richiesta di aiuto nel qual caso che il giocatore non abbia afferrato
    # l'indizio di quello che deve fare
    defer_if_possible(15, 30, idrusa, player, ask_for_answer, idrusa, player)

    # L'idrusa non starà ad aspettare in eterno che il giocatore si decida a
    # iniziare la quest, se dopo un po' di tempo lo status della quest non
    # è cambiato allora gli specials vengono azzerati
    deferred_reset = defer_random_time(60, 90, reset_farfalla_quest, idrusa)
    idrusa.specials["deferred_reset"] = deferred_reset
#- Fine Funzione -


def ask_for_answer(idrusa, player):
    # Controlla se la quest non sia già stata resettata oppure avanzata
    if "quest_status" not in idrusa.specials or idrusa.specials["quest_status"] != "domanda":
        return

    to_say = "a %s *supponente* L'incoscienza non ti manca di certo! Lo vuoi davvero?" % player.code
    command_say(idrusa, to_say)
#- Fine Funzione -


# Da notare che qui non è stato utilizzato il trigger after_listen_rpg_channel,
# che invece funziona per tutti i canali rpg, questo funziona ovviamente
# solo con il canale say.
def after_listen_say(idrusa, speaker, target, phrase, behavioured):
    if not speaker.IS_PLAYER:
        return

    # Controlla se la quest non sia già stata resettata oppure avanzata
    if "quest_status" not in idrusa.specials or idrusa.specials["quest_status"] != "domanda":
        return

    # Ricava la frase ripulita dalla punteggiatura e non continua la quest fino
    # a che il giocatore non dice: sì
    phrase = ALFA_ONLY_PATTERN.sub("", phrase)
    if not is_same(phrase, "si"):
        return

    # Guarda il giocatore che ha risposto
    command_look(idrusa, speaker.code)

    # Ignora coloro che hanno risposto ma che non hanno avviato la quest
    quest_player_code = idrusa.specials["player_code"]
    if speaker.code != quest_player_code:
        quest_player = database["players"][quest_player_code]
        # Ricava il nome o la short per come lo vede idrusa
        to_say = "a %s No, non la tua risposta attendo ma di %s." % (speaker.code, quest_player.get_name(looker=idrusa))
        command_say(idrusa, to_say)
        return

    # Visto che il secondo stadio della missione si sta attivando cancella il
    # precedente reset che è meglio che sia reimpostato a fine funzione
    delete_deferred_reset(idrusa)

    # Facciamo avanzare lo stato della quest
    idrusa.specials["quest_status"] = "cerca"

    # Descriviamo quello che vogliamo
    to_say = "a %s *in tono grave* L'accesso ti verrà indicato solo se porterai una farfalla!" % speaker.code
    defer_if_possible(1, 2, idrusa, speaker, command_say, idrusa, to_say)

    # Ecco qui, qui viene impostata la durata media della quest, ovvero quanto
    # idrusa attenderà che il giocatore gli porti la farfalla
    deferred_reset = defer_random_time(200, 300, reset_farfalla_quest, idrusa)
    idrusa.specials["deferred_reset"] = deferred_reset
#- Fine Funzione -


# Da notare i return True per evitare di accettare una qualsiasi cosa
def before_giving(player, farfalla, idrusa, direction, behavioured):
    if not player.IS_PLAYER:
        to_say = "a %s *concentrato* No grazie. Non accetto nulla da chicchessia." % player.get_numbered_keyword()
        defer_if_possible(1, 2, command_say, idrusa, to_say)
        return True

    command_look(idrusa, player.code)

    # Idrusa non ha iniziato a dare nessuna quest
    if "quest_status" not in idrusa.specials:
        to_say = "a %s *impensierito* No grazie. Ora non sono interessata." % player.code
        defer_if_possible(1, 2, idrusa, player, command_say, idrusa, to_say)
        return True

    quest_player_code = idrusa.specials["player_code"]
    quest_player = database["players"][quest_player_code]
    quest_player_name = quest_player.get_name(looker=idrusa)

    quest_status = idrusa.specials["quest_status"]
    if quest_status == "domanda":
        to_say = "a %s *concentrato* No grazie. Sto attendendo che %s mi risponda." % (
            player.code, quest_player_name)
        defer_if_possible(1, 2, idrusa, player, command_say, idrusa, to_say)
        return True

    # Controlla che l'entità che dà sia il giocatore della quest
    if player.code != quest_player_code:
        to_say = "a %s No grazie. Sto aspettando che %s mi porti ciò che deve." % (
            player.code, quest_player_name)
        defer_if_possible(1, 2, idrusa, player, command_say, idrusa, to_say)
        return True

    # Controlla se l'oggetto dato sia una farfalla
    if not farfalla.race == RACE.BUTTERFLY:
        to_say = "a %s *critica* Stai cercando di muovermi a pena o di turlupinarmi?" % quest_player_code
        defer_if_possible(1, 2, idrusa, player, command_say, idrusa, to_say)
        return True
    else:
        idrusa.specials["quest_status"] = "completa"
        # Ora che la quest è completa ne blocca un eventuale reset
        delete_deferred_reset(idrusa)

        to_yell = "a %s *scortese* Pensavo avessi desistito ormai!" % quest_player_code
        defer_if_possible(1, 2, idrusa, player, command_yell, idrusa, to_yell)
        to_say = "a %s *con un largo sorriso di scherno* La via per Klirbe non è però accessibile per te..." % quest_player_code
        defer_if_possible(1, 2, idrusa, player, command_say, idrusa, to_say)
        to_say = "a %s In compenso hai fatto un po' d'esperienza!" % quest_player_code
        defer_if_possible(1, 2, idrusa, player, command_say, idrusa, to_say)
        player.experience += 100

        # Tra un po' di tempo si potranno cercare farfalle
        defer_random_time(3600, 4800, its_farfalla_time, idrusa)
#- Fine Funzione -


def its_farfalla_time(idrusa):
    reset_farfalla_quest(idrusa)
    command_say(idrusa, "*irruente come si conviene alla sua razza* Qualcun altro si vuole cimentare?")
#- Fine Funzione -


def reset_farfalla_quest(idrusa):
    # E' normale poiché questa funzione viene anche deferrata
    if not idrusa:
        return

    player_is_here = False
    quest_player_code = ""
    idrusa.specials["before_lookeding_me"] = True
    if "player_code" in idrusa.specials:
        quest_player_code = idrusa.specials["player_code"]
        quest_player = database["players"][quest_player_code]
        for player in idrusa.location.players:
            if player.code == quest_player_code:
                player_is_here = True
                break

    if "quest_status" in idrusa.specials:
        quest_status = idrusa.specials["quest_status"]
        if quest_status == "domanda":
            if player_is_here:
                to_say = "a %s *tranquilla* Oh beh.. qualchedun altro si farà avanti." % quest_player_code
            else:
                to_say = "a %s *tranquilla* Oh beh.. qualchedun altro si farà avanti.." % idrusa.get_numbered_keyword()
            command_say(idrusa, to_say)
        elif quest_status == "cerca":
            if player_is_here:
                to_say = "a %s *impaziente* Ci hai messo troppo tempo!" % quest_player_code
            elif quest_player_code:
                to_say = "a %s *impaziente* %s ci ha messo troppo tempo, lasciamo stare.." % (idrusa.get_numbered_keyword(), quest_player.get_name(idrusa))
            else:
                to_say = "a %s *impaziente* chi si era proposto ha evidentemente desistito..." % idrusa.get_numbered_keyword()
            command_say(idrusa, to_say)

    extract_farfalle(idrusa)

    # Cancelliamo anche le variabili speciali della quest
    if "quest_status" in idrusa.specials:
        del(idrusa.specials["quest_status"])
    if "player_code" in idrusa.specials:
        del(idrusa.specials["player_code"])
    delete_deferred_reset(idrusa)
#- Fine Funzione -


def extract_farfalle(idrusa):
    for en in idrusa.iter_contains(use_reversed=True):
        if en.race == RACE.BUTTERFLY:
            en.extract()
#- Fine Funzione -


def delete_deferred_reset(idrusa):
    if not "deferred_reset" in idrusa.specials:
        return

    deferred_reset = idrusa.specials["deferred_reset"]
    if deferred_reset:
        deferred_reset.pause()
        #deferred_reset.cancel()
        deferred_reset = None
    del(idrusa.specials["deferred_reset"])
#- Fine Funzione -
