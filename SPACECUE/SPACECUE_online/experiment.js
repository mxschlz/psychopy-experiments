let global_trial_data = [];
let abort_experiment = false;
let exited_early = false;
const datapipe_id = "p6rmFV5NMVaw";

function formatDataToCSV() {
    let responses = jsPsych.data.get().filter({phase: 'response', is_practice: false}).values();
    
    let export_data = global_trial_data.map(function(row, idx) {
        let resp_trial = responses[idx];
        let new_row = { ...row }; // copy original csv row
        
        new_row.trial_nr = idx;
        new_row.subject_id = subject;
        new_row.block = block;
        new_row.age = demo_age;
        new_row.gender = demo_gender;
        new_row.handedness = demo_handedness;
        
        if (resp_trial) {
            new_row.rt = resp_trial.rt ? resp_trial.rt / 1000 : null; // match python format (seconds)
            new_row.response = resp_trial.response !== null ? parseInt(resp_trial.response) + 1 : null;
        } else {
            new_row.rt = null;
            new_row.response = null;
        }
        
        return new_row;
    });

    // Convert back to CSV using PapaParse
    return Papa.unparse(export_data);
}

function formatMouseDataToCSV() {
    let trials = jsPsych.data.get().filterCustom(function(trial) {
        return ['cue', 'delay', 'response', 'iti'].includes(trial.phase) && trial.is_practice === false;
    }).values();

    let export_data = [];

    for (let trial of trials) {
        if (!trial.mouse_tracking_data) continue;
        
        let mData = trial.mouse_tracking_data; 
        
        for (let pt of mData) {
            export_data.push({
                subject_id: subject,
                block: block,
                trial_nr: trial.trial_nr,
                phase: trial.phase,
                t: pt.t,
                x: pt.x,
                y: pt.y,
                event: pt.event
            });
        }
    }

    return Papa.unparse(export_data);
}

function getFormattedDate() {
    const d = new Date();
    const month = d.toLocaleString('en-US', { month: 'long' });
    const day = String(d.getDate()).padStart(2, '0');
    const year = d.getFullYear();
    const hours = String(d.getHours()).padStart(2, '0');
    const minutes = String(d.getMinutes()).padStart(2, '0');
    const seconds = String(d.getSeconds()).padStart(2, '0');
    return `${month}_${day}_${year}_${hours}_${minutes}_${seconds}`;
}

const jsPsych = initJsPsych({
    display_element: 'jspsych-target',
    extensions: [{type: jsPsychExtensionMouseTracking}],
    on_finish: function() {
        if (abort_experiment) {
            return;
        }

        if (exited_early) {
            document.body.innerHTML = `
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; color: white; background: #121212;">
                <h2 style="color: #4da8da;">Daten werden gespeichert...</h2>
            </div>`;
            
            const timestamp = getFormattedDate();
            jsPsychPipe.saveData(
                datapipe_id, 
                `sce-${subject}_block_${block}_data_early_exit_${timestamp}.csv`, 
                formatDataToCSV()
            ).then((result) => {
                if (result && !result.error) {
                    document.body.innerHTML = `
                    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; color: white; background: #121212;">
                        <div class="glass-container" style="text-align: center; max-width: 600px;">
                            <h2 style="color: #ff6b6b;">Experiment abgebrochen</h2>
                            <p>Ihre Daten bis zu diesem Punkt wurden erfolgreich gespeichert.</p>
                            <p>Sie können dieses Fenster nun schließen.</p>
                        </div>
                    </div>`;
                } else {
                    console.error("DataPipe Error:", result);
                    document.body.innerHTML = `
                    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; color: white; background: #121212;">
                        <div class="glass-container" style="text-align: center; max-width: 600px;">
                            <h2 style="color: #ff6b6b;">Fehler beim Speichern</h2>
                            <p>Leider ist ein Fehler beim Speichern aufgetreten. Details finden Sie in der Konsole.</p>
                            <p>Sie können dieses Fenster nun schließen.</p>
                        </div>
                    </div>`;
                }
            }).catch((err) => {
                console.error("Fetch Error:", err);
                document.body.innerHTML = `
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; color: white; background: #121212;">
                    <div class="glass-container" style="text-align: center; max-width: 600px;">
                        <h2 style="color: #ff6b6b;">Fehler beim Speichern</h2>
                        <p>Leider ist ein Fehler beim Speichern aufgetreten.</p>
                    </div>
                </div>`;
            });
            return;
        }

        // Block Chaining and Forced Pause Logic
        let current_block = parseInt(block);
        if (current_block < 3) {
            document.body.innerHTML = `
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; color: white; background: #121212;">
                <div class="glass-container" style="text-align: center; max-width: 600px;">
                    <h2 style="color: #4da8da;">Dieser Block ist zu Ende.</h2>
                    <p>Bitte machen Sie eine kurze Pause von 60 Sekunden.</p>
                    <p>Der nächste Block startet automatisch in <strong style="font-size: 24px; color: #ff6b6b;" id="countdown">60</strong> Sekunden.</p>
                </div>
            </div>`;
            
            let timeLeft = 60;
            let timer = setInterval(function() {
                timeLeft--;
                document.getElementById('countdown').innerText = timeLeft;
                if (timeLeft <= 0) {
                    clearInterval(timer);
                    window.location.href = `?subject=${subject}&block=${current_block + 1}&age=${demo_age}&gender=${demo_gender}&handedness=${demo_handedness}`;
                }
            }, 1000);
        } else {
            document.body.innerHTML = `
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; color: white; background: #121212;">
                <div class="glass-container" style="text-align: center; max-width: 600px;">
                    <h2 style="color: #4caf50;">Das Experiment ist beendet.</h2>
                    <p>Vielen Dank für Ihre Teilnahme!</p>
                    <p>Ihre Daten wurden erfolgreich auf dem Server gespeichert. Sie können dieses Fenster nun schließen.</p>
                </div>
            </div>`;
        }
    }
});

