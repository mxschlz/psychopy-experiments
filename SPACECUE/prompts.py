prompt1 = '''
Willkommen und vielen Dank für die Teilnahme an diesem Experiment zur räumlichen Aufmerksamkeit. \n
In jedem Durchgang des Experiments sollen Sie ein Zahlwort aus jeweils drei verschiedenen Zahlwörtern identifizieren. \n
Versuchen Sie dabei stets, so korrekt und so schnell wie möglich zu antworten! \n
Das Experiment ist in 4 Blöcke aufgeteilt, zwischen denen Sie kurze Pausen einlegen können. \n

Drücken Sie LEERTASTE, um weiterzublättern.
'''

prompt2 = """
In jedem Durchgang des Experiments werden gleichzeitig drei Zahlwörter aus drei verschiedenen Richtungen abgespielt (links, geradeaus, rechts). \n
Alle Zahlwörter werden von derselben Stimme gesprochen. Bei den Zahlwörtern handelt es sich um eine Auswahl der Zahlen zwischen 1 und 9. \n
In einem Durchgang sind alle Ziffern einzigartig, z.B. kann die Zahl 9 nicht sowohl aus dem linken als auch dem rechten Lautsprecher gleichzeitig ertönen. \n

Drücken Sie LEERTASTE, um weiterzublättern.
"""

prompt3 = """
Das Zahlwort, welches Sie identifizieren sollen, unterscheidet sich von den anderen beiden in der folgenden Eigenschaft: \n
Dieses Zahlwort klingt im Vergleich zu den restlichen Zahlwörtern sehr rau und kratzig. \n
Die Stimme dieses Wortes klingt wie in einer schlechten Telefonverbindung. \n
Auf genau dieses Zahlwort sollen Sie sich konzentrieren und die Zahl so schnell wie möglich angeben! \n

Drücken Sie LEERTASTE, um weiterzublättern.
"""

prompt4 = """
In allen Durchgängen hat eines der zwei weiteren Zahlwörter eine andere Tonhöhe. Dieses Zahlwort ist ein Störreiz und klingt wie eine Kinderstimme. \n
Lassen Sie sich davon nicht irritieren: Ihre Aufgabe bleibt es, stets das raue, kratzige Zahlwort zu benennen. \n

Drücken Sie LEERTASTE, um weiterzublättern.
"""

demo = """
Im Kommenden werden Sie einen Eindruck davon erhalten, wie sich die Zahlwörter anhören. \n
Es werden nur die relevanten Zahlwörter abgespielt, auf die Sie achten sollen. \n
Dabei ertönen sie zufällig aus einem der drei Lautsprecher, so wie es auch im Hauptexperiment sein wird. \n
ACHTUNG: erschrecken Sie bitte nicht. \n

Drücken Sie LEERTASTE, um die Zielziffern zwischen 1 und 9 anzuhören.
"""

prompt5 = """
Während des Experiments erscheint eine Antwort-Box in der Mitte des Bildschirms. \n
Diese enthält die Ziffern von 1 bis 9 und ist durch einen schwarzen Rahmen begrenzt. \n
Mit der Maus können Sie auf eine Zahl pro Durchgang klicken, um das raue, kratzige Zahlwort anzugeben. \n
ACHTUNG: die Antwort ist nur gültig, wenn der Mauszeiger nach dem Klicken verschwindet! \n

Drücken Sie LEERTASTE, um weiterzublättern.
"""

prompt6 = """
Sollten Sie zu langsam antworten, färbt sich der Rahmen der Box für eine kurze Zeit rot. \n
Das ist dann der Hinweis, dass Sie in den kommenden Durchgängen etwas schneller antworten sollen. \n
Bitte halten Sie Ihren Blick während der Aufgabe stets auf die Antwort-Box gerichtet. \n
Die Zahlen färben sich dunkel, wenn Sie den Mauszeiger über sie bewegen. \n
Der Mauszeiger erscheint in der Mitte der Box am Anfang jedes Durchgangs und verschwindet, sobald Sie eine Zahl ausgewählt haben. \n

Drücken Sie LEERTASTE, um weiterzublättern.
"""

