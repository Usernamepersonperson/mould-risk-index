"""Message templates in the four Swiss national languages (de-CH spelling, fr, it) plus English.

Rules for editing: every key must exist in all four languages and use the same placeholders
(tests enforce this). Texts are written by the project owner's tooling and should be read by a native
speaker before real-world use (see README, "What is not verified yet").
"""

from __future__ import annotations

LANGS = ("de", "fr", "it", "en")

ADVICE = {
    "ok": {
        "en": "Humidity is fine. No action needed.",
        "de": "Die Feuchte ist in Ordnung. Keine Massnahme nötig.",
        "fr": "L'humidité est correcte. Aucune action nécessaire.",
        "it": "L'umidità è nella norma. Nessuna azione necessaria.",
    },
    "air_now": {
        "en": "Airing: open windows on opposite sides fully for {minutes} min now (cross ventilation), then close them. "
        "Indoor air holds {excess:.1f} g/m3 more moisture than outdoor air.",
        "de": "Lüften: Fenster auf gegenüberliegenden Seiten jetzt {minutes} Min. ganz öffnen (Durchzug), danach schliessen. "
        "Die Raumluft enthält {excess:.1f} g/m3 mehr Feuchte als die Aussenluft.",
        "fr": "Aération : ouvrir grand les fenêtres de deux côtés opposés pendant {minutes} min (courant d'air), puis les refermer. "
        "L'air intérieur contient {excess:.1f} g/m3 d'humidité de plus que l'air extérieur.",
        "it": "Ventilazione: aprire completamente le finestre su lati opposti per {minutes} min (corrente d'aria), poi richiuderle. "
        "L'aria interna contiene {excess:.1f} g/m3 di umidità in più rispetto all'aria esterna.",
    },
    "air_useless": {
        "en": "Airing will not dry the room now: outdoor air carries about as much moisture as indoor air "
        "({ah_out:.1f} vs {ah_in:.1f} g/m3). Keep the heating steady and avoid new moisture sources.",
        "de": "Lüften trocknet jetzt nicht: Die Aussenluft enthält etwa gleich viel Feuchte wie die Raumluft "
        "({ah_out:.1f} gegenüber {ah_in:.1f} g/m3). Heizung konstant halten und neue Feuchtequellen vermeiden.",
        "fr": "Aérer n'asséchera pas la pièce maintenant : l'air extérieur contient à peu près autant d'humidité que l'air intérieur "
        "({ah_out:.1f} contre {ah_in:.1f} g/m3). Maintenir un chauffage régulier et éviter de nouvelles sources d'humidité.",
        "it": "Ventilare ora non asciuga l'ambiente: l'aria esterna contiene circa la stessa umidità di quella interna "
        "({ah_out:.1f} contro {ah_in:.1f} g/m3). Mantenere un riscaldamento costante ed evitare nuove fonti di umidità.",
    },
    "heat_up": {
        "en": "Raise the heating setpoint by {dk:.1f} K. The coldest wall spots are at about {surf_rh:.0f} % relative humidity; "
        "warmer surfaces lower it.",
        "de": "Heizung um {dk:.1f} K höher einstellen. Die kältesten Wandstellen liegen bei etwa {surf_rh:.0f} % relativer Feuchte; "
        "wärmere Oberflächen senken sie.",
        "fr": "Augmenter la consigne de chauffage de {dk:.1f} K. Les points les plus froids du mur sont à environ "
        "{surf_rh:.0f} % d'humidité relative ; des surfaces plus chaudes la réduisent.",
        "it": "Aumentare la temperatura impostata di {dk:.1f} K. I punti più freddi della parete sono a circa "
        "{surf_rh:.0f} % di umidità relativa; superfici più calde la riducono.",
    },
    "heat_not_enough": {
        "en": "A higher setpoint alone will not be enough (cold wall spots at {surf_rh:.0f} %). Combine airing with a "
        "check of the wall by the property manager.",
        "de": "Eine höhere Heizeinstellung allein genügt nicht (kalte Wandstellen bei {surf_rh:.0f} %). Lüften und die Wand "
        "von der Verwaltung prüfen lassen.",
        "fr": "Une consigne plus élevée ne suffira pas à elle seule (points froids du mur à {surf_rh:.0f} %). Aérer et faire "
        "contrôler le mur par la gérance.",
        "it": "Una temperatura impostata più alta non basta da sola (punti freddi della parete a {surf_rh:.0f} %). "
        "Ventilare e far controllare la parete dall'amministrazione.",
    },
    "min_temp": {
        "en": "Room temperature is {t_in:.1f} C. Keep occupied and adjoining rooms at 17 C or more, also at night, and keep "
        "doors to colder rooms closed so warm moist air does not reach cold walls.",
        "de": "Die Raumtemperatur beträgt {t_in:.1f} C. Bewohnte und angrenzende Räume auch nachts auf mindestens 17 C halten "
        "und Türen zu kälteren Räumen schliessen, damit warme feuchte Luft nicht an kalte Wände gelangt.",
        "fr": "La température de la pièce est de {t_in:.1f} C. Garder les pièces occupées et voisines à 17 C ou plus, aussi la nuit, "
        "et fermer les portes vers les pièces plus froides afin que l'air chaud et humide n'atteigne pas les murs froids.",
        "it": "La temperatura della stanza è {t_in:.1f} C. Mantenere le stanze occupate e adiacenti ad almeno 17 C, anche di notte, "
        "e tenere chiuse le porte verso i locali più freddi, così l'aria calda e umida non raggiunge le pareti fredde.",
    },
    "move_furniture": {
        "en": "Move wardrobes and beds 5-10 cm away from external walls, especially in corners, so room air can reach the wall.",
        "de": "Schränke und Betten 5-10 cm von Aussenwänden abrücken, besonders in Ecken, damit Raumluft an die Wand gelangt.",
        "fr": "Éloigner armoires et lits de 5 à 10 cm des murs extérieurs, surtout dans les angles, pour que l'air de la pièce "
        "atteigne le mur.",
        "it": "Spostare armadi e letti di 5-10 cm dalle pareti esterne, soprattutto negli angoli, così l'aria della stanza "
        "raggiunge la parete.",
    },
    "reduce_moisture": {
        "en": "Moisture load is high ({excess:.1f} g/m3 above outdoor air). Dry laundry outside or in a ventilated room with the "
        "door closed, cook with lids on, and air after showering.",
        "de": "Die Feuchtelast ist hoch ({excess:.1f} g/m3 über der Aussenluft). Wäsche draussen oder in einem gelüfteten Raum "
        "bei geschlossener Tür trocknen, mit Deckel kochen und nach dem Duschen lüften.",
        "fr": "La charge d'humidité est élevée ({excess:.1f} g/m3 de plus que l'air extérieur). Sécher le linge dehors ou dans une "
        "pièce aérée porte fermée, cuisiner avec couvercle et aérer après la douche.",
        "it": "Il carico di umidità è elevato ({excess:.1f} g/m3 sopra l'aria esterna). Asciugare il bucato all'aperto o in un "
        "locale ventilato a porta chiusa, cucinare con il coperchio e ventilare dopo la doccia.",
    },
    "notify_manager": {
        "en": "The wall stays damp despite airing and heating. Report it to the property manager so the thermal bridge can be "
        "checked. This is a neutral hint, not an assessment of fault.",
        "de": "Die Wand bleibt trotz Lüften und Heizen feucht. Bitte der Verwaltung melden, damit die Wärmebrücke geprüft wird. "
        "Das ist ein neutraler Hinweis, keine Schuldzuweisung.",
        "fr": "Le mur reste humide malgré l'aération et le chauffage. À signaler à la gérance pour faire contrôler le pont "
        "thermique. Il s'agit d'une indication neutre, pas d'une attribution de responsabilité.",
        "it": "La parete resta umida nonostante ventilazione e riscaldamento. Segnalarlo all'amministrazione per far controllare "
        "il ponte termico. È un'indicazione neutra, non un'attribuzione di colpa.",
    },
    "check_sensor": {
        "en": "No readings for {hours} h. Check the sensor battery and radio range.",
        "de": "Seit {hours} Std. keine Messwerte. Batterie und Funkreichweite des Sensors prüfen.",
        "fr": "Aucune mesure depuis {hours} h. Vérifier la pile et la portée radio du capteur.",
        "it": "Nessuna misura da {hours} h. Controllare la batteria e la portata radio del sensore.",
    },
}