const urlParams = new URLSearchParams(window.location.search);
const subject = urlParams.get('subject') || "1";
const block = urlParams.get('block') || "0";
let demo_age = urlParams.get('age') || null;
let demo_gender = urlParams.get('gender') || null;
let demo_handedness = urlParams.get('handedness') || null;

// Configure this to point to your Cloudflare R2 or OSF storage bucket link when deploying
// Example: const base_url = "https://pub-xxxxxx.r2.dev/";
const base_url = "https://pub-65f7c7cdfbd94569a681f48c959ee559.r2.dev/";

const csv_path = `${base_url}sequences/sce-${subject}_block_${block}.csv`;
const audio_folder = `${base_url}sequences/sce-${subject}_block_${block}/`;

// Bind the exit button
document.getElementById('exit-btn').addEventListener('click', function() {
    if (confirm("Möchten Sie das Experiment wirklich frühzeitig abbrechen? Ihre bisherigen Daten werden gespeichert.")) {
        exited_early = true;
        jsPsych.endExperiment();
    }
});

// --- PROMPTS FROM prompts.py ---
const prompts = {
    prompt1: `Willkommen und vielen Dank für die Teilnahme an diesem Experiment zur räumlichen Aufmerksamkeit.<br><br>
In jedem Durchgang des Experiments sollen Sie ein Zahlwort aus jeweils drei verschiedenen Zahlwörtern identifizieren.<br>
Versuchen Sie dabei stets, so korrekt und so schnell wie möglich zu antworten!<br>
Das Experiment ist in 4 Blöcke aufgeteilt, zwischen denen Sie kurze Pausen einlegen können.<br><br>
Drücken Sie LEERTASTE, um weiterzublättern.`,

    prompt2: `In jedem Durchgang des Experiments werden gleichzeitig drei Zahlwörter aus drei verschiedenen Richtungen abgespielt (links, geradeaus, rechts).<br>
Alle Zahlwörter werden von derselben Stimme gesprochen. Bei den Zahlwörtern handelt es sich um eine Auswahl der Zahlen zwischen 1 und 9.<br>
In einem Durchgang sind alle Ziffern einzigartig, z.B. kann die Zahl 9 nicht sowohl aus dem linken als auch dem rechten Lautsprecher gleichzeitig ertönen.<br><br>
Drücken Sie LEERTASTE, um weiterzublättern.`,

    prompt3: `Das Zahlwort, welches Sie identifizieren sollen, unterscheidet sich von den anderen beiden in der folgenden Eigenschaft:<br>
Dieses Zahlwort klingt im Vergleich zu den restlichen Zahlwörtern sehr rau und kratzig.<br>
Die Stimme dieses Wortes klingt wie in einer schlechten Telefonverbindung.<br>
Auf genau dieses Zahlwort sollen Sie sich konzentrieren und die Zahl so schnell wie möglich angeben!<br><br>
Drücken Sie LEERTASTE, um weiterzublättern.`,

    prompt4: `In allen Durchgängen hat eines der zwei weiteren Zahlwörter eine andere Tonhöhe. Dieses Zahlwort ist ein Störreiz und klingt wie eine Kinderstimme.<br>
Lassen Sie sich davon nicht irritieren: Ihre Aufgabe bleibt es, stets das raue, kratzige Zahlwort zu benennen.<br><br>
Drücken Sie LEERTASTE, um weiterzublättern.`,

    prompt5: `Während des Experiments erscheint eine Antwort-Box in der Mitte des Bildschirms.<br>
Diese enthält die Ziffern von 1 bis 9 und ist durch einen Rahmen begrenzt.<br>
Mit der Maus können Sie auf eine Zahl pro Durchgang klicken, um das raue, kratzige Zahlwort anzugeben.<br>
ACHTUNG: die Antwort ist nur gültig, wenn der Mauszeiger nach dem Klicken verschwindet!<br><br>
Drücken Sie LEERTASTE, um weiterzublättern.`,

    prompt6: `Sollten Sie zu langsam antworten, färbt sich der Rahmen der Box für eine kurze Zeit rot.<br>
Das ist dann der Hinweis, dass Sie in den kommenden Durchgängen etwas schneller antworten sollen.<br>
Bitte halten Sie Ihren Blick während der Aufgabe stets auf die Antwort-Box gerichtet.<br>
Die Zahlenfelder treten etwas hervor, wenn Sie den Mauszeiger über sie bewegen.<br>
Drücken Sie LEERTASTE, um weiterzublättern.`
};

function getCueInstruction(colorStr) {
    let t_ger = "weiß";
    let d_ger = "weiß";
    
    if (colorStr) {
        let info = colorStr.split("-");
        if (info.length >= 4) {
            let targetColor = info[1].toLowerCase(); // Still extracting color from index 1 (nonsingleton color now)
            let distractorColor = info[3].toLowerCase();
            
            const colorMap = { "red": "rot", "green": "grün", "blue": "blau", "yellow": "gelb", "orange": "orange", "white": "weiß" };
            t_ger = colorMap[targetColor] || targetColor;
            d_ger = colorMap[distractorColor] || distractorColor;
        }
    }
    
    let colored_arrow_description = `In anderen Durchgängen besitzt ein Pfeil entweder die Farbe ${t_ger} oder ${d_ger}.`;
    
    return `In jedem Durchgang werden Ihnen drei Pfeile angezeigt, welche in drei Richtungen zeigen.<br>
In einigen Durchgängen sind alle Pfeile farblos. ${colored_arrow_description}<br>
Dieser Pfeil ist nützlich, denn er zeigt, welche Art von Zahlwort aus dieser Richtung kommen wird.<br>
Die Farbe gibt dabei an, um welche Art von Zahlwort es sich handelt.<br>
Ist der Pfeil ${t_ger}, handelt es sich um einen irrelevanten Störreiz mit normaler Stimme.<br>
Ist der Pfeil ${d_ger}, handelt es sich um das hohe Zahlwort, welches sich wie eine Kinderstimme anhört.<br><br>
Drücken Sie LEERTASTE, um weiterzublättern.`;
}