prompt7 = """
Während des Experiments können Sie Ihre Antwort auf der horizontalen Leiste Ihrer Tastatur abgeben (1 - 9). \n
Bitte achten Sie darauf, dass sie Ihren Blick auf den Bildschirm gerichtet halten. Wenn Sie ab und zu auf die Tastatur für Ihre Antwort schauen sollten, ist das natürlich kein Problem. \n

Drücken Sie LEERTASTE, um weiterzublättern.
"""

testing = """
Im Kommenden werden Ihnen einige Probe-Durchläufe präsentiert. Diese sollen Sie mit der Aufgabe vertraut machen. \n
Sie können üben und Antworten geben, diese werden natürlich nicht gespeichert. \n
Bitte nutzen Sie diese Phase, um so gut wie möglich mit dem Experiment vertraut zu werden. \n
Nach diesem Testblock können Sie Fragen an die Versuchsleitung stellen. Nach diesem Testblock startet das Hauptexperiment. \n

Drücken Sie LEERTASTE, um zu beginnen.
"""

camera_calibration = """
Bitte schauen Sie für die nächsten 10 Sekunden auf den Fixationspunkt. \n
Achten Sie darauf, dass Ihr Kopf und Ihre Augen geradeaus auf den Punkt gerichtet sind. \n
Sie sollten Ihren Kopf so halten, wie sie es auch während des Experiments tun. \n
Versuchen Sie stets, Ihren Kopf während der Messung so still und entspannt wie möglich zu halten. \n
Während der Pausen können Sie sich natürlich frei bewegen. \n
Danach geht es mit dem Experiment weiter. \n

Drücken Sie LEERTASTE, um zu beginnen.
"""

pause = """
Dieser Block ist zu Ende. Bitte machen Sie eine kurze Pause von 60 Sekunden. \n
Der nächste Block startet im Anschluss automatisch.
"""

pause_finished = """
Die Pause ist zu Ende. Drücken Sie LEERTASTE, um den nächsten Block zu beginnen.
"""

# --- STUDY INFO & CONSENT (From infos.md and consent.md) ---