SEVERITY = {
    "info": {"en": "Info", "de": "Info", "fr": "Info", "it": "Info"},
    "watch": {"en": "Watch", "de": "Beobachten", "fr": "À surveiller", "it": "Da osservare"},
    "warn": {"en": "Warning", "de": "Warnung", "fr": "Avertissement", "it": "Avviso"},
    "critical": {"en": "Critical", "de": "Kritisch", "fr": "Critique", "it": "Critico"},
}

REPORT = {
    "title": {
        "en": "Weekly humidity report",
        "de": "Wochenbericht Raumfeuchte",
        "fr": "Rapport hebdomadaire d'humidité",
        "it": "Rapporto settimanale sull'umidità",
    },
    "flat": {"en": "Flat", "de": "Wohnung", "fr": "Logement", "it": "Appartamento"},
    "period": {"en": "Period", "de": "Zeitraum", "fr": "Période", "it": "Periodo"},
    "summary": {"en": "Summary", "de": "Zusammenfassung", "fr": "Résumé", "it": "Riepilogo"},
    "mean_t": {
        "en": "Mean room temperature (C)",
        "de": "Mittlere Raumtemperatur (C)",
        "fr": "Température moyenne de la pièce (C)",
        "it": "Temperatura media della stanza (C)",
    },
    "mean_rh": {
        "en": "Mean room humidity (%)",
        "de": "Mittlere Raumfeuchte (%)",
        "fr": "Humidité moyenne de la pièce (%)",
        "it": "Umidità media della stanza (%)",
    },
    "hours_over_80": {
        "en": "Hours with wall-surface humidity of 80 % or more",
        "de": "Stunden mit Wandoberflächenfeuchte von 80 % oder mehr",
        "fr": "Heures avec humidité de surface du mur de 80 % ou plus",
        "it": "Ore con umidità superficiale della parete pari o superiore all'80 %",
    },
    "mould_index": {
        "en": "Mould index at end of week (0-6)",
        "de": "Schimmelindex am Wochenende (0-6)",
        "fr": "Indice de moisissure en fin de semaine (0-6)",
        "it": "Indice di muffa a fine settimana (0-6)",
    },
    "coverage": {
        "en": "Data coverage (%)",
        "de": "Datenabdeckung (%)",
        "fr": "Couverture des données (%)",
        "it": "Copertura dei dati (%)",
    },
    "factors": {
        "en": "Contributing factors (neutral)",
        "de": "Einflussfaktoren (neutral)",
        "fr": "Facteurs contributifs (neutre)",
        "it": "Fattori concorrenti (neutro)",
    },
    "moisture_load": {
        "en": "Moisture load: room air holds {v:.1f} g/m3 more water than outdoor air on average",
        "de": "Feuchtelast: Die Raumluft enthält im Mittel {v:.1f} g/m3 mehr Wasser als die Aussenluft",
        "fr": "Charge d'humidité : l'air de la pièce contient en moyenne {v:.1f} g/m3 d'eau de plus que l'air extérieur",
        "it": "Carico di umidità: l'aria della stanza contiene in media {v:.1f} g/m3 di acqua in più dell'aria esterna",
    },
    "surface_temp": {
        "en": "Wall temperature factor (building side): assumed fRsi {v:.2f}; recommended minimum 0.70",
        "de": "Temperaturfaktor der Wand (Gebäudeseite): angenommenes fRsi {v:.2f}; empfohlenes Minimum 0.70",
        "fr": "Facteur de température du mur (côté bâtiment) : fRsi supposé {v:.2f} ; minimum recommandé 0.70",
        "it": "Fattore di temperatura della parete (lato edificio): fRsi ipotizzato {v:.2f}; minimo raccomandato 0.70",
    },
    "actions": {
        "en": "Suggested actions",
        "de": "Empfohlene Massnahmen",
        "fr": "Actions suggérées",
        "it": "Azioni suggerite",
    },
    "alerts": {
        "en": "Alert episodes this week",
        "de": "Warnepisoden in dieser Woche",
        "fr": "Épisodes d'alerte cette semaine",
        "it": "Episodi di allarme questa settimana",
    },
    "privacy": {
        "en": "Privacy: readings are processed and stored on a local device only. Nothing is sent to a cloud service. "
        "The report contains room temperature and humidity, no occupancy data.",
        "de": "Datenschutz: Die Messwerte werden nur auf einem lokalen Gerät verarbeitet und gespeichert. "
        "Es wird nichts an einen Cloud-Dienst gesendet. Der Bericht enthält Raumtemperatur und -feuchte, keine Anwesenheitsdaten.",
        "fr": "Protection des données : les mesures sont traitées et stockées uniquement sur un appareil local. "
        "Rien n'est envoyé vers un service cloud. Le rapport contient température et humidité, aucune donnée de présence.",
        "it": "Protezione dei dati: le misure sono elaborate e conservate solo su un dispositivo locale. "
        "Nulla viene inviato a un servizio cloud. Il rapporto contiene temperatura e umidità, nessun dato di presenza.",
    },
    "disclaimer": {
        "en": "This report is an indicator, not a legal or expert assessment. It does not assign responsibility to tenant or landlord.",
        "de": "Dieser Bericht ist ein Indikator, kein rechtliches oder fachliches Gutachten. Er weist weder Mieter noch Vermieter "
        "eine Verantwortung zu.",
        "fr": "Ce rapport est un indicateur, pas une expertise juridique ou technique. Il n'attribue aucune responsabilité au "
        "locataire ni au bailleur.",
        "it": "Questo rapporto è un indicatore, non una perizia legale o tecnica. Non attribuisce responsabilità né all'inquilino "
        "né al locatore.",
    },
}


def tr(table: dict, key: str, lang: str, **kw) -> str:
    """Look up and format a template; unknown language falls back to English."""
    entry = table[key]
    text = entry.get(lang) or entry["en"]
    return text.format(**kw) if kw else text