// Reusable instruction trial factory
function createInstructionTrial(htmlContentArray) {
    if (!Array.isArray(htmlContentArray)) {
        htmlContentArray = [htmlContentArray];
    }
    
    let pages = htmlContentArray.map(htmlContent => {
        // Remove spacebar prompts if they happen to exist in the html
        htmlContent = htmlContent.replace("[Drücken Sie LEERTASTE, um weiterzublättern]", "");
        htmlContent = htmlContent.replace("Drücken Sie LEERTASTE, um weiterzublättern.", "");
        htmlContent = htmlContent.replace("Drücken Sie LEERTASTE, um zu beginnen.", "");
        return `<div class="instruction-text">${htmlContent}</div>`;
    });
    
    return {
        type: jsPsychInstructions,
        pages: pages,
        show_clickable_nav: true,
        button_label_previous: "Zurück",
        button_label_next: "Weiter",
        allow_keys: true,
        key_forward: "ArrowRight",
        key_backward: "ArrowLeft"
    };
}

function getInfoTrials() {
    let pages = [
`<div class="instruction-text" style="text-align: left; overflow-y: auto; max-height: 70vh; padding-right: 15px;">
    <p style="color: #f1f5f9; margin-bottom: 12px;">Sehr geehrte Dame, sehr geehrter Herr,</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">vielen Dank für Ihr Interesse an unserer Studie!</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">Im Folgenden erhalten Sie von uns einige grundlegende Informationen zur Studie und den geplanten Messungen. Außerdem informieren wir Sie über den Umgang mit den erhobenen Daten und nennen Ausschlusskriterien für die Teilnahme an der Studie.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">Bitte lesen Sie diese Studieninformation sorgfältig durch und kontaktieren Sie bei Fragen die Studienleitung (für Kontaktinformationen siehe Punkt 4).</p>
</div>`,

`<div class="instruction-text" style="text-align: left; overflow-y: auto; max-height: 70vh; padding-right: 15px;">
    <h3 style="color: #4da8da; margin-top: 25px; border-bottom: 1px solid rgba(77, 168, 218, 0.3); padding-bottom: 5px;"><strong>1. Studienziele</strong></h3>
    <p style="color: #f1f5f9; margin-bottom: 12px;">Mit dieser Studie erhoffen wir uns neue Erkenntnisse zu Verhaltensmechanismen, während Menschen ihre Aufmerksamkeit mit ihrem Gehör auf eine bestimmte Aufgabe richten.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">Zu diesem Zweck werden Ihnen verschiedene räumliche, akustische Reize vorgespielt, von denen Sie immer nur einen Reiz beachten sollen.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">Am Ende jedes Durchgangs beantworten Sie eine Frage zur Identität des relevanten akustischen Reizes.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">Vor dem eigentlichen Experiment findet eine Einführung statt, in der Sie sich mit dem Ablauf des Experiments vertraut machen können.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">Mit einer Teilnahme würden Sie einen wichtigen Beitrag zur kognitionspsychologischen Grundlagenforschung bezüglich Aufmerksamkeit beitragen.</p>
</div>`,

`<div class="instruction-text" style="text-align: left; overflow-y: auto; max-height: 70vh; padding-right: 15px;">
    <h3 style="color: #4da8da; margin-top: 25px; border-bottom: 1px solid rgba(77, 168, 218, 0.3); padding-bottom: 5px;"><strong>2. Studienumfang, geplanter Ablauf, Risiken und Vergütung</strong></h3>
    <p style="color: #f1f5f9; margin-bottom: 12px;">Die Studie umfasst einen einzigen Termin von circa 60 Minuten Dauer. Die Teilnahme erfolgt online.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">Bitte beachten Sie, dass die Studie nicht über Handys oder Tablets abgespielt werden kann, da Sie eine Tastatur benötigen.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">Außerdem sind Kopfhörer <strong>zwingend</strong> erforderlich.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">Die Studie umfasst verschiedene Teilschritte, die wir an einem Termin durchführen wollen.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">Alle Schritte werden im Folgenden zu Ihrer Information genau beschrieben.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">Der folgende Abschnitt enthält Inhalte des Studienablaufs.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">Die Durchführung der Studie teilt sich in folgende Punkte auf:</p>
    <p style="margin-left: 20px; color: #e2e8f0;">1. Die schriftliche Aufklärung der Versuchsperson.</p>
    <p style="margin-left: 20px; color: #e2e8f0;">2. Das Sammeln von personenbezogenen Daten (Alter, Händigkeit und Geschlecht).</p>
    <p style="margin-left: 20px; color: #e2e8f0;">3. Die Durchführung der Aufmerksamkeitsaufgabe durch Sie.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">Für Sie bestehen keine erkennbaren Risiken. Sie erhalten eine Aufwandsentschädigung von 12 Euro pro Stunde.</p>
</div>`,

`<div class="instruction-text" style="text-align: left; overflow-y: auto; max-height: 70vh; padding-right: 15px;">
    <h3 style="color: #4da8da; margin-top: 25px; border-bottom: 1px solid rgba(77, 168, 218, 0.3); padding-bottom: 5px;"><strong>3. Einschluss- und Ausschlusskriterien</strong></h3>
    <ul style="margin-left: 20px; line-height: 1.8;">
        <li style="margin-top: 10px; font-weight: 600;">Einschlusskriterien:</li>
        <li style="color: #4caf50;">18 - 35 Jahre</li>
        <li style="color: #4caf50;">Rechtshändigkeit</li>
        <li style="color: #4caf50;">Fähigkeit der Einverständniserklärung zur Teilnahme an dem Experiment</li>
        <li style="margin-top: 10px; font-weight: 600;">Auschlusskriterien:</li>
        <li style="color: #ff6b6b;">Neurologische oder audiologische Erkrankungen, z.B. Tragen eines Hörgeräts oder ein Schlaganfall in vergangener Zeit</li>
        <li style="color: #ff6b6b;">Unfähigkeit, die experimentellen Aufgaben entsprechend den Anweisungen auszuführen</li>
        <li style="color: #ff6b6b;">Unfähigkeit, die Einverständniserklärung zu geben</li>
    </ul>
</div>`,

`<div class="instruction-text" style="text-align: left; overflow-y: auto; max-height: 70vh; padding-right: 15px;">
    <h3 style="color: #4da8da; margin-top: 25px; border-bottom: 1px solid rgba(77, 168, 218, 0.3); padding-bottom: 5px;"><strong>4. Datenschutzrechtliche Informationen</strong></h3>
    <p style="color: #f1f5f9; margin-bottom: 12px;">Die erhobenen Daten werden pseudonymisiert <sup style="color: #4da8da; font-weight: bold; margin-left: 2px;">1</sup> und sind über einen Code in der Projektdatenbank auf den einzelnen Probanden zurückführbar.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">Die Datenbank befindet sich auf einem Server des IT-Service Center der Universität zu Lübeck (ITSC, https://www.itsc.uni-luebeck.de/dienstleistungen/it-sicherheit/firewall-und-idp.html),</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">der durch eine Firewall sowie ein Intrusion-Detection- und Intrusion-Prevention-System (IDS) geschützt ist.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">Studienrelevante Daten werden in einem RAID-basierten Archivsystem vor Ort gesichert.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">Die Daten werden nur innerhalb des geschützten LANs oder über verschlüsselte Drahtlosnetzwerke der Universität Lübeck transferiert.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">Alle Mitarbeiter der Arbeitsgruppe "Auditive Kognition" unterschreiben an ihrem ersten Arbeitstag eine Datenschutz- und Vertraulichkeitsvereinbarung.</p>
    <p style="color: #f1f5f9; margin-bottom: 8px;">Für die Datenverarbeitung verantwortlich ist:</p>
    <div style="background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 15px; margin: 10px 0 20px 0;">
    <p style="color: #f1f5f9; margin-bottom: 4px;">Max Schulz, M.Sc..</p>
    <p style="color: #f1f5f9; margin-bottom: 4px;">Maria-Goeppert-Straße 9a</p>
    <p style="color: #f1f5f9; margin-bottom: 4px;">23562 Lübeck</p>
    <p style="color: #f1f5f9; margin-bottom: 4px;">Gebäude MFC 8, 1. OG., Raum 2</p>
    <p style="color: #f1f5f9; margin-bottom: 4px;">Tel.: +49 451 3101 3647</p>
    <p style="color: #f1f5f9; margin-bottom: 4px;">E-Mail: (<a href="mailto:max.schulz@uni-luebeck.de" style="color: #4da8da; text-decoration: none; font-weight: 600;">max.schulz@uni-luebeck.de</a>)</p>
    </div>
    <p style="color: #f1f5f9; margin-bottom: 12px;">Die Datenerhebung erfolgt zum Zweck des oben genannten Studienziels.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">Die personenbezogenen Daten (Adressen, Namen etc.) werden streng vertraulich und nach gesetzlichen Bestimmungen behandelt.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">Die erhobenen Daten im Experiment werden in pseudonymisierter Form, d.h. ohne direkten Bezug zu Ihrem Namen, elektronisch gespeichert und ausgewertet.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">Für die spätere Auswertung werden die Daten aller Probanden vollständig anonymisiert<sup style="color: #4da8da; font-weight: bold; margin-left: 2px;">2</sup> herangezogen.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">Die Bestimmungen des Datenschutzgesetzes werden eingehalten.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">Zugriff auf Ihre Daten haben nur Mitarbeitende der Studie.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">Diese Personen sind zur Verschwiegenheit verpflichtet. Die Daten sind vor fremden Zugriff geschützt.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">Sie haben das Recht auf Auskunft über die Sie betreffenden Daten, auch in Form einer unentgeltlichen Kopie.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">Bei Rücknahme Ihrer Einwilligung haben Sie das Recht, die Löschung der bis dahin gesammelten Daten zu verlangen.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">Dazu kontaktieren Sie bitte Max Schulz (<a href="mailto:max.schulz@uni-luebeck.de" style="color: #4da8da; text-decoration: none; font-weight: 600;">max.schulz@uni-luebeck.de</a>).</p>
    <p style="color: #f1f5f9; margin-bottom: 8px;">Im Falle einer Beschwerde wenden Sie sich bitte an den Datenschutzbeauftragte der Universität zu Lübeck:</p>
    <div style="background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 15px; margin: 10px 0 20px 0;">
    <p style="color: #f1f5f9; margin-bottom: 4px;">x-tention Informationstechnologie GmbH</p>
    <p style="color: #f1f5f9; margin-bottom: 4px;">Margot-Becke-Ring 37, 69124 Heidelberg</p>
    <p style="color: #f1f5f9; margin-bottom: 4px;">Telefon: 0451 3101 1903</p>
    <p style="color: #f1f5f9; margin-bottom: 4px;">E-Mail: <a href="mailto:datentschutz@uni-luebeck.de" style="color: #4da8da; text-decoration: none; font-weight: 600;">datenschutz@uni-luebeck.de</a></p>
    </div>
    <p style="color: #f1f5f9; margin-bottom: 8px;">Sie können sich mit einer Beschwerde auch an die zuständige Datenschutzbehörde wenden:</p>
    <div style="background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 15px; margin: 10px 0 20px 0;">
    <p style="color: #f1f5f9; margin-bottom: 4px;">Unabhängiges Landeszentrum für Datenschutz Schleswig-Holstein</p>
    <p style="color: #f1f5f9; margin-bottom: 4px;">Holstenstraße 98, 24103 Kiel</p>
    <p style="color: #f1f5f9; margin-bottom: 4px;">E-Mail: <a href="mailto:mail@datenschutzzentrum.de" style="color: #4da8da; text-decoration: none; font-weight: 600;">mail@datenschutzzentrum.de</a></p>
    </div>
    <p style="color: #f1f5f9; margin-bottom: 12px;">Herzlichen Dank!</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">Max Schulz</p>
    <hr style="border: 0; border-top: 1px solid rgba(255, 255, 255, 0.1); margin: 20px 0;">
    <div style="font-size: 14px; color: #94a3b8; margin-top: 12px; padding-left: 12px; border-left: 3px solid #3b82f6; font-style: italic; background: rgba(59, 130, 246, 0.05); padding-top: 8px; padding-bottom: 8px; border-radius: 0 8px 8px 0;">
        <p style="margin: 0 0 5px 0;"><strong style="color: #4da8da; font-size: 16px; margin-right: 5px;">1</strong> <strong>Pseudonymisierung:</strong> "die Verarbeitung personenbezogener Daten in einer Weise,</p>
        <p style="margin: 0 0 5px 0;">dass die personenbezogenen Daten ohne Hinzuziehung zusätzlicher Informationen nicht mehr einer spezifischen betroffenen Person zugeordnet werden können,</p>
        <p style="margin: 0 0 5px 0;">sofern diese zusätzlichen Informationen gesondert aufbewahrt werden und technischen und organisatorischen Maßnahmen unterliegen,</p>
        <p style="margin: 0 0 5px 0;">die gewährleisten, dass die personen Daten nicht einer identifizierten oder identifizierbaren natürlichen Person zugewiesen werden;"</p>
        <p style="margin: 0 0 5px 0;">Artikel 4 Abs. 5 DSGVO</p>
    </div>
    <div style="font-size: 14px; color: #94a3b8; margin-top: 12px; padding-left: 12px; border-left: 3px solid #3b82f6; font-style: italic; background: rgba(59, 130, 246, 0.05); padding-top: 8px; padding-bottom: 8px; border-radius: 0 8px 8px 0;">
        <p style="margin: 0 0 5px 0;"><strong style="color: #4da8da; font-size: 16px; margin-right: 5px;">2</strong> <strong>Anonymisierung:</strong> "das Verändern personenbezogener Daten derart, dass Einzelangaben über persönliche oder sachliche Verhältnisse nicht mehr oder nur mit einem unverhältnismäßig</p>
        <p style="margin: 0 0 5px 0;">großen Aufwand an Zeit, Kosten und Arbeitskraft einer bestimmten oder bestimmbaren natürlichen Person zugeordnet werden können." §3 Abs. 6 BDSG</p>
    </div>
</div>`
    ];

    return [{
        type: jsPsychInstructions,
        pages: pages,
        show_clickable_nav: true,
        button_label_previous: "Zurück",
        button_label_next: "Weiter",
        allow_keys: true,
        key_forward: "ArrowRight",
        key_backward: "ArrowLeft"
    }];
}

