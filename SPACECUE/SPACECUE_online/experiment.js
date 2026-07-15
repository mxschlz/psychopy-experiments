let global_trial_data = [];
let abort_experiment = false;
let exited_early = false;
const datapipe_id = "p6rmFV5NMVaw";

function formatDataToCSV() {
    let responses = jsPsych.data.get().filter({phase: 'response'}).values();
    
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
Diese enthält die Ziffern von 1 bis 9 und ist durch einen schwarzen Rahmen begrenzt.<br>
Mit der Maus können Sie auf eine Zahl pro Durchgang klicken, um das raue, kratzige Zahlwort anzugeben.<br>
ACHTUNG: die Antwort ist nur gültig, wenn der Mauszeiger nach dem Klicken verschwindet!<br><br>
Drücken Sie LEERTASTE, um weiterzublättern.`,

    prompt6: `Sollten Sie zu langsam antworten, färbt sich der Rahmen der Box für eine kurze Zeit rot.<br>
Das ist dann der Hinweis, dass Sie in den kommenden Durchgängen etwas schneller antworten sollen.<br>
Bitte halten Sie Ihren Blick während der Aufgabe stets auf die Antwort-Box gerichtet.<br>
Die Zahlen färben sich dunkel, wenn Sie den Mauszeiger über sie bewegen.<br>
Der Mauszeiger erscheint in der Mitte der Box am Anfang jedes Durchgangs und verschwindet, sobald Sie eine Zahl ausgewählt haben.<br><br>
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
function createInstructionTrial(htmlContent) {
    // Remove spacebar prompts if they happen to exist in the html
    htmlContent = htmlContent.replace("[Drücken Sie LEERTASTE, um weiterzublättern]", "");
    htmlContent = htmlContent.replace("Drücken Sie LEERTASTE, um weiterzublättern.", "");
    htmlContent = htmlContent.replace("Drücken Sie LEERTASTE, um zu beginnen.", "");
    
    return {
        type: jsPsychInstructions,
        pages: [`<div class="instruction-text">${htmlContent}</div>`],
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
        `<div class="instruction-text" style="text-align: left;">
            <p>Sehr geehrte Dame, sehr geehrter Herr,</p>
            <p>vielen Dank für Ihr Interesse an unserer Studie!</p>
            <p>Im Folgenden erhalten Sie von uns einige grundlegende Informationen zur Studie und den geplanten Messungen. Außerdem informieren wir Sie über den Umgang mit den erhobenen Daten und nennen Ausschlusskriterien für die Teilnahme an der Studie.</p>
            <p>Bitte lesen Sie diese Studieninformation sorgfältig durch und kontaktieren Sie bei Fragen die Studienleitung.</p>
            <h3 style="color: #4da8da; margin-top: 30px;">1. Studienziele</h3>
            <p>Mit dieser Studie erhoffen wir uns neue Erkenntnisse zu Verhaltensmechanismen, während Menschen ihre Aufmerksamkeit mit ihrem Gehör auf eine bestimmte richten.</p>
            <p>Zu diesem Zweck werden Ihnen verschiedene räumliche, akustische Reize vorgespielt, von denen Sie immer nur einen Reiz beachten sollen. Am Ende jedes Durchgangs beantworten Sie eine Frage zur Identität des relevanten akustischen Reizes.</p>
            <p>Vor dem eigentlichen Experiment findet eine Einführung statt, in der Sie sich mit dem Ablauf des Experiments vertraut machen können.</p>
            <p>Mit einer Teilnahme würden Sie einen wichtigen Beitrag zur kognitionspsychologischen Grundlagenforschung bezüglich Aufmerksamkeit beitragen.</p>
        </div>`,
        
        `<div class="instruction-text" style="text-align: left;">
            <h3 style="color: #4da8da;">2. Studienumfang, geplanter Ablauf, Risiken und Vergütung</h3>
            <p>Die Studie umfasst einen einzigen Termin von circa <strong>60 Minuten</strong> Dauer. Die Teilnahme erfolgt online.</p>
            <p style="color: #ff6b6b;"><strong>Bitte beachten Sie, dass die Studie nicht über Handys oder Tablets abgespielt werden kann, da Sie eine Tastatur benötigen. Außerdem sind Kopfhörer zwingend erforderlich.</strong></p>
            <p>Die Durchführung der Studie teilt sich in folgende Punkte auf:</p>
            <ol style="margin-left: 20px;">
                <li>Die schriftliche Aufklärung der Versuchsperson.</li>
                <li>Das Sammeln von personenbezogenen Daten (Alter, Händigkeit und Geschlecht).</li>
                <li>Die Durchführung der Aufmerksamkeitsaufgabe durch Sie.</li>
            </ol>
            <p>Für Sie bestehen keine erkennbaren Risiken. Sie erhalten eine Aufwandsentschädigung von <strong>12 Euro pro Stunde</strong>.</p>
        </div>`,
        
        `<div class="instruction-text" style="text-align: left;">
            <h3 style="color: #4da8da;">3. Einschluss- und Ausschlusskriterien</h3>
            <p><strong>Einschlusskriterien:</strong></p>
            <ul style="margin-left: 20px;">
                <li>18 - 35 Jahre</li>
                <li>Rechtshändigkeit</li>
                <li>Fähigkeit der Einverständniserklärung zur Teilnahme an dem Experiment</li>
            </ul>
            <p style="margin-top: 20px;"><strong>Ausschlusskriterien:</strong></p>
            <ul style="margin-left: 20px; color: #ff9e9e;">
                <li>Neurologische oder audiologische Erkrankungen (z.B. Tragen eines Hörgeräts oder ein Schlaganfall in vergangener Zeit)</li>
                <li>Unfähigkeit, die experimentellen Aufgaben entsprechend den Anweisungen auszuführen</li>
                <li>Unfähigkeit, die Einverständniserklärung zu geben</li>
            </ul>
        </div>`,
        
        `<div class="instruction-text" style="text-align: left;">
            <h3 style="color: #4da8da;">4. Datenschutzrechtliche Informationen</h3>
            <p>Die erhobenen Daten werden pseudonymisiert[1] und sind über einen Code in der Projektdatenbank auf den einzelnen Probanden zurückführbar.<br>Die personenbezogenen Daten (Adressen, Namen etc.) werden streng vertraulich und nach gesetzlichen Bestimmungen behandelt.<br>Die erhobenen Daten im Experiment werden in pseudonymisierter Form, d.h. ohne direkten Bezug zu Ihrem Namen, elektronisch gespeichert und ausgewertet.</p>
            <p>Für die spätere Auswertung werden die Daten aller Probanden vollständig anonymisiert[2] herangezogen.</p>
            <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; margin-top: 15px;">
                <strong>Für die Datenverarbeitung verantwortlich ist:</strong><br>
                Max Schulz, M.Sc.<br>
                Maria-Goeppert-Straße 9a<br>
                23562 Lübeck<br>
                Gebäude MFC 8, 1. OG., Raum 2<br>
                Tel.: +49 451 3101 3647<br>
                E-Mail: max.schulz@uni-luebeck.de
            </div>
            <p style="margin-top: 15px;">Zugriff auf Ihre Daten haben nur Mitarbeitende der Studie. Sie haben das Recht auf Auskunft über die Sie betreffenden Daten, auch in Form einer unentgeltlichen Kopie. Bei Rücknahme Ihrer Einwilligung haben Sie das Recht, die Löschung der bis dahin gesammelten Daten zu verlangen. Dazu kontaktieren Sie bitte Max Schulz.</p>
        </div>`,
        
        `<div class="instruction-text" style="text-align: left;">
            <h3 style="color: #4da8da;">5. Datenschutzrechtliche Informationen (Fortsetzung)</h3>
            <p>Im Falle einer Beschwerde wenden Sie sich bitte an den Datenschutzbeauftragte der Universität zu Lübeck:<br>
            <strong>x-tention Informationstechnologie GmbH</strong><br>
            Margot-Becke-Ring 37, 69124 Heidelberg<br>
            Telefon: 0451 3101 1903<br>
            E-Mail: datenschutz@uni-luebeck.de</p>
            <p>Sie können sich mit einer Beschwerde auch an die zuständige Datenschutzbehörde wenden:<br>
            <strong>Unabhängiges Landeszentrum für Datenschutz Schleswig-Holstein</strong><br>
            Holstenstraße 98, 24103 Kiel<br>
            E-Mail: mail@datenschutzzentrum.de</p>
            <p>Herzlichen Dank!<br><em>Max Schulz</em></p>
            <hr style="border-color: rgba(255,255,255,0.1); margin: 20px 0;">
            <p style="font-size: 14px; color: #aaa;">[1] <strong>Pseudonymisierung:</strong> "die Verarbeitung personenbezogener Daten in einer Weise, dass die personenbezogenen Daten ohne Hinzuziehung zusätzlicher Informationen nicht mehr einer spezifischen betroffenen Person zugeordnet werden können..." Artikel 4 Abs. 5 DSGVO</p>
            <p style="font-size: 14px; color: #aaa;">[2] <strong>Anonymisierung:</strong> "das Verändern personenbezogener Daten derart, dass Einzelangaben über persönliche oder sachliche Verhältnisse nicht mehr... einer bestimmten oder bestimmbaren natürlichen Person zugeordnet werden können." §3 Abs. 6 BDSG</p>
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
    type: jsPsychHtmlKeyboardResponse,
    stimulus: `<div class="instruction-text">
        <div style="text-align: left; padding: 0 20px;">
            <h2 style="color: white; margin-bottom: 20px; text-align: center;">EINVERSTÄNDNISERKLÄRUNG</h2>
            <p>Ich bestätige hiermit, dass ich über Wesen, Bedeutung, Risiken und Tragweite der beabsichtigten Studie aufgeklärt wurde und für meine Entscheidung genügend Bedenkzeit hatte.</p>
            <p>Ich wurde darauf hingewiesen, dass meine Teilnahme freiwillig ist und ich das Recht habe, diese jederzeit ohne Angabe von Gründen zu beenden, ohne dass dadurch Nachteile entstehen.</p>
            <p>Ich habe verstanden, dass ich jederzeit ohne Angabe von Gründen die Untersuchung abbrechen kann sowie das Recht auf Datenlöschung besitze.</p>
            <p>Ich erkläre mich bereit, an der verhaltenspsychologischen Untersuchung teilzunehmen. Ich erkläre mich dazu bereit, dass meine Verhaltensdaten aufgenommen und gespeichert werden.</p>
            <p>Ich erkläre mich damit einverstanden, dass meine erhobenen Daten in anonymisierter Form für Publikationszwecke verwendet werden können.</p>
            <div style="text-align: center; margin-top: 30px; padding: 20px; background: rgba(0,0,0,0.2); border-radius: 12px;">
                Drücken Sie <strong style="color:#4caf50; font-size: 22px;">'J' (Ja)</strong>, wenn Sie zustimmen und teilnehmen möchten.<br><br>
                Drücken Sie <strong style="color:#f44336; font-size: 22px;">'N' (Nein)</strong>, wenn Sie NICHT zustimmen und abbrechen möchten.
            </div>
        </div>
    </div>`,
    choices: ['j', 'n'],
    on_finish: function(data) {
        if (jsPsych.pluginAPI.compareKeys(data.response, 'n')) {
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
    screeningTimeline.push({
        type: jsPsychHtmlKeyboardResponse,
        stimulus: `<div class="instruction-text" style="text-align: center;">
            <h2 style="color: #4da8da;">Kopfhörer-Screening: Teil 1 (Ortung)</h2>
            <p>Wir prüfen nun, ob Ihr System die räumlichen Klänge korrekt wiedergibt.</p>
            <p>Sie werden gleich ein einzelnes gesprochenes Zahlwort hören. Ihre Aufgabe ist es anzugeben, aus welcher <strong>Richtung</strong> das Wort kam.</p>
            <br>
            <p style="color: #ff6b6b;">Wenn Sie einen Kopfhörer falsch herum aufhaben, werden Sie Fehler machen. Bitte prüfen Sie den Sitz (L/R) Ihrer Kopfhörer!</p>
            <br>
            <p>Drücken Sie LEERTASTE, um zu beginnen.</p>
        </div>`,
        choices: [' ']
    });

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
            button_html: '<button class="jspsych-btn virtual-response-box" style="margin: 0 10px;">%choice%</button>',
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
    
    screeningTimeline.push({
        type: jsPsychInstructions,
        pages: [`<div class="instruction-text" style="text-align: center;">
            <h2 style="color: #4caf50;">Screening beendet!</h2>
        </div>`],
        show_clickable_nav: true,
        button_label_previous: "Zurück",
        button_label_next: "Weiter",
        allow_keys: true,
        key_forward: "ArrowRight",
        key_backward: "ArrowLeft",
        on_finish: function() {
            if (screening_errors > 0) {
                abort_experiment = true;
                jsPsych.endExperiment(`<div class="instruction-text" style="text-align: center; max-width: 600px;">
                    <h2 style="color: #ff6b6b;">Screening nicht bestanden</h2>
                    <p>Leider haben Sie einen oder mehrere Fehler im Screening gemacht.</p>
                    <p>Dies deutet darauf hin, dass Sie entweder keine Kopfhörer tragen, diese falsch herum aufhaben (L/R vertauscht), oder die räumlichen Klänge nicht richtig wahrnehmen können.</p>
                    <p>Das Experiment wird daher nun abgebrochen. Vielen Dank für Ihr Interesse.</p>
                </div>`);
            }
        }
    });

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
        timeline = timeline.concat(getInfoTrials());
        timeline.push(consentTrial);
        timeline.push(demoTrial);
        timeline.push(headphoneCheckTrial);
        timeline = timeline.concat(getScreeningTrials());
        
        timeline.push(createInstructionTrial(prompts.prompt1));
        timeline.push(createInstructionTrial(prompts.prompt2));
        timeline.push(createInstructionTrial(prompts.prompt3));
        timeline.push(createInstructionTrial(prompts.prompt4));
        timeline.push(createInstructionTrial(prompts.prompt5));
        timeline.push(createInstructionTrial(prompts.prompt6));
    }
    
    // The cue instruction needs the color configuration from the first row of CSV
    let cue_instruction_html = getCueInstruction(trial_data[0].Color);
    timeline.push(createInstructionTrial(cue_instruction_html));

    // 3. Main Trial Loop
    let trial_timeline = {
        timeline: [
            // Phase 0: Cue Presentation (with Fixation Cross and Arrows around it)
            {
                type: jsPsychHtmlKeyboardResponse,
                stimulus: function() {
                    let nonsingletonLoc = jsPsych.timelineVariable('Non-Singleton2Loc'); 
                    let singletonLoc = jsPsych.timelineVariable('SingletonLoc');
                    let colorStr = jsPsych.timelineVariable('Color'); 
                    let cueInstruction = jsPsych.timelineVariable('CueInstruction');

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
                data: { phase: 'cue' }
            },
            
            // Phase 1: Delay (Fixation only)
            {
                type: jsPsychHtmlKeyboardResponse,
                stimulus: '<div class="cue-screen"><div class="fixation">+</div></div>',
                choices: "NO_KEYS",
                trial_duration: function() {
                    return jsPsych.timelineVariable('cue_stim_delay_jitter') * 1000; 
                },
                data: { phase: 'delay' }
            },

            // Phase 2/3: Audio Stimulus & Virtual Response Box (1-9 Numpad)
            {
                type: jsPsychAudioButtonResponse,
                stimulus: function() {
                    let i = jsPsych.timelineVariable('original_index');
                    return `${audio_folder}s_${i}.wav`;
                },
                // 9 choices for the digits 1 through 9
                choices: ['1', '2', '3', '4', '5', '6', '7', '8', '9'],
                button_html: '<button class="jspsych-btn virtual-response-box">%choice%</button>',
                response_ends_trial: false,
                trial_duration: 1750, // response_duration = 1.75s
                data: {
                    phase: 'response',
                    targetDigit: jsPsych.timelineVariable('TargetDigit')
                },
                on_finish: function(data) {
                    // Score the response (choice 0 = '1', choice 8 = '9')
                    let selectedDigit = data.response + 1; 
                    data.correct = (selectedDigit === data.targetDigit);
                }
            },

            // Phase 4: ITI (Blank screen)
            {
                type: jsPsychHtmlKeyboardResponse,
                stimulus: '',
                choices: "NO_KEYS",
                trial_duration: function() {
                    return jsPsych.timelineVariable('ITI-Jitter') * 1000;
                },
                data: { phase: 'iti' }
            }
        ],
        timeline_variables: trial_data.map((row, idx) => ({...row, original_index: idx}))
    };
    
    timeline.push(trial_timeline);

    const save_data = {
        type: jsPsychPipe,
        action: "save",
        experiment_id: datapipe_id,
        filename: `sce-${subject}_block_${block}_data_${getFormattedDate()}.csv`,
        data_string: ()=>formatDataToCSV()
    };
    timeline.push(save_data);

    jsPsych.run(timeline);
}