info_pages = [
    """
Sehr geehrte Dame, sehr geehrter Herr,
vielen Dank für Ihr Interesse an unserer Studie!

Im Folgenden erhalten Sie von uns einige grundlegende Informationen zur Studie und den geplanten Messungen. Außerdem informieren wir Sie über den Umgang mit den erhobenen Daten und nennen Ausschlusskriterien für die Teilnahme an der Studie.

Bitte lesen Sie diese Studieninformation sorgfältig durch und kontaktieren Sie bei Fragen die Studienleitung.

1. Studienziele
Mit dieser Studie erhoffen wir uns neue Erkenntnisse zu Verhaltensmechanismen, während Menschen ihre Aufmerksamkeit mit ihrem Gehör auf eine bestimmte richten.
Zu diesem Zweck werden Ihnen verschiedene räumliche, akustische Reize vorgespielt, von denen Sie immer nur einen Reiz beachten sollen.
Am Ende jedes Durchgangs beantworten Sie eine Frage zur Identität des relevanten akustischen Reizes. 
Vor dem eigentlichen Experiment findet eine Einführung statt, in der Sie sich mit dem Ablauf des Experiments vertraut machen können. 
Mit einer Teilnahme würden Sie einen wichtigen Beitrag zur kognitionspsychologischen Grundlagenforschung bezüglich Aufmerksamkeit beitragen.

[Drücken Sie LEERTASTE, um weiterzublättern]
""",
    """
2. Studienumfang, geplanter Ablauf, Risiken und Vergütung

Die Studie umfasst einen einzigen Termin von circa 60 Minuten Dauer. Die Teilnahme erfolgt online.
Bitte beachten Sie, dass die Studie nicht über Handys oder Tablets abgespielt werden kann, da Sie eine Tastatur benötigen.
Außerdem sind Kopfhörer zwingend erforderlich. 

Die Durchführung der Studie teilt sich in folgende Punkte auf:
1. Die schriftliche Aufklärung der Versuchsperson.
2. Das Sammeln von personenbezogenen Daten (Alter, Händigkeit und Geschlecht).
3. Die Durchführung der Aufmerksamkeitsaufgabe durch Sie.

Für Sie bestehen keine erkennbaren Risiken. Sie erhalten eine Aufwandsentschädigung von 12 Euro pro Stunde.

[Drücken Sie LEERTASTE, um weiterzublättern]
""",
    """
3. Einschluss- und Ausschlusskriterien

Einschlusskriterien:
- 18 - 35 Jahre
- Rechtshändigkeit
- Fähigkeit der Einverständniserklärung zur Teilnahme an dem Experiment

Ausschlusskriterien:
- Neurologische oder audiologische Erkrankungen, z.B. Tragen eines Hörgeräts oder ein Schlaganfall in vergangener Zeit
- Unfähigkeit, die experimentellen Aufgaben entsprechend den Anweisungen auszuführen
- Unfähigkeit, die Einverständniserklärung zu geben

[Drücken Sie LEERTASTE, um weiterzublättern]
""",
    """
4. Datenschutzrechtliche Informationen

Die erhobenen Daten werden pseudonymisiert und sind über einen Code in der Projektdatenbank auf den einzelnen Probanden zurückführbar.
Die personenbezogenen Daten (Adressen, Namen etc.) werden streng vertraulich und nach gesetzlichen Bestimmungen behandelt.
Die erhobenen Daten im Experiment werden in pseudonymisierter Form, d.h. ohne direkten Bezug zu Ihrem Namen, elektronisch gespeichert und ausgewertet.
Für die spätere Auswertung werden die Daten aller Probanden vollständig anonymisiert herangezogen.

Für die Datenverarbeitung verantwortlich ist:
Max Schulz, M.Sc.
Maria-Goeppert-Straße 9a
23562 Lübeck
Gebäude MFC 8, 1. OG., Raum 2
Tel.: +49 451 3101 3647
E-Mail: max.schulz@uni-luebeck.de

Zugriff auf Ihre Daten haben nur Mitarbeitende der Studie.
Sie haben das Recht auf Auskunft über die Sie betreffenden Daten, auch in Form einer unentgeltlichen Kopie.
Bei Rücknahme Ihrer Einwilligung haben Sie das Recht, die Löschung der bis dahin gesammelten Daten zu verlangen.
Dazu kontaktieren Sie bitte Max Schulz.

[Drücken Sie LEERTASTE, um weiterzublättern]
""",
    """
5. Datenschutzrechtliche Informationen (Fortsetzung)

Im Falle einer Beschwerde wenden Sie sich bitte an den Datenschutzbeauftragte der Universität zu Lübeck:
x-tention Informationstechnologie GmbH
Margot-Becke-Ring 37, 69124 Heidelberg
Telefon: 0451 3101 1903
E-Mail: datenschutz@uni-luebeck.de

Sie können sich mit einer Beschwerde auch an die zuständige Datenschutzbehörde wenden:
Unabhängiges Landeszentrum für Datenschutz Schleswig-Holstein
Holstenstraße 98, 24103 Kiel
E-Mail: mail@datenschutzzentrum.de

Herzlichen Dank!
Max Schulz
---
[1] Pseudonymisierung: "die Verarbeitung personenbezogener Daten in einer Weise, dass die personenbezogenen Daten ohne Hinzuziehung zusätzlicher Informationen nicht mehr einer spezifischen betroffenen Person zugeordnet werden können..." Artikel 4 Abs. 5 DSGVO
[2] Anonymisierung: "das Verändern personenbezogener Daten derart, dass Einzelangaben über persönliche oder sachliche Verhältnisse nicht mehr... einer bestimmten oder bestimmbaren natürlichen Person zugeordnet werden können." §3 Abs. 6 BDSG

[Drücken Sie LEERTASTE, um weiterzublättern]
"""
]