const consentTrial = {
    type: jsPsychHtmlButtonResponse,
    stimulus: `<div class="instruction-text">
        <div style="text-align: left; padding: 0 20px;">
            <h2 style="color: white; margin-bottom: 20px; text-align: center;">EINVERSTÄNDNISERKLÄRUNG</h2>
            <p>Ich bestätige hiermit, dass ich über Wesen, Bedeutung, Risiken und Tragweite der beabsichtigten Studie aufgeklärt wurde und für meine Entscheidung genügend Bedenkzeit hatte.</p>
            <p>Ich wurde darauf hingewiesen, dass meine Teilnahme freiwillig ist und ich das Recht habe, diese jederzeit ohne Angabe von Gründen zu beenden, ohne dass dadurch Nachteile entstehen.</p>
            <p>Ich habe verstanden, dass ich jederzeit ohne Angabe von Gründen die Untersuchung abbrechen kann sowie das Recht auf Datenlöschung besitze.</p>
            <p>Ich erkläre mich bereit, an der verhaltenspsychologischen Untersuchung teilzunehmen. Ich erkläre mich dazu bereit, dass meine Verhaltensdaten aufgenommen und gespeichert werden.</p>
            <p>Ich erkläre mich damit einverstanden, dass meine erhobenen Daten in anonymisierter Form für Publikationszwecke verwendet werden können.</p>
            <div style="text-align: center; margin-top: 30px; padding: 20px; background: rgba(0,0,0,0.2); border-radius: 12px;">
                Wählen Sie unten eine Option aus.
            </div>
        </div>
    </div>`,
    choices: ['Zurück zu den Informationen', 'Nein, abbrechen', 'Ja, ich stimme zu'],
    button_html: [
        '<button class="jspsych-btn" style="margin: 10px; background-color: #555;">%choice%</button>',
        '<button class="jspsych-btn" style="margin: 10px; background-color: #f44336;">%choice%</button>',
        '<button class="jspsych-btn" style="margin: 10px; background-color: #4caf50;">%choice%</button>'
    ],
    on_finish: function(data) {
        if (data.response === 1) {
            abort_experiment = true;
            jsPsych.endExperiment(`<div class="instruction-text">Sie haben nicht zugestimmt. Das Experiment wird abgebrochen. Vielen Dank für Ihr Interesse.</div>`);
        }
    }
};

