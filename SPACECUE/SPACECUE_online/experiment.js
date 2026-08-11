let global_all_blocks_data = {};
let current_block_global = 0;
let abort_experiment = false;
let exited_early = false;
const datapipe_id = "p6rmFV5NMVaw";

function formatDataToCSV(b) {
    let current_trial_data = global_all_blocks_data[b];
    let responses = jsPsych.data.get().filter({phase: 'response', is_practice: false, block: b}).values();
    
    let export_data = current_trial_data.map(function(row, idx) {
        let resp_trial = responses.find(r => r.trial_nr === idx);
        let new_row = { ...row }; // copy original csv row
        
        new_row.trial_nr = idx;
        new_row.subject_id = subject;
        new_row.prolific_pid = prolific_pid;
        new_row.study_id = study_id;
        new_row.session_id = session_id;
        new_row.block = b;
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

function formatMouseDataToCSV(b) {
    let trials = jsPsych.data.get().filterCustom(function(trial) {
        return ['cue', 'delay', 'response', 'iti'].includes(trial.phase) && trial.is_practice === false && trial.block === b;
    }).values();

    let export_data = [];

    for (let trial of trials) {
        if (!trial.mouse_tracking_data) continue;
        
        let mData = trial.mouse_tracking_data; 
        
        for (let pt of mData) {
            export_data.push({
                subject_id: subject,
                prolific_pid: prolific_pid,
                study_id: study_id,
                session_id: session_id,
                block: b,
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
                `sce-${subject}_block_${current_block_global}_data_early_exit_${timestamp}.csv`, 
                formatDataToCSV(current_block_global)
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

        if (prolific_pid && prolific_pid !== "null") {
            // REDIRECT TO PROLIFIC
            // Important: Replace "YOUR_COMPLETION_CODE" with the actual code from Prolific!
            window.location.href = "https://app.prolific.com/submissions/complete?cc=YOUR_COMPLETION_CODE";
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

let subject, prolific_pid, study_id, session_id, block, demo_age, demo_gender, demo_handedness, csv_path, audio_folder;

// Configure this to point to your Cloudflare R2 or OSF storage bucket link when deploying
const base_url = "https://pub-65f7c7cdfbd94569a681f48c959ee559.r2.dev/";

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

    prompt2: `In jedem Durchgang des Experiments werden gleichzeitig drei Zahlwörter aus drei verschiedenen Richtungen abgespielt (links, mitte, rechts).<br>
Alle Zahlwörter werden von derselben Stimme gesprochen. Bei den Zahlwörtern handelt es sich um eine Auswahl der Zahlen zwischen 1 und 9.<br>
In einem Durchgang sind alle Ziffern einzigartig, z.B. kann die Zahl 9 nicht sowohl von links als auch von rechts gleichzeitig ertönen.<br><br>
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
ACHTUNG: die Antwort ist nur gültig, wenn der Mauszeiger nach dem Klicken verschwindet! Bitte stellen Sie sicher, dass Sie in jedem Durchgang eine Antwort geben, da ansonsten Ihre Daten unvollständig sind und nicht gewertet werden können.<br><br>
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
    let t_col = "#ffffff";
    let d_col = "#ffffff";
    
    if (colorStr) {
        let info = colorStr.split("-");
        if (info.length >= 4) {
            let targetColor = info[1].toLowerCase(); // Still extracting color from index 1 (nonsingleton color now)
            let distractorColor = info[3].toLowerCase();
            
            const colorMap = { "red": "rot", "green": "grün", "blue": "blau", "yellow": "gelb", "orange": "orange", "white": "weiß" };
            // Using slightly muted/brightened hex codes so they look good on a dark background
            const hexMap = { "red": "#ff6b6b", "green": "#4caf50", "blue": "#4da8da", "yellow": "#ffeb3b", "orange": "#ffa726", "white": "#ffffff" };
            
            t_ger = colorMap[targetColor] || targetColor;
            d_ger = colorMap[distractorColor] || distractorColor;
            t_col = hexMap[targetColor] || targetColor;
            d_col = hexMap[distractorColor] || distractorColor;
        }
    }
    
    let t_highlight = `<span style="color: ${t_col}; font-weight: bold; text-transform: uppercase;">${t_ger}</span>`;
    let d_highlight = `<span style="color: ${d_col}; font-weight: bold; text-transform: uppercase;">${d_ger}</span>`;
    
    let colored_arrow_description = `In anderen Durchgängen besitzt ein Pfeil entweder die Farbe ${t_highlight} oder ${d_highlight}.`;
    
    return `In jedem Durchgang werden Ihnen drei Pfeile angezeigt, welche in drei Richtungen zeigen.<br>
In einigen Durchgängen sind alle Pfeile farblos. ${colored_arrow_description}<br>
Dieser Pfeil ist nützlich, denn er zeigt, welche Art von Zahlwort aus dieser Richtung kommen wird.<br>
Die Farbe gibt dabei an, um welche Art von Zahlwort es sich handelt.<br>
Ist der Pfeil ${t_highlight}, handelt es sich um das Zahlwort mit normaler Stimme.<br>
Ist der Pfeil ${d_highlight}, handelt es sich um das hohe Zahlwort, welches sich wie eine Kinderstimme anhört.<br><br>
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
    <p style="color: #f1f5f9; margin-bottom: 12px;">Die erhobenen Daten werden pseudonymisiert<sup style="color: #4da8da; font-weight: bold; margin-left: 2px;">1</sup> und sind über einen Code in der Projektdatenbank auf den einzelnen Probanden zurückführbar.</p>
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
    <p style="color: #f1f5f9; margin-bottom: 4px;">Gebäude MFC 8, 1. OG., Raum 5</p>
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

function getHeadphoneCheckTrial() {
    return createInstructionTrial(`
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
}

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

(async function initializeExperiment() {
    const urlParams = new URLSearchParams(window.location.search);
    subject = urlParams.get('subject');
    prolific_pid = urlParams.get('PROLIFIC_PID') || null;
    study_id = urlParams.get('STUDY_ID') || null;
    session_id = urlParams.get('SESSION_ID') || null;

    if (!subject) {
        try {
            // DataPipe automatically assigns a unique, non-repeating condition ID sequentially
            // It distributes from 0 to N-1 based on your OSF/DataPipe settings.
            let condition = await jsPsychPipe.getCondition(datapipe_id);
            subject = condition + 1; // Maps 0 to 1, 1 to 2, etc.
        } catch (e) {
            console.error("DataPipe condition assignment failed", e);
            const NUM_PREGENERATED_SEQUENCES = 200; // Only used as a fallback now!
            subject = Math.floor(Math.random() * NUM_PREGENERATED_SEQUENCES) + 1;
        }
    }

    block = urlParams.get('block') || "0";
    demo_age = urlParams.get('age') || null;
    demo_gender = urlParams.get('gender') || null;
    demo_handedness = urlParams.get('handedness') || null;

    let start_block = parseInt(block);
    let all_blocks_data = [];

    try {
        for (let b = start_block; b < 4; b++) {
            let b_csv_path = `${base_url}sequences/sce-${subject}_block_${b}.csv`;
            const response = await fetch(b_csv_path);
            if (!response.ok) throw new Error("CSV konnte nicht geladen werden: " + b_csv_path);
            const csvText = await response.text();
            await new Promise(resolve => {
                Papa.parse(csvText, {
                    header: true,
                    dynamicTyping: true,
                    skipEmptyLines: true,
                    complete: function(results) {
                        all_blocks_data.push({ block: b, data: results.data });
                        resolve();
                    }
                });
            });
        }
        buildAndRunExperiment(all_blocks_data, start_block);
    } catch (error) {
        console.error(error);
        document.body.innerHTML = `<h1>Fehler beim Laden der Sequenz!</h1>
        <p style="color:red;">${error.message}</p>`;
    }
})();

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

function buildAndRunExperiment(all_blocks_data, start_block) {
    for (let item of all_blocks_data) { global_all_blocks_data[item.block] = item.data; }
    let timeline = [];
    
    for (let b_idx = 0; b_idx < all_blocks_data.length; b_idx++) {
        let current_block_data = all_blocks_data[b_idx];
        let current_block_num = current_block_data.block;
        let trial_data = current_block_data.data;
        let b_audio_folder = `${base_url}sequences/sce-${subject}_block_${current_block_num}/`;
        
        timeline.push({
            type: jsPsychCallFunction,
            func: function() { current_block_global = current_block_num; }
        });
        
        // 1. Preload Audio Files
        let audio_files = [];
        for (let i = 0; i < trial_data.length; i++) {
            audio_files.push(`${b_audio_folder}s_${i}.wav`);
        }
        
        if (current_block_num === 0) {
            ['4_loc1.wav', '7_loc3.wav', '2_loc2.wav', '8_loc2.wav', '3_loc1.wav', '5_loc3.wav'].forEach(f => {
                audio_files.push(`${base_url}screening_stimuli/${f}`);
            });
            ['1','2','3','4','5','6','7','8','9'].forEach(d => {
                audio_files.push(`${base_url}stimuli/targets_low_30_Hz/${d}_amplitude_modulated_30.wav`);
                audio_files.push(`${base_url}stimuli/digits_all_250ms/${d}.wav`);
            });
        }
        
        timeline.push({
            type: jsPsychPreload,
            audio: audio_files,
            message: `Lade akustische Stimuli (Block ${current_block_num + 1} von 4), bitte warten...`
        });

        // 2. Instructions
        if (current_block_num === 0) {
            let infoAndConsentLoop = {
                timeline: [
                    ...getInfoTrials(),
                    consentTrial
                ],
                loop_function: function(data) {
                    let consent_response = data.values()[data.values().length - 1].response;
                    if (consent_response === 0) {
                        return true;
                    } else {
                        return false;
                    }
                }
            };
            timeline.push(infoAndConsentLoop);
            timeline.push(demoTrial);
            timeline.push(getHeadphoneCheckTrial());
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

            // DEMO BLOCK
            let demo_instruction_trial = createInstructionTrial(`
                <div style="text-align: center; color: white;">
                    <h2 style="color: #4da8da;">Zielreize</h2>
                    <p>Im Kommenden werden Sie einen Eindruck davon erhalten, wie sich die Zahlwörter anhören.</p>
                    <p>Es werden nur die relevanten Zahlwörter abgespielt, auf die Sie achten sollen.</p>
                    <p>Dabei ertönen sie zufällig aus einer der drei Richtungen, so wie es auch im Hauptexperiment sein wird.</p>
                    <p>ACHTUNG: erschrecken Sie bitte nicht.</p>
                </div>
            `);

            let demo_audio_trials = [];
            let demo_digits = [1, 2, 3, 4, 5, 6, 7, 8, 9];
            for (let d of demo_digits) {
                demo_audio_trials.push({
                    type: jsPsychAudioKeyboardResponse,
                    stimulus: `${base_url}stimuli/targets_low_30_Hz/${d}_amplitude_modulated_30.wav`,
                    choices: "NO_KEYS",
                    trial_duration: 1500,
                    prompt: '<div style="margin-top:20px; font-size: 40px; color: white;">...</div>'
                });
            }
            timeline.push(demo_instruction_trial);
            for (let dt of demo_audio_trials) { timeline.push(dt); }

            // ACCURACY TEST BLOCK
            let acc_correct_count = 0;
            let current_acc_trial = {};

            let accuracy_instruction_trial = createInstructionTrial(`
                <div style="text-align: center; color: white;">
                    <h2 style="color: #4da8da;">Genauigkeitstest</h2>
                    <p>Nun werden Ihnen nacheinander Zahlwörter abgespielt. Nach jedem Zahlwort müssen Sie durch Tastendruck angeben, ob es sich um ein zu identifizierendes Zahlwort (rau, kratzig) oder um ein reguläres Zahlwort handelt.</p>
                    <p>Drücken sie die Taste <strong style="color: #4caf50;">L</strong> für das raue, kratzige Zahlwort, und die Taste <strong style="color: #ff6b6b;">M</strong> für das reguläre Zahlwort.</p>
                    <p>Sie müssen 10 Wörter <strong>hintereinander</strong> korrekt identifizieren, um mit dem Experiment beginnen zu können.</p>
                    <p>Bei einem Fehler beginnt die Zählung wieder bei 0.</p>
                </div>
            `);
            accuracy_instruction_trial.on_start = function() {
                acc_correct_count = 0;
            };

            let accuracy_audio_trial = {
                type: jsPsychAudioKeyboardResponse,
                stimulus: function() {
                    let digit = Math.floor(Math.random() * 9) + 1;
                    let isTarget = Math.random() < 0.5;
                    current_acc_trial.file = isTarget ? `${base_url}stimuli/targets_low_30_Hz/${digit}_amplitude_modulated_30.wav` : `${base_url}stimuli/digits_all_250ms/${digit}.wav`;
                    current_acc_trial.correct_key = isTarget ? 'l' : 'm';
                    return current_acc_trial.file;
                },
                choices: ['l', 'm'],
                prompt: function() {
                    return `
                        <div style="margin-top:20px; font-size: 40px; color: white; display: flex; flex-direction: column; align-items: center; gap: 20px;">
                            <div style="display: flex; justify-content: center; gap: 50px;">
                                <div><span style="color: #4caf50;">L</span></div>
                                <div>oder</div>
                                <div><span style="color: #ff6b6b;">M</span></div>
                            </div>
                            <div style="font-size: 24px; color: #aaa;">
                                Bisher korrekt: ${acc_correct_count} / 10
                            </div>
                        </div>
                    `;
                },
                on_finish: function(data) {
                    data.correct = (data.response === current_acc_trial.correct_key);
                }
            };

            let accuracy_feedback_trial = {
                type: jsPsychHtmlKeyboardResponse,
                stimulus: function() {
                    let last_trial_correct = jsPsych.data.get().last(1).values()[0].correct;
                    if (last_trial_correct) {
                        acc_correct_count++;
                        return `<div style="font-size: 30px; color: #4caf50;">Korrekt! (${acc_correct_count}/10)</div>`;
                    } else {
                        acc_correct_count = 0;
                        return '<div style="font-size: 30px; color: #ff6b6b;">Falsch! Zähler zurückgesetzt.</div>';
                    }
                },
                choices: "NO_KEYS",
                trial_duration: 1000,
            };

            let accuracy_dynamic_loop = {
                timeline: [accuracy_audio_trial, accuracy_feedback_trial],
                loop_function: function() {
                    if (acc_correct_count >= 10) {
                        return false;
                    }
                    return true;
                }
            };

            let accuracy_result_trial = {
                type: jsPsychHtmlKeyboardResponse,
                stimulus: `
                    <div style="text-align: center; color: white;">
                        <h2 style="color: #4caf50;">Geschafft!</h2>
                        <p>Sie haben 10 Zahlwörter hintereinander korrekt identifiziert.</p>
                        <p>Drücken Sie auf die Rechte Pfeiltaste, um weiterzublättern.</p>
                    </div>
                `,
                choices: ['ArrowRight']
            };

            timeline.push(accuracy_instruction_trial);
            timeline.push(accuracy_dynamic_loop);
            timeline.push(accuracy_result_trial);

            // CUE TEST BLOCK
            let cue_correct_count = 0;
            let current_cue_trial = {};

            let cue_test_instruction_trial = createInstructionTrial(`
                <div style="text-align: center; color: white;">
                    <h2 style="color: #4da8da;">Pfeil-Test</h2>
                    <p>Nun prüfen wir, ob Sie sich die Bedeutung der farbigen Pfeile gemerkt haben.</p>
                    <p>Ihnen wird nacheinander ein farbiger Pfeil präsentiert.</p>
                    <p>Drücken Sie die Taste <strong style="color: #4caf50;">N</strong>, wenn der Pfeil die <strong>Normale Stimme</strong> ankündigt.</p>
                    <p>Drücken Sie die Taste <strong style="color: #ff6b6b;">K</strong>, wenn der Pfeil die <strong>Kinderstimme</strong> (Störreiz) ankündigt.</p>
                    <p>Sie müssen 10 Pfeile <strong>hintereinander</strong> korrekt zuordnen.</p>
                    <p>Bei einem Fehler beginnt die Zählung wieder bei 0.</p>
                </div>
            `);
            cue_test_instruction_trial.on_start = function() {
                cue_correct_count = 0;
            };

            let cue_test_trial = {
                type: jsPsychHtmlKeyboardResponse,
                stimulus: function() {
                    let t_color_name = trial_data[0].Color.split("-")[1].toLowerCase();
                    let d_color_name = trial_data[0].Color.split("-")[3].toLowerCase();
                    const hexMap = { "red": "#ff6b6b", "green": "#4caf50", "blue": "#4da8da", "yellow": "#ffeb3b", "orange": "#ffa726", "white": "#ffffff" };
                    let t_col_hex = hexMap[t_color_name] || t_color_name;
                    let d_col_hex = hexMap[d_color_name] || d_color_name;
                    
                    let isTarget = Math.random() < 0.5;
                    current_cue_trial.color_hex = isTarget ? t_col_hex : d_col_hex;
                    current_cue_trial.correct_key = isTarget ? 'n' : 'k';
                    
                    return `
                        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh;">
                            <div class="arrow arrow-up" style="border-bottom-color: ${current_cue_trial.color_hex}; transform: translate(0, 0) scale(3); position: relative; margin-bottom: 60px; top: 0; left: 0;"></div>
                            <div style="font-size: 30px; color: white; display: flex; flex-direction: column; align-items: center; gap: 20px; margin-top: 40px;">
                                <div style="display: flex; gap: 50px;">
                                    <div><span style="color: #4caf50; font-weight: bold;">N</span> (Normale Stimme)</div>
                                    <div>oder</div>
                                    <div><span style="color: #ff6b6b; font-weight: bold;">K</span> (Kinderstimme)</div>
                                </div>
                                <div style="font-size: 24px; color: #aaa;">
                                    Bisher korrekt: ${cue_correct_count} / 10
                                </div>
                            </div>
                        </div>
                    `;
                },
                choices: ['n', 'k'],
                on_finish: function(data) {
                    data.correct = (data.response === current_cue_trial.correct_key);
                }
            };

            let cue_test_feedback = {
                type: jsPsychHtmlKeyboardResponse,
                stimulus: function() {
                    let last_trial_correct = jsPsych.data.get().last(1).values()[0].correct;
                    if (last_trial_correct) {
                        cue_correct_count++;
                        return `<div style="font-size: 30px; color: #4caf50;">Korrekt! (${cue_correct_count}/10)</div>`;
                    } else {
                        cue_correct_count = 0;
                        return '<div style="font-size: 30px; color: #ff6b6b;">Falsch! Zähler zurückgesetzt.</div>';
                    }
                },
                choices: "NO_KEYS",
                trial_duration: 1000,
            };

            let cue_dynamic_loop = {
                timeline: [cue_test_trial, cue_test_feedback],
                loop_function: function() {
                    if (cue_correct_count >= 10) {
                        return false;
                    }
                    return true;
                }
            };

            let cue_result_trial = {
                type: jsPsychHtmlKeyboardResponse,
                stimulus: `
                    <div style="text-align: center; color: white;">
                        <h2 style="color: #4caf50;">Geschafft!</h2>
                        <p>Sie haben 10 Pfeile hintereinander korrekt identifiziert.</p>
                        <p>Drücken Sie auf die Rechte Pfeiltaste, um weiterzublättern.</p>
                    </div>
                `,
                choices: ['ArrowRight']
            };

            timeline.push(cue_test_instruction_trial);
            timeline.push(cue_dynamic_loop);
            timeline.push(cue_result_trial);
            
            timeline.push(createInstructionTrial(`
                <div style="text-align: center; color: white;">
                    <h2 style="color: #4caf50;">Bereit für das Hauptexperiment</h2>
                    <p>Im Kommenden werden Ihnen einige Probe-Durchläufe präsentiert. Diese sollen Sie mit der Aufgabe vertraut machen.</p>
                    <p>Sie können üben und Antworten geben, diese werden natürlich nicht gespeichert.</p>
                    <p>Bitte nutzen Sie diese Phase, um so gut wie möglich mit dem Experiment vertraut zu werden.</p>
                    <p>Nach diesem Testblock startet das Hauptexperiment.</p>
                </div>
            `));
        }

        // 3. Main Trial Loop
        let trial_timeline = {
            timeline: [
                {
                    type: jsPsychHtmlKeyboardResponse,
                    stimulus: function() {
                        let nonsingletonLoc = jsPsych.timelineVariable('Non-Singleton2Loc', true); 
                        let singletonLoc = jsPsych.timelineVariable('SingletonLoc', true);
                        let colorStr = jsPsych.timelineVariable('Color', true); 
                        let cueInstruction = jsPsych.timelineVariable('CueInstruction', true);

                        let colorParts = colorStr.split('-');
                        let nonsingletonColor = colorParts[1];
                        let distractorColor = colorParts[3];
                        const hexMap = { "red": "#ff6b6b", "green": "#4caf50", "blue": "#4da8da", "yellow": "#ffeb3b", "orange": "#ffa726", "white": "#ffffff" };
                        let nonsingletonColorHex = hexMap[nonsingletonColor] || nonsingletonColor;
                        let distractorColorHex = hexMap[distractorColor] || distractorColor;
                        
                        let cuedIndex = -1; // 1=L, 2=U, 3=R
                        let activeColor = 'white';
                        
                        if (cueInstruction.includes('nonsingleton_location')) {
                            cuedIndex = nonsingletonLoc;
                            activeColor = nonsingletonColorHex;
                        } else if (cueInstruction.includes('distractor_location')) {
                            cuedIndex = singletonLoc;
                            activeColor = distractorColorHex;
                        }

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
                    data: { phase: 'cue', trial_nr: jsPsych.timelineVariable('original_index'), is_practice: jsPsych.timelineVariable('is_practice'), block: current_block_num }
                },
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
                    data: { phase: 'delay', trial_nr: jsPsych.timelineVariable('original_index'), is_practice: jsPsych.timelineVariable('is_practice'), block: current_block_num }
                },
                {
                    type: jsPsychAudioButtonResponse,
                    stimulus: function() {
                        let i = jsPsych.timelineVariable('original_index', true);
                        return `${b_audio_folder}s_${i}.wav`;
                    },
                    choices: ['1', '2', '3', '4', '5', '6', '7', '8', '9'],
                    button_html: '<button class="jspsych-btn virtual-response-box">%choice%</button>',
                    response_ends_trial: false,
                    trial_duration: 1750,
                    data: {
                        phase: 'response',
                        targetDigit: jsPsych.timelineVariable('TargetDigit'),
                        trial_nr: jsPsych.timelineVariable('original_index'),
                        is_practice: jsPsych.timelineVariable('is_practice'),
                        block: current_block_num
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
                        let selectedDigit = data.response !== null ? data.response + 1 : null; 
                        data.correct = (selectedDigit === data.targetDigit);
                    }
                },
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
                        
                        btns.forEach(btn => {
                            btn.style.transition = 'none';
                            setTimeout(() => {
                                btn.style.transition = '';
                            }, 50);
                        });

                        if (window.responded_in_trial) {
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
                                    setTimeout(() => {
                                        container.classList.remove('error-glow');
                                    }, 500); 
                                }
                            });
                        });
                    },
                    extensions: [{type: jsPsychExtensionMouseTracking}],
                    data: { phase: 'iti', trial_nr: jsPsych.timelineVariable('original_index'), is_practice: jsPsych.timelineVariable('is_practice'), block: current_block_num }
                }
            ],
            timeline_variables: trial_data.map((row, idx) => ({...row, original_index: idx, is_practice: false}))
        };

        if (current_block_num === 0) {
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
            filename: ()=>`sce-${subject}_block_${current_block_num}_data_${getFormattedDate()}.csv`,
            data_string: ()=>formatDataToCSV(current_block_num)
        };
        timeline.push(save_data);

        const save_mouse_data = {
            type: jsPsychPipe,
            action: "save",
            experiment_id: datapipe_id,
            filename: ()=>`sce-${subject}_block_${current_block_num}_trajectories_${getFormattedDate()}.csv`,
            data_string: ()=>formatMouseDataToCSV(current_block_num)
        };
        timeline.push(save_mouse_data);

        if (current_block_num < 3) {
            timeline.push({
                type: jsPsychHtmlKeyboardResponse,
                stimulus: function() {
                    return `
                    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; color: white; background: #121212;">
                        <div class="glass-container" style="text-align: center; max-width: 600px;">
                            <h2 style="color: #4da8da;">Dieser Block ist zu Ende.</h2>
                            <p>Bitte machen Sie eine kurze Pause von 60 Sekunden.</p>
                            <p>Der nächste Block startet automatisch in <strong style="font-size: 24px; color: #ff6b6b;" id="countdown">60</strong> Sekunden.</p>
                        </div>
                    </div>`;
                },
                choices: "NO_KEYS",
                trial_duration: 60000,
                on_load: function() {
                    let timeLeft = 60;
                    let timer = setInterval(function() {
                        timeLeft--;
                        let el = document.getElementById('countdown');
                        if(el) el.innerText = timeLeft;
                        if (timeLeft <= 0) {
                            clearInterval(timer);
                        }
                    }, 1000);
                    window.blockTimer = timer;
                },
                on_finish: function() {
                    if (window.blockTimer) clearInterval(window.blockTimer);
                }
            });
        }
    }
    
    jsPsych.run(timeline);
}