consent_form = """
EINVERSTÄNDNISERKLÄRUNG

Ich bestätige hiermit, dass ich über Wesen, Bedeutung, Risiken und Tragweite der beabsichtigten Studie aufgeklärt wurde und für meine Entscheidung genügend Bedenkzeit hatte.
Ich wurde darauf hingewiesen, dass meine Teilnahme freiwillig ist und ich das Recht habe, diese jederzeit ohne Angabe von Gründen zu beenden, ohne dass dadurch Nachteile entstehen.
Ich habe verstanden, dass ich jederzeit ohne Angabe von Gründen die Untersuchung abbrechen kann sowie das Recht auf Datenlöschung besitze.
Ich erkläre mich bereit, an der verhaltenspsychologischen Untersuchung teilzunehmen. Ich erkläre mich dazu bereit, dass meine Verhaltensdaten aufgenommen und gespeichert werden.
Ich erkläre mich damit einverstanden, dass meine erhobenen Daten in anonymisierter Form für Publikationszwecke verwendet werden können.

Drücken Sie 'Y' (Yes/Ja), wenn Sie zustimmen und teilnehmen möchten.
Drücken Sie 'N' (No/Nein), wenn Sie NICHT zustimmen und das Experiment abbrechen möchten.
"""


end = """
Das Experiment ist nun vorbei. Vielen Dank für die Teilnahme! \n
Sie können sich nun an die Versuchsleitung wenden.
"""

accuracy_instruction = """
Nun werden Ihnen nacheinander 10 Zahlwörter abgespielt. Nach jedem Zahlwort müssen Sie durch Tastendruck angeben, ob es sich um ein zu identifizierendes Zahlwort (rau, kratzig) oder um ein reguläres Zahlwort handelt.\n
Drücken sie die Taste L für das raue, kratzige Zahlwort, und die Taste M für das reguläre Zahlwort.\n
Sie müssen alle 10 Wörter korrekt identifizieren, um mit dem Experiment beginnen zu können.\n
Erreichen Sie weniger als 100%, wiederholt sich dieser Test automatisch.\n

Drücken Sie LEERTASTE, um zu beginnen.
"""


def get_cue_instruction(csv_subject_path):
    """
    Generates the cue instruction string with German color names.

    Args:
        csv_subject_path: absolute path leading to a csv subject file with a column "Color"
                          that specifies the target and distractor color
                          (e.g., "target-blue-distractor-yellow").

    Returns:
        Instruction text string in German.
    """
    import pandas as pd

    df = pd.read_csv(csv_subject_path)
    # Assuming the "Color" column is consistent for all rows if df has multiple,
    # or that you specifically want the first row's configuration.
    instruction_string = df.iloc[0]["Color"]
    info = instruction_string.split("-")

    # Extract color names from the CSV string (e.g., "blue", "yellow")
    target_color_from_csv = info[1]
    distractor_color_from_csv = info[-1]

    # Map English color names to German
    color_translation_map = {
        "red": "rot",
        "green": "grün",
        "blue": "blau",
        "yellow": "gelb",
        "orange": "orange"  # In case you use orange later
        # Add any other color translations if needed
    }

    # Translate to German. Use .lower() for case-insensitive matching from CSV.
    # If a color from CSV is not in the map (e.g., already German), it will use the original.
    target_color_german = color_translation_map.get(target_color_from_csv.lower(), target_color_from_csv)
    distractor_color_german = color_translation_map.get(distractor_color_from_csv.lower(), distractor_color_from_csv)

    # Dynamically create the sentence describing which colors the arrow can have.
    # This makes the prompt accurate for the current subject's color scheme.
    colored_arrow_description = f"In anderen Durchgängen besitzt ein Pfeil entweder die Farbe {target_color_german} oder {distractor_color_german}."

    # If there's a possibility that only one type of colored cue appears, or other neutral cues,
    # you might prefer a more general statement like:
    # colored_arrow_description = "In anderen Durchgängen ist einer der Pfeile farbig."
    # For now, the version above matches the original structure more closely.

    return f"""
In jedem Durchgang werden Ihnen drei Pfeile angezeigt, welche in drei Richtungen zeigen. \n
In einigen Durchgängen sind alle Pfeile farblos. {colored_arrow_description} \n
Dieser Pfeil ist nützlich, denn er zeigt, welche Art von Zahlwort aus dieser Richtung kommen wird. \n
Die Farbe gibt dabei an, um welche Art von Zahlwort es sich handelt. \n
Ist der Pfeil {target_color_german}, handelt es sich um einen Störreiz mit normaler Stimme. \n
Ist der Pfeil {distractor_color_german}, handelt es sich um das hohe Zahlwort, welches sich wie eine Kinderstimme anhört. \n

Drücken Sie LEERTASTE, um weiterzublättern.
"""