const headphoneCheckTrial = createInstructionTrial(`
        <div style="text-align: left;">
            <h2 style="color: #4da8da; margin-bottom: 20px;">Kopfhörer-Test & Lautstärke</h2>
            <p>Dieses Experiment erfordert das Tragen von Kopfhörern. Bitte stellen Sie sicher, dass Sie diese jetzt aufgesetzt haben.</p>
            <p>Klicken Sie auf den Button unten, um einen Testton abzuspielen. Passen Sie die Systemlautstärke Ihres Computers so an, dass Sie den Ton klar und deutlich hören können, er aber nicht unangenehm laut ist.</p>
            <div style="text-align: center;">
                <audio id="test-audio" src="${base_url}sequences/sce-${subject}_block_0/s_0.wav" preload="auto"></audio>
                <button class="jspsych-btn" style="margin: 20px 0; background-color: #4caf50;" onclick="document.getElementById('test-audio').play();">Testton abspielen</button>
            </div>
            <p style="color: #ff6b6b; font-weight: bold;">WICHTIG: Bitte verändern Sie die Lautstärke nach diesem Test während des restlichen Experiments nicht mehr!</p>
        </div>`);

function getScreeningTrials() {
    let screeningTimeline = [];
    const screening_audio_folder = `${base_url}screening_stimuli/`;
    
    // Localization Instructions
    screeningTimeline.push(createInstructionTrial(`
        <div style="text-align: center;">
            <h2 style="color: #4da8da;">Kopfhörer-Screening: Teil 1 (Ortung)</h2>
            <p>Wir prüfen nun, ob Ihr System die räumlichen Klänge korrekt wiedergibt.</p>
            <p>Sie werden gleich ein einzelnes gesprochenes Zahlwort hören. Ihre Aufgabe ist es anzugeben, aus welcher <strong>Richtung</strong> das Wort kam.</p>
            <br>
            <p style="color: #ff6b6b;">Wenn Sie einen Kopfhörer falsch herum aufhaben, werden Sie Fehler machen. Bitte prüfen Sie den Sitz (L/R) Ihrer Kopfhörer!</p>
        </div>
    `));

    const loc_trials = [
        { file: '4_loc1.wav', correct_loc: 'Links' },
        { file: '7_loc3.wav', correct_loc: 'Rechts' },
        { file: '2_loc2.wav', correct_loc: 'Mitte' }
    ];

    let screening_errors = 0;

    for (let t of loc_trials) {
        screeningTimeline.push({
            type: jsPsychAudioButtonResponse,
            stimulus: screening_audio_folder + t.file,
            choices: ['Links', 'Mitte', 'Rechts'],
            prompt: '<div style="margin-top:20px; font-size: 20px; color: white;">Aus welcher Richtung kam der Ton?</div>',
            button_html: '<button class="jspsych-btn virtual-response-box screening-btn" style="margin: 0 10px;">%choice%</button>',
            on_finish: function(data) {
                let selected_choice = ['Links', 'Mitte', 'Rechts'][data.response];
                if (selected_choice !== t.correct_loc) screening_errors++;
            }
        });
    }

    // Identification Instructions
    screeningTimeline.push(createInstructionTrial(`
        <div style="text-align: center;">
            <h2 style="color: #4da8da;">Kopfhörer-Screening: Teil 2 (Erkennung)</h2>
            <p>Nun prüfen wir, ob Sie die Zahlwörter gut verstehen können.</p>
            <p>Sie werden wieder einzelne Zahlwörter hören. Ihre Aufgabe ist es nun anzugeben, <strong>welche Zahl (1-9)</strong> gesprochen wurde.</p>
        </div>`));

    const id_trials = [
        { file: '8_loc2.wav', correct_id: '8' },
        { file: '3_loc1.wav', correct_id: '3' },
        { file: '5_loc3.wav', correct_id: '5' }
    ];

    for (let t of id_trials) {
        screeningTimeline.push({
            type: jsPsychAudioButtonResponse,
            stimulus: screening_audio_folder + t.file,
            choices: ['1','2','3','4','5','6','7','8','9'],
            prompt: '<div style="margin-top:20px; font-size: 20px; color: white;">Welches Zahlwort haben Sie gehört?</div>',
            button_html: '<button class="jspsych-btn virtual-response-box" style="margin: 0 5px;">%choice%</button>',
            on_finish: function(data) {
                let selected_choice = ['1','2','3','4','5','6','7','8','9'][data.response];
                if (selected_choice !== t.correct_id) screening_errors++;
            }
        });
    }
    
    let finish_trial = createInstructionTrial(`
        <div style="text-align: center;">
            <h2 style="color: #4caf50;">Screening beendet!</h2>
        </div>
    `);
    finish_trial.on_finish = function() {
        if (screening_errors > 0) {
            abort_experiment = true;
            jsPsych.endExperiment(`<div class="instruction-text" style="text-align: center; max-width: 600px;">
                <h2 style="color: #ff6b6b;">Screening nicht bestanden</h2>
                <p>Leider haben Sie einen oder mehrere Fehler im Screening gemacht.</p>
                <p>Dies deutet darauf hin, dass Sie entweder keine Kopfhörer tragen, diese falsch herum aufhaben (L/R vertauscht), oder die räumlichen Klänge nicht richtig wahrnehmen können.</p>
                <p>Das Experiment wird daher nun abgebrochen. Vielen Dank für Ihr Interesse.</p>
            </div>`);
        }
    };
    screeningTimeline.push(finish_trial);

    return screeningTimeline;
}

