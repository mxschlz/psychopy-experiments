prompt1 = '''
Willkommen und vielen Dank für die Teilnahme an diesem Experiment zur räumlichen Aufmerksamkeit. \n
In jedem Durchgang des Experiments sollen Sie ein Zahlwort aus jeweils drei verschiedenen Zahlwörtern identifizieren. \n
Versuchen Sie dabei stets, so korrekt und so schnell wie möglich zu antworten! \n
Das Experiment ist in 10 Blöcke aufgeteilt, zwischen denen Sie kurze Pausen einlegen können. \n

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
Dieser Block ist zu Ende. Bitte machen Sie eine kurze Pause.
"""

pause_finished = """
Die Pause ist zu Ende. Drücken Sie LEERTASTE, um den nächsten Block zu beginnen.
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
Ist der Pfeil {target_color_german}, handelt es sich um das raue, kratzige, zu identifizierende Zahlwort. \n
Ist der Pfeil {distractor_color_german}, handelt es sich um das hohe Zahlwort, welches sich wie eine Kinderstimme anhört. \n

Drücken Sie LEERTASTE, um weiterzublättern.
"""