fetch(csv_path)
    .then(response => {
        if (!response.ok) throw new Error("CSV konnte nicht geladen werden: " + csv_path);
        return response.text();
    })
    .then(csvText => {
        Papa.parse(csvText, {
            header: true,
            dynamicTyping: true,
            skipEmptyLines: true,
            complete: function(results) {
                const trial_data = results.data;
                buildAndRunExperiment(trial_data);
            }
        });
    })
    .catch(error => {
        console.error(error);
        document.body.innerHTML = `<h1>Fehler beim Laden der Sequenz!</h1>
        <p style="color:red;">${error.message}</p>`;
    });

const demoTrial = {
    type: jsPsychSurveyHtmlForm,
    preamble: `<div class="instruction-text" style="text-align: left;">
        <h2 style="color: #4da8da;">Demographische Daten</h2>
        <p>Bitte geben Sie Ihre Daten ein:</p>
    </div>`,
    html: `
        <div style="text-align: left; color: white; margin-bottom: 20px; font-size: 18px;">
            <p>Alter:</p>
            <input type="number" id="age" name="age" required min="18" max="99" style="padding: 10px; border-radius: 5px; width: 100px; font-size: 16px;">
            <p style="margin-top: 15px;">Geschlecht:</p>
            <select id="gender" name="gender" required style="padding: 10px; border-radius: 5px; font-size: 16px;">
                <option value="" disabled selected>Bitte wählen...</option>
                <option value="m">Männlich</option>
                <option value="w">Weiblich</option>
                <option value="d">Divers</option>
            </select>
            <p style="margin-top: 15px;">Händigkeit:</p>
            <select id="handedness" name="handedness" required style="padding: 10px; border-radius: 5px; font-size: 16px;">
                <option value="" disabled selected>Bitte wählen...</option>
                <option value="r">Rechtshänder</option>
                <option value="l">Linkshänder</option>
            </select>
        </div>
    `,
    button_label: 'Weiter',
    on_finish: function(data) {
        demo_age = data.response.age;
        demo_gender = data.response.gender;
        demo_handedness = data.response.handedness;
    }
};

function buildAndRunExperiment(trial_data) {
    global_trial_data = trial_data;
    let timeline = [];
    
    // 1. Preload Audio Files
    let audio_files = [];
    for (let i = 0; i < trial_data.length; i++) {
        audio_files.push(`${audio_folder}s_${i}.wav`);
    }
    
    // Add screening stimuli to preload if block 0
    if (parseInt(block) === 0) {
        ['4_loc1.wav', '7_loc3.wav', '2_loc2.wav', '8_loc2.wav', '3_loc1.wav', '5_loc3.wav'].forEach(f => {
            audio_files.push(`${base_url}screening_stimuli/${f}`);
        });
    }
    
    timeline.push({
        type: jsPsychPreload,
        audio: audio_files,
        message: "Lade akustische Stimuli, bitte warten..."
    });

    // 2. Instructions (Block 0 gets all prompts, other blocks get just the cue instruction)
    if (parseInt(block) === 0) {
        let infoAndConsentLoop = {
            timeline: [
                ...getInfoTrials(),
                consentTrial
            ],
            loop_function: function(data) {
                // The last trial is the consentTrial
                let consent_response = data.values()[data.values().length - 1].response;
                if (consent_response === 0) { // 'Zurück'
                    return true;
                } else {
                    return false;
                }
            }
        };
        timeline.push(infoAndConsentLoop);
        timeline.push(demoTrial);
        timeline.push(headphoneCheckTrial);
        timeline = timeline.concat(getScreeningTrials());
        
        let main_instructions = [
            prompts.prompt1,
            prompts.prompt2,
            prompts.prompt3,
            prompts.prompt4,
            prompts.prompt5,
            prompts.prompt6
        ];
        
        let cue_instruction_html = getCueInstruction(trial_data[0].Color);
        main_instructions.push(cue_instruction_html);
        
        timeline.push(createInstructionTrial(main_instructions));
    } else {
        // The cue instruction needs the color configuration from the first row of CSV
        let cue_instruction_html = getCueInstruction(trial_data[0].Color);
        timeline.push(createInstructionTrial(cue_instruction_html));
    }

    // 3. Main Trial Loop
    let trial_timeline = {
        timeline: [
            // Phase 0: Cue Presentation (with Fixation Cross and Arrows around it)
            {
                type: jsPsychHtmlKeyboardResponse,
                stimulus: function() {
                    let nonsingletonLoc = jsPsych.timelineVariable('Non-Singleton2Loc', true); 
                    let singletonLoc = jsPsych.timelineVariable('SingletonLoc', true);
                    let colorStr = jsPsych.timelineVariable('Color', true); 
                    let cueInstruction = jsPsych.timelineVariable('CueInstruction', true);

                    let nonsingletonColor = colorStr.includes('nonsingleton-blue') ? 'blue' : (colorStr.includes('nonsingleton-yellow') ? 'yellow' : 'white');
                    let distractorColor = colorStr.includes('distractor-blue') ? 'blue' : (colorStr.includes('distractor-yellow') ? 'yellow' : 'white');
                    
                    let cuedIndex = -1; // 1=L, 2=U, 3=R
                    let activeColor = 'white';
                    
                    if (cueInstruction.includes('nonsingleton_location')) {
                        cuedIndex = nonsingletonLoc;
                        activeColor = nonsingletonColor;
                    } else if (cueInstruction.includes('distractor_location')) {
                        cuedIndex = singletonLoc;
                        activeColor = distractorColor;
                    }

                    // Build arrows HTML inside the cue-screen wrapper
                    const arrowsHTML = [1, 2, 3].map(pos => {
                        let clr = (pos === cuedIndex) ? activeColor : 'white';
                        let cls = pos === 1 ? 'arrow-left' : (pos === 2 ? 'arrow-up' : 'arrow-right');
                        return `<div class="arrow ${cls}" style="border-bottom-color: ${clr};"></div>`;
                    }).join('');

                    return `
                    <div class="cue-screen">
                        <div class="fixation">+</div>
                        ${arrowsHTML}
                    </div>`;
                },
                choices: "NO_KEYS",
                trial_duration: 200, 
                on_start: function() {
                    const logo = document.getElementById('uzl-logo');
                    if (logo) logo.style.display = 'none';
                    document.body.classList.add('hide-cursor');
                },
                extensions: [{type: jsPsychExtensionMouseTracking}],
                data: { phase: 'cue', trial_nr: jsPsych.timelineVariable('original_index'), is_practice: jsPsych.timelineVariable('is_practice') }
            },
            
            // Phase 1: Delay (Fixation only)
            {
                type: jsPsychHtmlKeyboardResponse,
                stimulus: '<div class="cue-screen"><div class="fixation">+</div></div>',
                choices: "NO_KEYS",
                trial_duration: function() {
                    return jsPsych.timelineVariable('cue_stim_delay_jitter', true) * 1000; 
                },
                on_start: function() {
                    document.body.classList.add('hide-cursor');
                },
                extensions: [{type: jsPsychExtensionMouseTracking}],
                data: { phase: 'delay', trial_nr: jsPsych.timelineVariable('original_index'), is_practice: jsPsych.timelineVariable('is_practice') }
            },

            // Phase 2/3: Audio Stimulus & Virtual Response Box (1-9 Numpad)
            {
                type: jsPsychAudioButtonResponse,
                stimulus: function() {
                    let i = jsPsych.timelineVariable('original_index', true);
                    return `${audio_folder}s_${i}.wav`;
                },
                // 9 choices for the digits 1 through 9
                choices: ['1', '2', '3', '4', '5', '6', '7', '8', '9'],
                button_html: '<button class="jspsych-btn virtual-response-box">%choice%</button>',
                response_ends_trial: false,
                trial_duration: 1750, // response_duration = 1.75s
                data: {
                    phase: 'response',
                    targetDigit: jsPsych.timelineVariable('TargetDigit'), // This one is fine as timelineVariable because it's evaluated natively by jsPsych outside a function
                    trial_nr: jsPsych.timelineVariable('original_index'),
                    is_practice: jsPsych.timelineVariable('is_practice')
                },
                extensions: [{type: jsPsychExtensionMouseTracking}],
                on_start: function() {
                    window.responded_in_trial = false;
                    document.body.classList.remove('hide-cursor');
                },
                on_load: function() {
                    const btns = document.querySelectorAll('.virtual-response-box');
                    btns.forEach(btn => {
                        btn.addEventListener('click', () => {
                            document.body.classList.add('hide-cursor');
                        });
                    });
                },
                on_finish: function(data) {
                    if (data.response !== null) {
                        window.responded_in_trial = true;
                    }
                    // Score the response (choice 0 = '1', choice 8 = '9')
                    let selectedDigit = data.response !== null ? data.response + 1 : null; 
                    data.correct = (selectedDigit === data.targetDigit);
                }
            },

            // Phase 4: ITI (Blank screen, or remaining buttons if no response yet)
            {
                type: jsPsychHtmlButtonResponse,
                stimulus: '',
                choices: ['1', '2', '3', '4', '5', '6', '7', '8', '9'],
                button_html: '<button class="jspsych-btn virtual-response-box">%choice%</button>',
                response_ends_trial: false,
                trial_duration: function() {
                    return jsPsych.timelineVariable('ITI-Jitter', true) * 1000;
                },
                on_load: function() {
                    const btns = document.querySelectorAll('.virtual-response-box');
                    
                    // Prevent initial hover transition bump
                    btns.forEach(btn => {
                        btn.style.transition = 'none';
                        setTimeout(() => {
                            btn.style.transition = '';
                        }, 50);
                    });

                    if (window.responded_in_trial) {
                        // Already responded: disable buttons and hide cursor
                        btns.forEach(btn => btn.setAttribute('disabled', 'disabled'));
                        document.body.classList.add('hide-cursor');
                    } else {
                        document.body.classList.remove('hide-cursor');
                    }

                    btns.forEach(btn => {
                        btn.addEventListener('click', (e) => {
                            document.body.classList.add('hide-cursor');
                            const container = document.querySelector('#jspsych-html-button-response-btngroup');
                            if (container && !window.responded_in_trial) {
                                container.classList.add('error-glow');
                                // Briefly glow red, then remove glow
                                setTimeout(() => {
                                    container.classList.remove('error-glow');
                                }, 500); 
                            }
                        });
                    });
                },
                extensions: [{type: jsPsychExtensionMouseTracking}],
                data: { phase: 'iti', trial_nr: jsPsych.timelineVariable('original_index'), is_practice: jsPsych.timelineVariable('is_practice') }
            }
        ],
        timeline_variables: trial_data.map((row, idx) => ({...row, original_index: idx, is_practice: false}))
    };
    
    if (parseInt(block) === 0) {
        let practice_intro = {
            type: jsPsychHtmlKeyboardResponse,
            stimulus: `<div class="instruction-text">
                <h2 style="color: #4da8da; margin-bottom: 20px;">Übungsdurchgänge</h2>
                <p>Bevor das eigentliche Experiment beginnt, haben Sie nun die Möglichkeit, 15 Übungsdurchgänge zu absolvieren.</p>
                <p>Nutzen Sie diese Durchgänge, um sich an die Aufgabe und die Steuerung zu gewöhnen. Diese Durchgänge gehen nicht in die Wertung ein.</p>
                <p style="margin-top: 30px; color: #aaa;">Drücken Sie die <strong>LEERTASTE</strong>, um mit den Übungsdurchgängen zu beginnen.</p>
            </div>`,
            choices: [" "]
        };
        timeline.push(practice_intro);
        
        let practice_vars = jsPsych.randomization.sampleWithoutReplacement(trial_data, 15).map((row, idx) => ({...row, original_index: idx, is_practice: true}));
        let practice_timeline = {
            timeline: trial_timeline.timeline,
            timeline_variables: practice_vars
        };
        timeline.push(practice_timeline);
        
        let main_start = {
            type: jsPsychHtmlKeyboardResponse,
            stimulus: `<div class="instruction-text">
                <h2 style="color: #4caf50; margin-bottom: 20px;">Start des Hauptexperiments</h2>
                <p>Die Übungsdurchgänge sind nun beendet.</p>
                <p>Das eigentliche Experiment beginnt jetzt. Bitte konzentrieren Sie sich auf die Aufgabe.</p>
                <p style="margin-top: 30px; color: #aaa;">Drücken Sie die <strong>LEERTASTE</strong>, um zu starten.</p>
            </div>`,
            choices: [" "]
        };
        timeline.push(main_start);
    }

    timeline.push(trial_timeline);

    const save_data = {
        type: jsPsychPipe,
        action: "save",
        experiment_id: datapipe_id,
        filename: `sce-${subject}_block_${block}_data_${getFormattedDate()}.csv`,
        data_string: ()=>formatDataToCSV()
    };
    timeline.push(save_data);

    const save_mouse_data = {
        type: jsPsychPipe,
        action: "save",
        experiment_id: datapipe_id,
        filename: `sce-${subject}_block_${block}_trajectories_${getFormattedDate()}.csv`,
        data_string: ()=>formatMouseDataToCSV()
    };
    timeline.push(save_mouse_data);

    jsPsych.run(timeline);
}
