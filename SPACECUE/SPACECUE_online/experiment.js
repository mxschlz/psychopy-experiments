let global_all_blocks_data = {};
let current_block_global = 0;
let abort_experiment = false;
let exited_early = false;
let demo_headphone_type = null; // pilot v2: track playback device (Bluetooth/mono-downmix risk)
const datapipe_id = "p6rmFV5NMVaw";

// --- LANGUAGE FLAG ---------------------------------------------------------
// 'de' (default) or 'en'. Controls ALL instruction, feedback and UI text
// (info/consent pages, screening, tests, practice feedback, block summaries).
// NOTE: the task itself (spoken German digits) stays German in both settings.
const LANGUAGE = "en";
const L = (de, en) => (LANGUAGE === "en" ? en : de);

// --- DEBUG FLAG (?debug=1) --------------------------------------------------
// Testing aid: append &debug=1 to the URL (e.g. ...?subject=37&block=0&debug=1)
// to skip the whole intro battery (info/consent pages, demographics, headphone
// check, screening, spoken-digit demo, accuracy test, arrow test, ready screen)
// and jump straight to the two-stage practice and the main task. All DataPipe
// saves are disabled so debug runs can never pollute pilot data.
let DEBUG_MODE = false;

// English color key -> localized color name for on-screen cue descriptions.
const COLOR_NAME_MAP_DE = { "red": "rot", "green": "grün", "blue": "blau", "yellow": "gelb", "orange": "orange", "white": "weiß", "violet": "violett" };
function localizeColorName(engName) {
    return (LANGUAGE === "en") ? engName : (COLOR_NAME_MAP_DE[engName] || engName);
}


function formatDataToCSV(b) {
    let current_trial_data = global_all_blocks_data[b];
    let responses = jsPsych.data.get().filter({phase: 'response', is_practice: false, block: b}).values();
    let itis = jsPsych.data.get().filter({phase: 'iti', is_practice: false, block: b}).values();
    
    let export_data = current_trial_data.map(function(row, idx) {
        let resp_trial = responses.find(r => r.trial_nr === idx);
        let iti_trial = itis.find(r => r.trial_nr === idx);
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
        new_row.headphone_type = demo_headphone_type; // pilot v2: playback device tracking
        
        if (resp_trial && resp_trial.response !== null) {
            new_row.rt = resp_trial.rt ? resp_trial.rt / 1000 : null; // match python format (seconds)
            new_row.response = parseInt(resp_trial.response) + 1;
        } else if (iti_trial && iti_trial.response !== null) {
            new_row.rt = (iti_trial.rt + 1750) / 1000;
            new_row.response = parseInt(iti_trial.response) + 1;
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
            if (DEBUG_MODE) {
                // Debug runs never write to DataPipe; show the abort screen directly.
                document.body.innerHTML = `
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; color: white; background: #121212;">
                    <div class="glass-container" style="text-align: center; max-width: 600px;">
                        <h2 style="color: #ff6b6b;">${L("Experiment abgebrochen (Debug-Modus)", "Experiment Aborted (Debug Mode)")}</h2>
                        <p>${L("Debug-Modus: Es wurden keine Daten gespeichert.", "Debug mode: no data have been saved.")}</p>
                        <p>${L("Sie können dieses Fenster nun schließen.", "You may now close this window.")}</p>
                    </div>
                </div>`;
                return;
            }
            document.body.innerHTML = `
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; color: white; background: #121212;">
                <h2 style="color: #4da8da;">${L("Daten werden gespeichert...", "Saving data...")}</h2>
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
                            <h2 style="color: #ff6b6b;">${L("Experiment abgebrochen", "Experiment Aborted")}</h2>
                            <p>${L("Ihre Daten bis zu diesem Punkt wurden erfolgreich gespeichert.", "Your data up to this point have been saved successfully.")}</p>
                            <p>${L("Sie können dieses Fenster nun schließen.", "You may now close this window.")}</p>
                        </div>
                    </div>`;
                } else {
                    console.error("DataPipe Error:", result);
                    document.body.innerHTML = `
                    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; color: white; background: #121212;">
                        <div class="glass-container" style="text-align: center; max-width: 600px;">
                            <h2 style="color: #ff6b6b;">${L("Fehler beim Speichern", "Error While Saving")}</h2>
                            <p>${L("Leider ist ein Fehler beim Speichern aufgetreten. Details finden Sie in der Konsole.", "Unfortunately, an error occurred while saving. Details can be found in the browser console.")}</p>
                            <p>${L("Sie können dieses Fenster nun schließen.", "You may now close this window.")}</p>
                        </div>
                    </div>`;
                }
            }).catch((err) => {
                console.error("Fetch Error:", err);
                document.body.innerHTML = `
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; color: white; background: #121212;">
                    <div class="glass-container" style="text-align: center; max-width: 600px;">
                        <h2 style="color: #ff6b6b;">${L("Fehler beim Speichern", "Error While Saving")}</h2>
                        <p>${L("Leider ist ein Fehler beim Speichern aufgetreten.", "Unfortunately, an error occurred while saving.")}</p>
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
                    <h2 style="color: #4caf50;">${L("Das Experiment ist beendet.", "The experiment is finished.")}</h2>
                    <p>${L("Vielen Dank für Ihre Teilnahme!", "Thank you very much for your participation!")}</p>
                    <p>${L("Ihre Daten wurden erfolgreich auf dem Server gespeichert. Sie können dieses Fenster nun schließen.", "Your data have been saved successfully on the server. You may now close this window.")}</p>
                </div>
            </div>`;
        }
    }
});

let subject, prolific_pid, study_id, session_id, block, demo_age, demo_gender, demo_handedness, csv_path, audio_folder;

// Configure this to point to your Cloudflare R2 or OSF storage bucket link when deploying
const base_url = "https://pub-65f7c7cdfbd94569a681f48c959ee559.r2.dev/";

// Bind the exit button (label localized here so the flag also controls index.html)
let exitBtnEl = document.getElementById('exit-btn');
exitBtnEl.innerText = L("Abbrechen & Speichern", "Abort & Save");
exitBtnEl.addEventListener('click', function() {
    if (confirm(L("Möchten Sie das Experiment wirklich frühzeitig abbrechen? Ihre bisherigen Daten werden gespeichert.", "Do you really want to abort the experiment early? Your data collected so far will be saved."))) {
        exited_early = true;
        jsPsych.endExperiment();
    }
});

// --- PROMPTS FROM prompts.py ---
const prompts = {
    prompt1: L(`Willkommen und vielen Dank für die Teilnahme an diesem Experiment zur räumlichen Aufmerksamkeit.<br><br>
In jedem Durchgang des Experiments sollen Sie ein Zahlwort aus jeweils drei verschiedenen Zahlwörtern identifizieren.<br>
Versuchen Sie dabei stets, so korrekt und so schnell wie möglich zu antworten!<br>
Das Experiment ist in 6 Blöcke aufgeteilt, zwischen denen Sie kurze Pausen einlegen können.<br><br>
Drücken Sie LEERTASTE, um weiterzublättern.`, `Welcome and thank you very much for taking part in this experiment on spatial attention.<br><br>
In each trial of the experiment, your task is to identify one spoken digit out of three different spoken digits.<br>
Always try to answer as accurately and as quickly as possible!<br>
The experiment is divided into 6 blocks, between which you can take short breaks.<br><br>
Press SPACEBAR to continue.`),

    prompt2: L(`In jedem Durchgang des Experiments werden gleichzeitig drei Zahlwörter aus drei verschiedenen Richtungen abgespielt (links, mitte, rechts).<br>
Alle Zahlwörter werden von derselben Stimme gesprochen. Bei den Zahlwörtern handelt es sich um eine Auswahl der Zahlen zwischen 1 und 9.<br>
In einem Durchgang sind alle Ziffern einzigartig, z.B. kann die Zahl 9 nicht sowohl von links als auch von rechts gleichzeitig ertönen.<br><br>
Drücken Sie LEERTASTE, um weiterzublättern.`, `In each trial of the experiment, three spoken digits are played simultaneously from three different directions (left, center, right).<br>
All digits are spoken by the same voice. The digits are a selection of the numbers between 1 and 9.<br>
Within a trial, all digits are unique; for example, the number 9 cannot sound from the left and the right at the same time.<br><br>
Press SPACEBAR to continue.`),

    prompt3: L(`Das Zahlwort, welches Sie identifizieren sollen, unterscheidet sich von den anderen beiden in der folgenden Eigenschaft:<br>
Dieses Zahlwort klingt im Vergleich zu den restlichen Zahlwörtern sehr rau und kratzig.<br>
Die Stimme dieses Wortes klingt wie in einer schlechten Telefonverbindung.<br>
Auf genau dieses Zahlwort sollen Sie sich konzentrieren und die Zahl so schnell wie möglich angeben!<br><br>
Drücken Sie LEERTASTE, um weiterzublättern.`, `The spoken digit you are supposed to identify differs from the other two in the following way:<br>
Compared to the remaining digits, this digit sounds very rough and raspy.<br>
The voice of this digit sounds like a bad phone connection.<br>
You should concentrate on exactly this digit and report the number as quickly as possible!<br><br>
Press SPACEBAR to continue.`),

    prompt4: L(`In allen Durchgängen hat eines der zwei weiteren Zahlwörter eine andere Tonhöhe. Dieses Zahlwort ist ein Störreiz und klingt wie eine Kinderstimme.<br>
Lassen Sie sich davon nicht irritieren: Ihre Aufgabe bleibt es, stets das raue, kratzige Zahlwort zu benennen.<br><br>
Drücken Sie LEERTASTE, um weiterzublättern.`, `In every trial, one of the two remaining digits has a different pitch. This digit is a distractor and sounds like a child's voice.<br>
Do not let it distract you: your task remains to always name the rough, raspy digit.<br><br>
Press SPACEBAR to continue.`),

    prompt5: L(`Während des Experiments erscheint eine Antwort-Box in der Mitte des Bildschirms.<br>
Diese enthält die Ziffern von 1 bis 9 und ist durch einen Rahmen begrenzt.<br>
Mit der Maus können Sie auf eine Zahl pro Durchgang klicken, um das raue, kratzige Zahlwort anzugeben.<br>
ACHTUNG: die Antwort ist nur gültig, wenn der Mauszeiger nach dem Klicken verschwindet! Bitte stellen Sie sicher, dass Sie in jedem Durchgang eine Antwort geben, da ansonsten Ihre Daten unvollständig sind und nicht gewertet werden können.<br><br>
Drücken Sie LEERTASTE, um weiterzublättern.`, `During the experiment, a response box appears in the center of the screen.<br>
It contains the digits 1 to 9 and is bounded by a frame.<br>
With the mouse, you can click one number per trial to report the rough, raspy digit.<br>
ATTENTION: the response is only valid if the mouse cursor disappears after the click! Please make sure that you give a response in every trial; otherwise your data will be incomplete and cannot be evaluated.<br><br>
Press SPACEBAR to continue.`),

    prompt6: L(`Sollten Sie zu langsam antworten, färbt sich der Rahmen der Box für eine kurze Zeit rot.<br>
Das ist dann der Hinweis, dass Sie in den kommenden Durchgängen etwas schneller antworten sollen.<br>
Bitte halten Sie Ihren Blick während der Aufgabe stets auf die Antwort-Box gerichtet.<br>
Die Zahlenfelder treten etwas hervor, wenn Sie den Mauszeiger über sie bewegen.<br>
Drücken Sie LEERTASTE, um weiterzublättern.`, `If you respond too slowly, the frame of the box briefly turns red.<br>
This is the signal that you should respond somewhat faster in the upcoming trials.<br>
Please keep your gaze directed at the response box at all times during the task.<br>
The number fields stand out slightly when you move the mouse cursor over them.<br>
Press SPACEBAR to continue.`)
};

function getBlockReminderTrial(trial_data) {
    let informative_trial = trial_data.find(t => t.CueInstruction !== 'cue_neutral');
    let n_cue_inst = informative_trial ? informative_trial.CueInstruction : 'cue_neutral';
    let n_colorStr = trial_data[0].Color;
    let info = n_colorStr.split("-");
    let targetColor = info[1].toLowerCase();
    let distractorColor = info[3].toLowerCase();
    let controlColor = info[5].toLowerCase();
    
    const hexMap = { "red": "#ff6b6b", "green": "#4caf50", "blue": "#4da8da", "yellow": "#ffeb3b", "orange": "#ffa726", "white": "#ffffff", "violet": "#b388ff" };
    
    let active_color_eng = "";
    let cue_desc = "";
    
    if (n_cue_inst.includes('target_location')) {
        active_color_eng = targetColor;
        cue_desc = L("den <strong>Zielreiz</strong> (raue Stimme)", "the <strong>target stimulus</strong> (rough voice)");
    } else if (n_cue_inst.includes('distractor_location')) {
        active_color_eng = distractorColor;
        cue_desc = L("den <strong>Störreiz</strong> (Kinderstimme)", "the <strong>distractor</strong> (child's voice)");
    } else if (n_cue_inst.includes('nonsingleton_location')) {
        active_color_eng = controlColor;
        cue_desc = L("die <strong>Normale Stimme</strong>", "the <strong>normal voice</strong>");
    }
    
    let active_ger = localizeColorName(active_color_eng);
    let active_hex = hexMap[active_color_eng] || active_color_eng;
    let highlight = `<span style="color: ${active_hex}; font-weight: bold; text-transform: uppercase;">${active_ger}</span>`;
    
    return {
        type: jsPsychHtmlKeyboardResponse,
        stimulus: `
        <div class="instruction-text">
            <h2 style="color: #4da8da; margin-bottom: 20px;">${L("Wichtige Information zum aktuellen Block", "Important Information About the Current Block")}</h2>
            <p style="font-size: 18px;">${L(`In diesem Block gibt Ihnen der farbige Pfeil einen Hinweis auf ${cue_desc}.`, `In this block, the colored arrow gives you a cue about ${cue_desc}.`)}</p>
            <p style="font-size: 18px;">${L(`Achten Sie also auf den Pfeil mit der Farbe ${highlight}!`, `So pay attention to the arrow with the color ${highlight}!`)}</p>
            <p style="margin-top: 40px; color: #aaa;">${L("Drücken Sie die <strong>LEERTASTE</strong>, um sofort fortzufahren.<br>(Dieses Fenster schließt sich automatisch nach 15 Sekunden)", "Press the <strong>SPACEBAR</strong> to continue immediately.<br>(This window closes automatically after 15 seconds)")}</p>
        </div>`,
        choices: [" "],
        trial_duration: 15000
    };
}

function getCueInstruction(colorStr) {
    let trg_ger = L("weiß", "white");
    let d_ger = L("weiß", "white");
    let c_ger = L("weiß", "white");
    let trg_col = "#ffffff";
    let d_col = "#ffffff";
    let c_col = "#ffffff";
    
    if (colorStr) {
        let info = colorStr.split("-");
        if (info.length >= 6) {
            let targetColor = info[1].toLowerCase();
            let distractorColor = info[3].toLowerCase();
            let controlColor = info[5].toLowerCase();
            const hexMap = { "red": "#ff6b6b", "green": "#4caf50", "blue": "#4da8da", "yellow": "#ffeb3b", "orange": "#ffa726", "white": "#ffffff", "violet": "#b388ff" };
            
            trg_ger = localizeColorName(targetColor);
            d_ger = localizeColorName(distractorColor);
            c_ger = localizeColorName(controlColor);
            trg_col = hexMap[targetColor] || targetColor;
            d_col = hexMap[distractorColor] || distractorColor;
            c_col = hexMap[controlColor] || controlColor;
        }
    }
    
    let trg_highlight = `<span style="color: ${trg_col}; font-weight: bold; text-transform: uppercase;">${trg_ger}</span>`;
    let d_highlight = `<span style="color: ${d_col}; font-weight: bold; text-transform: uppercase;">${d_ger}</span>`;
    let c_highlight = `<span style="color: ${c_col}; font-weight: bold; text-transform: uppercase;">${c_ger}</span>`;
    
    let colored_arrow_description = L(
        `In anderen Durchgängen besitzt ein Pfeil entweder die Farbe ${trg_highlight}, ${d_highlight} oder ${c_highlight}.`,
        `In other trials, one of the arrows has either the color ${trg_highlight}, ${d_highlight} or ${c_highlight}.`
    );
    
    return L(`In jedem Durchgang werden Ihnen drei Pfeile angezeigt, welche in drei Richtungen zeigen (der linke Pfeil für links, der obere Pfeil für die Mitte / geradeaus, der rechte Pfeil für rechts).<br>
In einigen Durchgängen sind alle Pfeile farblos. ${colored_arrow_description}<br>
Dieser Pfeil ist nützlich, denn er zeigt, welche Art von Zahlwort aus dieser Richtung kommen wird.<br>
Die Farbe gibt dabei an, um welche Art von Zahlwort es sich handelt.<br>
Ist der Pfeil ${trg_highlight}, handelt es sich um das raue Zahlwort, auf das Sie reagieren sollen (Zielreiz).<br>
Ist der Pfeil ${d_highlight}, handelt es sich um das hohe Zahlwort, welches sich wie eine Kinderstimme anhört (Störreiz).<br>
Ist der Pfeil ${c_highlight}, handelt es sich um das Zahlwort mit normaler Stimme.<br><br>
<b>Wichtig:</b> In einem bestimmten Block wird immer nur <b>eine</b> dieser drei Hinweis-Farben (zusammen mit den farblosen Pfeilen) verwendet.<br>
Sie werden vor jedem Block darüber informiert, auf welche Farbe Sie in diesem Block achten müssen!<br><br>
Drücken Sie LEERTASTE, um weiterzublättern.`, `In every trial, three arrows are shown to you, pointing in three directions (the left arrow for left, the top arrow for center / straight ahead, the right arrow for right).<br>
In some trials, all arrows are colorless. ${colored_arrow_description}<br>
This arrow is useful, because it indicates which kind of spoken digit will come from that direction.<br>
The color tells you which kind of spoken digit it is.<br>
If the arrow is ${trg_highlight}, it is the rough digit to which you should respond (target stimulus).<br>
If the arrow is ${d_highlight}, it is the high-pitched digit that sounds like a child's voice (distractor).<br>
If the arrow is ${c_highlight}, it is the digit with the normal voice.<br><br>
<b>Important:</b> In any given block, only <b>one</b> of these three cue colors is used (alongside the colorless arrows).<br>
Before each block, you will be informed about which color you need to pay attention to in that block!<br><br>
Press SPACEBAR to continue.`);
}

// Reusable instruction trial factory
function createInstructionTrial(htmlContentArray) {
    if (!Array.isArray(htmlContentArray)) {
        htmlContentArray = [htmlContentArray];
    }
    
    let pages = htmlContentArray.map(htmlContent => {
        // Remove spacebar prompts if they happen to exist in the html
        // (strip both languages so cleanup works regardless of LANGUAGE)
        htmlContent = htmlContent.replace("[Drücken Sie LEERTASTE, um weiterzublättern]", "");
        htmlContent = htmlContent.replace("Drücken Sie LEERTASTE, um weiterzublättern.", "");
        htmlContent = htmlContent.replace("Drücken Sie LEERTASTE, um zu beginnen.", "");
        htmlContent = htmlContent.replace("[Press SPACEBAR to continue]", "");
        htmlContent = htmlContent.replace("Press SPACEBAR to continue.", "");
        htmlContent = htmlContent.replace("Press SPACEBAR to begin.", "");
        return `<div class="instruction-text">${htmlContent}</div>`;
    });
    
    return {
        type: jsPsychInstructions,
        pages: pages,
        show_clickable_nav: true,
        button_label_previous: L("Zurück", "Back"),
        button_label_next: L("Weiter", "Next"),
        allow_keys: true,
        key_forward: "ArrowRight",
        key_backward: "ArrowLeft"
    };
}

function getInfoTrials() {
    // English info pages (working translation of the German legal text below).
    if (LANGUAGE === "en") {
        let pagesEn = [
`<div class="instruction-text" style="text-align: left; overflow-y: auto; max-height: 70vh; padding-right: 15px;">
    <p style="color: #f1f5f9; margin-bottom: 12px;">Dear Madam, dear Sir,</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">Thank you very much for your interest in our study!</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">In the following, we provide you with basic information about the study and the planned measurements. We also inform you about how the collected data will be handled and state the exclusion criteria for participation in the study.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">Please read this study information carefully and contact the study team if you have any questions (for contact details, see section 4).</p>
</div>`,

`<div class="instruction-text" style="text-align: left; overflow-y: auto; max-height: 70vh; padding-right: 15px;">
    <h3 style="color: #4da8da; margin-top: 25px; border-bottom: 1px solid rgba(77, 168, 218, 0.3); padding-bottom: 5px;"><strong>1. Study Objectives</strong></h3>
    <p style="color: #f1f5f9; margin-bottom: 12px;">With this study, we hope to gain new insights into the behavioral mechanisms at work when people direct their auditory attention onto a specific task.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">For this purpose, various spatial acoustic stimuli will be played to you, and you should attend to only one of these stimuli at a time.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">At the end of each trial, you will answer a question about the identity of the relevant acoustic stimulus.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">Before the actual experiment, there is an introduction during which you can familiarize yourself with the procedure of the experiment.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">By participating, you would make an important contribution to basic research in cognitive psychology on the topic of attention.</p>
</div>`,

`<div class="instruction-text" style="text-align: left; overflow-y: auto; max-height: 70vh; padding-right: 15px;">
    <h3 style="color: #4da8da; margin-top: 25px; border-bottom: 1px solid rgba(77, 168, 218, 0.3); padding-bottom: 5px;"><strong>2. Study Scope, Planned Procedure, Risks and Compensation</strong></h3>
    <p style="color: #f1f5f9; margin-bottom: 12px;">The study consists of a single session lasting approximately 60 minutes. Participation takes place online.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">Please note that the study cannot be run on mobile phones or tablets, because you need a keyboard.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">Furthermore, headphones are <strong>strictly</strong> required.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">The study comprises several parts, which we intend to conduct within a single session.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">All steps are described in detail below for your information.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">The following section contains details about the course of the study.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">The study is divided into the following parts:</p>
    <p style="margin-left: 20px; color: #e2e8f0;">1. Written information for the participant.</p>
    <p style="margin-left: 20px; color: #e2e8f0;">2. Collection of personal data (age, handedness and gender).</p>
    <p style="margin-left: 20px; color: #e2e8f0;">3. Your performance of the attention task.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">There are no discernible risks for you. You will receive compensation of 12 euros per hour.</p>
</div>`,
`<div class="instruction-text" style="text-align: left; overflow-y: auto; max-height: 70vh; padding-right: 15px;">
    <h3 style="color: #4da8da; margin-top: 25px; border-bottom: 1px solid rgba(77, 168, 218, 0.3); padding-bottom: 5px;"><strong>3. Inclusion and Exclusion Criteria</strong></h3>
    <ul style="margin-left: 20px; line-height: 1.8;">
        <li style="margin-top: 10px; font-weight: 600;">Inclusion criteria:</li>
        <li style="color: #4caf50;">18 - 35 years</li>
        <li style="color: #4caf50;">Ability to give informed consent to participate in the experiment</li>
        <li style="margin-top: 10px; font-weight: 600;">Exclusion criteria:</li>
        <li style="color: #ff6b6b;">Neurological or audiological disorders, e.g. wearing a hearing aid or a recent stroke</li>
        <li style="color: #ff6b6b;">Inability to carry out the experimental tasks according to the instructions</li>
        <li style="color: #ff6b6b;">Inability to give informed consent</li>
    </ul>
</div>`,
`<div class="instruction-text" style="text-align: left; overflow-y: auto; max-height: 70vh; padding-right: 15px;">
    <h3 style="color: #4da8da; margin-top: 25px; border-bottom: 1px solid rgba(77, 168, 218, 0.3); padding-bottom: 5px;"><strong>4. Data Protection Information</strong></h3>
    <p style="color: #f1f5f9; margin-bottom: 12px;">The collected data are pseudonymized<sup style="color: #4da8da; font-weight: bold; margin-left: 2px;">1</sup> and can be traced back to the individual participant via a code in the project database.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">The database is located on a server of the IT Service Center of the University of Lübeck (ITSC, https://www.itsc.uni-luebeck.de/dienstleistungen/it-sicherheit/firewall-und-idp.html),</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">which is protected by a firewall as well as an intrusion detection and intrusion prevention system (IDS).</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">Study-relevant data are backed up in a RAID-based archive system on site.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">Data are transferred only within the protected LAN or via the encrypted wireless networks of the University of Lübeck.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">All members of the "Auditory Cognition" working group sign a data protection and confidentiality agreement on their first day of work.</p>
    <p style="color: #f1f5f9; margin-bottom: 8px;">Responsible for data processing:</p>
    <div style="background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 15px; margin: 10px 0 20px 0;">
    <p style="color: #f1f5f9; margin-bottom: 4px;">Max Schulz, M.Sc.</p>
    <p style="color: #f1f5f9; margin-bottom: 4px;">Maria-Goeppert-Straße 9a</p>
    <p style="color: #f1f5f9; margin-bottom: 4px;">23562 Lübeck</p>
    <p style="color: #f1f5f9; margin-bottom: 4px;">Building MFC 8, 1st floor, Room 5</p>
    <p style="color: #f1f5f9; margin-bottom: 4px;">Tel.: +49 451 3101 3647</p>
    <p style="color: #f1f5f9; margin-bottom: 4px;">E-Mail: (<a href="mailto:max.schulz@uni-luebeck.de" style="color: #4da8da; text-decoration: none; font-weight: 600;">max.schulz@uni-luebeck.de</a>)</p>
    </div>
    <p style="color: #f1f5f9; margin-bottom: 12px;">Data collection takes place for the purpose of the study objective stated above.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">Personal data (addresses, names, etc.) are treated as strictly confidential and in accordance with statutory provisions.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">The data collected in the experiment are stored and analyzed electronically in pseudonymized form, i.e. without direct reference to your name.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">For the later analysis, the data of all participants are used in fully anonymized<sup style="color: #4da8da; font-weight: bold; margin-left: 2px;">2</sup> form.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">The provisions of data protection law are complied with.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">Only members of the study team have access to your data.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">These persons are bound to confidentiality. The data are protected against access by third parties.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">You have the right to information about the data concerning you, including in the form of a free copy.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">If you withdraw your consent, you have the right to request the deletion of the data collected up to that point.</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">For this purpose, please contact Max Schulz (<a href="mailto:max.schulz@uni-luebeck.de" style="color: #4da8da; text-decoration: none; font-weight: 600;">max.schulz@uni-luebeck.de</a>).</p>
    <p style="color: #f1f5f9; margin-bottom: 8px;">In the event of a complaint, please contact the Data Protection Officer of the University of Lübeck:</p>
    <div style="background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 15px; margin: 10px 0 20px 0;">
    <p style="color: #f1f5f9; margin-bottom: 4px;">x-tention Informationstechnologie GmbH</p>
    <p style="color: #f1f5f9; margin-bottom: 4px;">Margot-Becke-Ring 37, 69124 Heidelberg</p>
    <p style="color: #f1f5f9; margin-bottom: 4px;">Phone: 0451 3101 1903</p>
    <p style="color: #f1f5f9; margin-bottom: 4px;">E-Mail: <a href="mailto:datenschutz@uni-luebeck.de" style="color: #4da8da; text-decoration: none; font-weight: 600;">datenschutz@uni-luebeck.de</a></p>
    </div>
    <p style="color: #f1f5f9; margin-bottom: 8px;">You can also address a complaint to the competent data protection authority:</p>
    <div style="background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 15px; margin: 10px 0 20px 0;">
    <p style="color: #f1f5f9; margin-bottom: 4px;">Unabhängiges Landeszentrum für Datenschutz Schleswig-Holstein (Independent State Center for Data Protection)</p>
    <p style="color: #f1f5f9; margin-bottom: 4px;">Holstenstraße 98, 24103 Kiel</p>
    <p style="color: #f1f5f9; margin-bottom: 4px;">E-Mail: <a href="mailto:mail@datenschutzzentrum.de" style="color: #4da8da; text-decoration: none; font-weight: 600;">mail@datenschutzzentrum.de</a></p>
    </div>
    <p style="color: #f1f5f9; margin-bottom: 12px;">Thank you very much!</p>
    <p style="color: #f1f5f9; margin-bottom: 12px;">Max Schulz</p>
    <hr style="border: 0; border-top: 1px solid rgba(255, 255, 255, 0.1); margin: 20px 0;">
    <div style="font-size: 14px; color: #94a3b8; margin-top: 12px; padding-left: 12px; border-left: 3px solid #3b82f6; font-style: italic; background: rgba(59, 130, 246, 0.05); padding-top: 8px; padding-bottom: 8px; border-radius: 0 8px 8px 0;">
        <p style="margin: 0 0 5px 0;"><strong style="color: #4da8da; font-size: 16px; margin-right: 5px;">1</strong> <strong>Pseudonymization:</strong> "'pseudonymisation' means the processing of personal data in such a manner</p>
        <p style="margin: 0 0 5px 0;">that the personal data can no longer be attributed to a specific data subject without the use of additional information,</p>
        <p style="margin: 0 0 5px 0;">provided that such additional information is kept separately and is subject to technical and organisational measures</p>
        <p style="margin: 0 0 5px 0;">to ensure that the personal data are not attributed to an identified or identifiable natural person;"</p>
        <p style="margin: 0 0 5px 0;">Article 4(5) GDPR</p>
    </div>
    <div style="font-size: 14px; color: #94a3b8; margin-top: 12px; padding-left: 12px; border-left: 3px solid #3b82f6; font-style: italic; background: rgba(59, 130, 246, 0.05); padding-top: 8px; padding-bottom: 8px; border-radius: 0 8px 8px 0;">
        <p style="margin: 0 0 5px 0;"><strong style="color: #4da8da; font-size: 16px; margin-right: 5px;">2</strong> <strong>Anonymization:</strong> "the alteration of personal data in such a way that details about personal or factual circumstances can no longer, or only with a disproportionate</p>
        <p style="margin: 0 0 5px 0;">expenditure of time, cost and labour, be attributed to an identified or identifiable natural person." §3(6) BDSG</p>
    </div>
</div>`
        ];
        return [{
            type: jsPsychInstructions,
            pages: pagesEn,
            show_clickable_nav: true,
            button_label_previous: "Back",
            button_label_next: "Next",
            allow_keys: true,
            key_forward: "ArrowRight",
            key_backward: "ArrowLeft"
        }];
    }

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
        button_label_previous: L("Zurück", "Back"),
        button_label_next: L("Weiter", "Next"),
        allow_keys: true,
        key_forward: "ArrowRight",
        key_backward: "ArrowLeft"
    }];
}

const consentTrial = {
    type: jsPsychHtmlButtonResponse,
    stimulus: L(`<div class="instruction-text">
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
    </div>`, `<div class="instruction-text">
        <div style="text-align: left; padding: 0 20px;">
            <h2 style="color: white; margin-bottom: 20px; text-align: center;">DECLARATION OF CONSENT</h2>
            <p>I hereby confirm that I have been informed about the nature, significance, risks and implications of the intended study, and that I had sufficient time to consider my decision.</p>
            <p>I have been made aware that my participation is voluntary and that I have the right to end it at any time without giving reasons, without any disadvantage arising from this.</p>
            <p>I have understood that I may abort the study at any time without giving reasons, and that I have the right to have my data deleted.</p>
            <p>I agree to take part in the behavioral psychological study. I agree that my behavioral data will be recorded and stored.</p>
            <p>I agree that the data collected from me may be used in anonymized form for publication purposes.</p>
            <div style="text-align: center; margin-top: 30px; padding: 20px; background: rgba(0,0,0,0.2); border-radius: 12px;">
                Please select an option below.
            </div>
        </div>
    </div>`),
    choices: [L('Zurück zu den Informationen', 'Back to the information'), L('Nein, abbrechen', 'No, cancel'), L('Ja, ich stimme zu', 'Yes, I agree')],
    button_html: [
        '<button class="jspsych-btn" style="margin: 10px; background-color: #555;">%choice%</button>',
        '<button class="jspsych-btn" style="margin: 10px; background-color: #f44336;">%choice%</button>',
        '<button class="jspsych-btn" style="margin: 10px; background-color: #4caf50;">%choice%</button>'
    ],
    on_finish: function(data) {
        if (data.response === 1) {
            abort_experiment = true;
            jsPsych.endExperiment(L(`<div class="instruction-text">Sie haben nicht zugestimmt. Das Experiment wird abgebrochen. Vielen Dank für Ihr Interesse.</div>`, `<div class="instruction-text">You have not given your consent. The experiment will now be aborted. Thank you very much for your interest.</div>`));
        }
    }
};

function getHeadphoneCheckTrial() {
    return createInstructionTrial(L(`
        <div style="text-align: left;">
            <h2 style="color: #4da8da; margin-bottom: 20px;">Kopfhörer-Test & Lautstärke</h2>
            <p>Dieses Experiment erfordert das Tragen von Kopfhörern. Bitte stellen Sie sicher, dass Sie diese jetzt aufgesetzt haben.</p>
            <p>Klicken Sie auf den Button unten, um einen Testton abzuspielen. Passen Sie die Systemlautstärke Ihres Computers so an, dass Sie den Ton klar und deutlich hören können, er aber nicht unangenehm laut ist.</p>
            <div style="text-align: center;">
                <audio id="test-audio" src="${base_url}sequences/sce-${subject}_block_0/s_0.wav" preload="auto"></audio>
                <button class="jspsych-btn" style="margin: 20px 0; background-color: #4caf50;" onclick="document.getElementById('test-audio').play();">Testton abspielen</button>
            </div>
            <p style="color: #ff6b6b; font-weight: bold;">WICHTIG: Bitte verändern Sie die Lautstärke nach diesem Test während des restlichen Experiments nicht mehr!</p>
        </div>`, `
        <div style="text-align: left;">
            <h2 style="color: #4da8da; margin-bottom: 20px;">Headphone Test & Volume</h2>
            <p>This experiment requires wearing headphones. Please make sure that you have put them on now.</p>
            <p>Click the button below to play a test tone. Adjust your computer's system volume so that you can hear the tone clearly and distinctly, but not uncomfortably loud.</p>
            <div style="text-align: center;">
                <audio id="test-audio" src="${base_url}sequences/sce-${subject}_block_0/s_0.wav" preload="auto"></audio>
                <button class="jspsych-btn" style="margin: 20px 0; background-color: #4caf50;" onclick="document.getElementById('test-audio').play();">Play test tone</button>
            </div>
            <p style="color: #ff6b6b; font-weight: bold;">IMPORTANT: Please do not change the volume after this test for the rest of the experiment!</p>
        </div>`));
}

function getScreeningTrials() {
    let screeningTimeline = [];
    const screening_audio_folder = `${base_url}screening_stimuli/`;
    
    // Localization Instructions
    screeningTimeline.push(createInstructionTrial(L(`
        <div style="text-align: center;">
            <h2 style="color: #4da8da;">Kopfhörer-Screening: Teil 1 (Ortung)</h2>
            <p>Wir prüfen nun, ob Ihr System die räumlichen Klänge korrekt wiedergibt.</p>
            <p>Sie werden gleich ein einzelnes gesprochenes Zahlwort hören. Ihre Aufgabe ist es anzugeben, aus welcher <strong>Richtung</strong> das Wort kam.</p>
            <br>
            <p style="color: #ff6b6b;">Wenn Sie einen Kopfhörer falsch herum aufhaben, werden Sie Fehler machen. Bitte prüfen Sie den Sitz (L/R) Ihrer Kopfhörer!</p>
        </div>
    `, `
        <div style="text-align: center;">
            <h2 style="color: #4da8da;">Headphone Screening: Part 1 (Localization)</h2>
            <p>We will now check whether your system plays back the spatial sounds correctly.</p>
            <p>You will hear a single spoken digit. Your task is to indicate from which <strong>direction</strong> the word came.</p>
            <br>
            <p style="color: #ff6b6b;">If your headphones are on the wrong way round, you will make errors. Please check that your headphones are seated correctly (L/R)!</p>
        </div>
    `)));

    // Localized direction labels (used for both the buttons and the scoring)
    const loc_labels = L(['Links', 'Mitte', 'Rechts'], ['Left', 'Center', 'Right']);

    const loc_trials = [
        { file: '4_loc1.wav', correct_loc: loc_labels[0] },
        { file: '7_loc3.wav', correct_loc: loc_labels[2] },
        { file: '2_loc2.wav', correct_loc: loc_labels[1] }
    ];

    let screening_errors = 0;

    for (let t of loc_trials) {
        screeningTimeline.push({
            type: jsPsychAudioButtonResponse,
            stimulus: screening_audio_folder + t.file,
            choices: loc_labels.slice(),
            prompt: `<div style="margin-top:20px; font-size: 20px; color: white;">${L("Aus welcher Richtung kam der Ton?", "From which direction did the sound come?")}</div>`,
            button_html: '<button class="jspsych-btn virtual-response-box screening-btn" style="margin: 0 10px;">%choice%</button>',
            on_finish: function(data) {
                let selected_choice = loc_labels[data.response];
                if (selected_choice !== t.correct_loc) screening_errors++;
            }
        });
    }

    // Identification Instructions
    screeningTimeline.push(createInstructionTrial(L(`
        <div style="text-align: center;">
            <h2 style="color: #4da8da;">Kopfhörer-Screening: Teil 2 (Erkennung)</h2>
            <p>Nun prüfen wir, ob Sie die Zahlwörter gut verstehen können.</p>
            <p>Sie werden wieder einzelne Zahlwörter hören. Ihre Aufgabe ist es nun anzugeben, <strong>welche Zahl (1-9)</strong> gesprochen wurde.</p>
        </div>`, `
        <div style="text-align: center;">
            <h2 style="color: #4da8da;">Headphone Screening: Part 2 (Identification)</h2>
            <p>Now we check whether you can understand the spoken digits well.</p>
            <p>You will again hear single spoken digits. Your task now is to indicate <strong>which number (1-9)</strong> was spoken.</p>
        </div>`)));

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
            prompt: `<div style="margin-top:20px; font-size: 20px; color: white;">${L("Welches Zahlwort haben Sie gehört?", "Which digit did you hear?")}</div>`,
            button_html: '<button class="jspsych-btn virtual-response-box" style="margin: 0 5px;">%choice%</button>',
            on_finish: function(data) {
                let selected_choice = ['1','2','3','4','5','6','7','8','9'][data.response];
                if (selected_choice !== t.correct_id) screening_errors++;
            }
        });
    }
    
    let finish_trial = createInstructionTrial(L(`
        <div style="text-align: center;">
            <h2 style="color: #4caf50;">Screening beendet!</h2>
        </div>
    `, `
        <div style="text-align: center;">
            <h2 style="color: #4caf50;">Screening complete!</h2>
        </div>
    `));
    finish_trial.on_finish = function() {
        if (screening_errors > 0) {
            abort_experiment = true;
            jsPsych.endExperiment(L(`<div class="instruction-text" style="text-align: center; max-width: 600px;">
                <h2 style="color: #ff6b6b;">Screening nicht bestanden</h2>
                <p>Leider haben Sie einen oder mehrere Fehler im Screening gemacht.</p>
                <p>Dies deutet darauf hin, dass Sie entweder keine Kopfhörer tragen, diese falsch herum aufhaben (L/R vertauscht), oder die räumlichen Klänge nicht richtig wahrnehmen können.</p>
                <p>Das Experiment wird daher nun abgebrochen. Vielen Dank für Ihr Interesse.</p>
            </div>`, `<div class="instruction-text" style="text-align: center; max-width: 600px;">
                <h2 style="color: #ff6b6b;">Screening not passed</h2>
                <p>Unfortunately, you made one or more errors in the screening.</p>
                <p>This indicates that you are either not wearing headphones, are wearing them the wrong way round (L/R swapped), or cannot perceive the spatial sounds correctly.</p>
                <p>The experiment will therefore now be aborted. Thank you very much for your interest.</p>
            </div>`));
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
    // ?debug=1 (also 'true'/'yes'): skip the intro battery and all DataPipe saves.
    DEBUG_MODE = ['1', 'true', 'yes'].includes((urlParams.get('debug') || '').toLowerCase());
    if (DEBUG_MODE) {
        console.log('[SPACECUE DEBUG] ?debug=1 active: intro/consent/screening/tests skipped, DataPipe saves disabled - starting at the practice trials.');
    }
    demo_age = urlParams.get('age') || null;
    demo_gender = urlParams.get('gender') || null;
    demo_handedness = urlParams.get('handedness') || null;

    let start_block = parseInt(block);
    let all_blocks_data = [];

    try {
        for (let b = start_block; b < 6; b++) {
            let b_csv_path = `${base_url}sequences/sce-${subject}_block_${b}.csv`;
            const response = await fetch(b_csv_path);
            if (!response.ok) throw new Error(L("CSV konnte nicht geladen werden: ", "CSV could not be loaded: ") + b_csv_path);
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
        document.body.innerHTML = `<h1>${L("Fehler beim Laden der Sequenz!", "Error loading the sequence!")}</h1>
        <p style="color:red;">${error.message}</p>`;
    }
})();

const demoTrial = {
    type: jsPsychSurveyHtmlForm,
    preamble: L(`<div class="instruction-text" style="text-align: left;">
        <h2 style="color: #4da8da;">Demographische Daten</h2>
        <p>Bitte geben Sie Ihre Daten ein:</p>
    </div>`, `<div class="instruction-text" style="text-align: left;">
        <h2 style="color: #4da8da;">Demographic Data</h2>
        <p>Please enter your details:</p>
    </div>`),
    html: L(`
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
            <p style="margin-top: 15px;">Mit welchem Gerät hören Sie die Klänge?</p>
            <select id="headphone_type" name="headphone_type" required style="padding: 10px; border-radius: 5px; font-size: 16px;">
                <option value="" disabled selected>Bitte wählen...</option>
                <option value="wired">Kabelgebundene Kopfhörer</option>
                <option value="wireless">Funk-/Bluetooth-Kopfhörer</option>
                <option value="builtin">Eingebaute Lautsprecher (Laptop/Handy)</option>
                <option value="external">Externe Lautsprecher</option>
            </select>
        </div>
    `, `
        <div style="text-align: left; color: white; margin-bottom: 20px; font-size: 18px;">
            <p>Age:</p>
            <input type="number" id="age" name="age" required min="18" max="99" style="padding: 10px; border-radius: 5px; width: 100px; font-size: 16px;">
            <p style="margin-top: 15px;">Gender:</p>
            <select id="gender" name="gender" required style="padding: 10px; border-radius: 5px; font-size: 16px;">
                <option value="" disabled selected>Please select...</option>
                <option value="m">Male</option>
                <option value="w">Female</option>
                <option value="d">Diverse</option>
            </select>
            <p style="margin-top: 15px;">Handedness:</p>
            <select id="handedness" name="handedness" required style="padding: 10px; border-radius: 5px; font-size: 16px;">
                <option value="" disabled selected>Please select...</option>
                <option value="r">Right-handed</option>
                <option value="l">Left-handed</option>
            </select>
            <p style="margin-top: 15px;">Which device are you using to listen to the sounds?</p>
            <select id="headphone_type" name="headphone_type" required style="padding: 10px; border-radius: 5px; font-size: 16px;">
                <option value="" disabled selected>Please select...</option>
                <option value="wired">Wired headphones</option>
                <option value="wireless">Wireless/Bluetooth headphones</option>
                <option value="builtin">Built-in speakers (laptop/phone)</option>
                <option value="external">External speakers</option>
            </select>
        </div>
    `),
    button_label: L('Weiter', 'Next'),
    on_finish: function(data) {
        demo_age = data.response.age;
        demo_gender = data.response.gender;
        demo_handedness = data.response.handedness;
        demo_headphone_type = data.response.headphone_type;
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
        
        // Screening/demo/accuracy audio is only needed for the intro battery,
        // which ?debug=1 skips - do not preload it in debug mode.
        if (current_block_num === 0 && !DEBUG_MODE) {
            ['4_loc1.wav', '7_loc3.wav', '2_loc2.wav', '8_loc2.wav', '3_loc1.wav', '5_loc3.wav'].forEach(f => {
                audio_files.push(`${base_url}screening_stimuli/${f}`);
            });
            ['1','2','3','4','5','6','7','8','9'].forEach(d => {
                audio_files.push(`${base_url}stimuli/targets_low_30_Hz/${d}_amplitude_modulated_30.wav`);
                audio_files.push(`${base_url}stimuli/digits_all_250ms/${d}.wav`);
            });
        }
        
        // 1b. Single-cue-type practice set (experiment start only, i.e. first block
        // of this session). Stage 2 of the two-stage training: 100% informative
        // cues, but ONLY target cues - independent of which informative cue type
        // the session's first block happens to use. The target cue ("this color
        // announces the rough voice I must report") is the most intuitive way to
        // make cue usage clear. Pilot v10: all three cue types were dropped -
        // training them proved confusing and is pointless anyway, since each
        // block uses exactly one informative cue type (announced by the block
        // reminder). 15 target-cue trials sampled from the subject's real trials
        // across all loaded blocks, so the cue->role mapping can be learned with
        // feedback before the first measured block. Neutral trials are
        // deliberately excluded: they teach nothing about the cue->role mapping.
        // Graceful degradation: if the loaded blocks contain no target-cue trials
        // at all (only possible for mid-session starts), stage 2 is skipped -
        // jsPsych executes a timeline with empty timeline_variables zero times.
        let practice_rows = [];
        let stage1_rows = [];   // stage 1: cue-free basic-task training (filled in 1c below)
        if (b_idx === 0) {
            const PRACTICE_CUE_TYPE = 'cue_target_location';   // ALWAYS target cues, whatever block 0 uses
            const cuePool = [];
            for (let item of all_blocks_data) {
                item.data.forEach(function(row, idx) {
                    if (row.CueInstruction === PRACTICE_CUE_TYPE) {
                        cuePool.push({ row: row, src_block: item.block, original_index: idx });
                    }
                });
            }
            const N_PRACTICE_CUE = 15;   // all 15 trials use the single trained cue type
            jsPsych.randomization.sampleWithoutReplacement(cuePool, N_PRACTICE_CUE).forEach(function(s) {
                practice_rows.push(Object.assign({}, s.row, { src_block: s.src_block, original_index: s.original_index, is_practice: true }));
            });
            practice_rows = jsPsych.randomization.shuffle(practice_rows);

            // 1c. Stage-1 cue-free training set (pilot v5): 15 real trials presented
            // WITHOUT cue information (CueInstruction overridden to 'cue_neutral' ->
            // the cue screen renders three white, uninformative arrows, exactly like
            // neutral trials in the main experiment). This teaches the basic task
            // (identify the rough target voice, report its digit) before any
            // cue->role contingency is introduced in stage 2. The stage-2 picks are
            // excluded so no underlying trial is used twice.
            const usedKeys = new Set(practice_rows.map(pr => `${pr.src_block}_${pr.original_index}`));
            let allPool = [];
            for (let item of all_blocks_data) {
                item.data.forEach(function(row, idx) {
                    if (!usedKeys.has(`${item.block}_${idx}`)) {
                        allPool.push({ row: row, src_block: item.block, original_index: idx });
                    }
                });
            }
            const N_STAGE1 = 15;
            jsPsych.randomization.sampleWithoutReplacement(allPool, N_STAGE1).forEach(function(s) {
                stage1_rows.push(Object.assign({}, s.row, {
                    src_block: s.src_block,
                    original_index: s.original_index,
                    is_practice: true,
                    CueInstruction: 'cue_neutral'  // all-white arrows = no cue information
                }));
            });
            stage1_rows = jsPsych.randomization.shuffle(stage1_rows);
            for (let pr of stage1_rows) {
                audio_files.push(`${base_url}sequences/sce-${subject}_block_${pr.src_block}/s_${pr.original_index}.wav`);
            }
            for (let pr of practice_rows) {
                audio_files.push(`${base_url}sequences/sce-${subject}_block_${pr.src_block}/s_${pr.original_index}.wav`);
            }
        }
        
        timeline.push({
            type: jsPsychPreload,
            audio: audio_files,
            message: L(`Lade akustische Stimuli (Block ${current_block_num + 1} von 6), bitte warten...`, `Loading audio stimuli (block ${current_block_num + 1} of 6), please wait...`)
        });

        // 2. Instructions - skipped entirely in ?debug=1 mode: the intro battery
        //    is not needed to verify practice / main-task behavior.
        if (current_block_num === 0 && !DEBUG_MODE) {
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
            let demo_instruction_trial = createInstructionTrial(L(`
                <div style="text-align: center; color: white;">
                    <h2 style="color: #4da8da;">Zielreize</h2>
                    <p>Im Kommenden werden Sie einen Eindruck davon erhalten, wie sich die Zahlwörter anhören.</p>
                    <p>Es werden nur die relevanten Zahlwörter abgespielt, auf die Sie achten sollen.</p>
                    <p>Dabei ertönen sie zufällig aus einer der drei Richtungen, so wie es auch im Hauptexperiment sein wird.</p>
                    <p>ACHTUNG: erschrecken Sie bitte nicht.</p>
                </div>
            `, `
                <div style="text-align: center; color: white;">
                    <h2 style="color: #4da8da;">Target Stimuli</h2>
                    <p>In the following, you will get an impression of what the spoken digits sound like.</p>
                    <p>Only the relevant spoken digits will be played - the ones you should attend to.</p>
                    <p>They will sound randomly from one of the three directions, just as it will be in the main experiment.</p>
                    <p>ATTENTION: please do not be startled.</p>
                </div>
            `));

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

            let accuracy_instruction_trial = createInstructionTrial(L(`
                <div style="text-align: center; color: white;">
                    <h2 style="color: #4da8da;">Genauigkeitstest</h2>
                    <p>Nun werden Ihnen nacheinander Zahlwörter abgespielt. Nach jedem Zahlwort müssen Sie durch Tastendruck angeben, ob es sich um ein zu identifizierendes Zahlwort (rau, kratzig) oder um ein reguläres Zahlwort handelt.</p>
                    <p>Drücken sie die Taste <strong style="color: #4caf50;">L</strong> für das raue, kratzige Zahlwort, und die Taste <strong style="color: #ff6b6b;">M</strong> für das reguläre Zahlwort.</p>
                    <p>Sie müssen 10 Wörter <strong>hintereinander</strong> korrekt identifizieren, um mit dem Experiment beginnen zu können.</p>
                    <p>Bei einem Fehler beginnt die Zählung wieder bei 0.</p>
                </div>
            `, `
                <div style="text-align: center; color: white;">
                    <h2 style="color: #4da8da;">Accuracy Test</h2>
                    <p>Now spoken digits will be played to you one after another. After each digit, you must indicate by key press whether it is a digit to be identified (rough, raspy) or a regular digit.</p>
                    <p>Press the key <strong style="color: #4caf50;">L</strong> for the rough, raspy digit, and the key <strong style="color: #ff6b6b;">M</strong> for the regular digit.</p>
                    <p>You must identify 10 words correctly <strong>in a row</strong> in order to be able to begin the experiment.</p>
                    <p>If you make an error, the count starts again at 0.</p>
                </div>
            `));
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
                                <div>${L("oder", "or")}</div>
                                <div><span style="color: #ff6b6b;">M</span></div>
                            </div>
                            <div style="font-size: 24px; color: #aaa;">
                                ${L(`Bisher korrekt: ${acc_correct_count} / 10`, `Correct so far: ${acc_correct_count} / 10`)}
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
                        return `<div style="font-size: 30px; color: #4caf50;">${L(`Korrekt! (${acc_correct_count}/10)`, `Correct! (${acc_correct_count}/10)`)}</div>`;
                    } else {
                        acc_correct_count = 0;
                        return `<div style="font-size: 30px; color: #ff6b6b;">${L("Falsch! Zähler zurückgesetzt.", "Wrong! Counter reset.")}</div>`;
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
                stimulus: L(`
                    <div style="text-align: center; color: white;">
                        <h2 style="color: #4caf50;">Geschafft!</h2>
                        <p>Sie haben 10 Zahlwörter hintereinander korrekt identifiziert.</p>
                        <p>Drücken Sie auf die Rechte Pfeiltaste, um weiterzublättern.</p>
                    </div>
                `, `
                    <div style="text-align: center; color: white;">
                        <h2 style="color: #4caf50;">Well done!</h2>
                        <p>You have correctly identified 10 spoken digits in a row.</p>
                        <p>Press the right arrow key to continue.</p>
                    </div>
                `),
                choices: ['ArrowRight']
            };

            timeline.push(accuracy_instruction_trial);
            timeline.push(accuracy_dynamic_loop);
            timeline.push(accuracy_result_trial);

            // CUE TEST BLOCK
            let cue_correct_count = 0;
            let current_cue_trial = {};

            let cue_test_instruction_trial = createInstructionTrial(L(`
                <div style="text-align: center; color: white;">
                    <h2 style="color: #4da8da;">Pfeil-Test</h2>
                    <p>Nun prüfen wir, ob Sie sich die Bedeutung der farbigen Pfeile gemerkt haben.</p>
                    <p>Ihnen wird nacheinander ein farbiger Pfeil präsentiert.</p>
                    <p>Drücken Sie die Taste <strong>Z</strong>, wenn der Pfeil den <strong>Zielreiz</strong> (raue Stimme) ankündigt.</p>
                    <p>Drücken Sie die Taste <strong>K</strong>, wenn der Pfeil die <strong>Kinderstimme</strong> (Störreiz) ankündigt.</p>
                    <p>Drücken Sie die Taste <strong>N</strong>, wenn der Pfeil die <strong>Normale Stimme</strong> ankündigt.</p>
                    <p>Sie müssen 10 Pfeile <strong>hintereinander</strong> korrekt zuordnen.</p>
                    <p>Bei einem Fehler beginnt die Zählung wieder bei 0.</p>
                </div>
            `, `
                <div style="text-align: center; color: white;">
                    <h2 style="color: #4da8da;">Arrow Test</h2>
                    <p>Now we test whether you have memorized the meaning of the colored arrows.</p>
                    <p>A colored arrow will be presented to you one after another.</p>
                    <p>Press the key <strong>Z</strong> if the arrow announces the <strong>target stimulus</strong> (rough voice).</p>
                    <p>Press the key <strong>K</strong> if the arrow announces the <strong>child's voice</strong> (distractor).</p>
                    <p>Press the key <strong>N</strong> if the arrow announces the <strong>normal voice</strong>.</p>
                    <p>You must classify 10 arrows correctly <strong>in a row</strong>.</p>
                    <p>If you make an error, the count starts again at 0.</p>
                </div>
            `));
            cue_test_instruction_trial.on_start = function() {
                cue_correct_count = 0;
            };

            let cue_test_trial = {
                type: jsPsychHtmlKeyboardResponse,
                stimulus: function() {
                    let trg_color_name = trial_data[0].Color.split("-")[1].toLowerCase();
                    let d_color_name = trial_data[0].Color.split("-")[3].toLowerCase();
                    let c_color_name = trial_data[0].Color.split("-")[5].toLowerCase();
                    const hexMap = { "red": "#ff6b6b", "green": "#4caf50", "blue": "#4da8da", "yellow": "#ffeb3b", "orange": "#ffa726", "white": "#ffffff", "violet": "#b388ff" };
                    let trg_col_hex = hexMap[trg_color_name] || trg_color_name;
                    let d_col_hex = hexMap[d_color_name] || d_color_name;
                    let c_col_hex = hexMap[c_color_name] || c_color_name;
                    
                    let rand = Math.random();
                    if (rand < 0.333) {
                        current_cue_trial.color_hex = trg_col_hex;
                        current_cue_trial.correct_key = 'z';
                    } else if (rand < 0.666) {
                        current_cue_trial.color_hex = d_col_hex;
                        current_cue_trial.correct_key = 'k';
                    } else {
                        current_cue_trial.color_hex = c_col_hex;
                        current_cue_trial.correct_key = 'n';
                    }
                    
                    return `
                        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh;">
                            <div class="arrow arrow-up" style="border-bottom-color: ${current_cue_trial.color_hex}; transform: translate(0, 0) scale(3); position: relative; margin-bottom: 60px; top: 0; left: 0;"></div>
                            <div style="font-size: 30px; color: white; display: flex; flex-direction: column; align-items: center; gap: 20px; margin-top: 40px;">
                                <div style="display: flex; gap: 40px;">
                                    ${(function(){
                                        let possible_wrongs = [];
                                        if (current_cue_trial.correct_key === 'z') possible_wrongs = ['k', 'n'];
                                        else if (current_cue_trial.correct_key === 'k') possible_wrongs = ['z', 'n'];
                                        else possible_wrongs = ['z', 'k'];
                                        
                                        let wrong_key = possible_wrongs[Math.floor(Math.random() * 2)];
                                        let display_options = [current_cue_trial.correct_key, wrong_key];
                                        
                                        let html_z = `<div><span style="font-weight: bold;">Z</span> ${L("(Zielreiz)", "(target)")}</div>`;
                                        let html_k = `<div><span style="font-weight: bold;">K</span> ${L("(Kinderstimme)", "(child's voice)")}</div>`;
                                        let html_n = `<div><span style="font-weight: bold;">N</span> ${L("(Normale Stimme)", "(normal voice)")}</div>`;
                                        
                                        let final_parts = [];
                                        if (display_options.includes('z')) final_parts.push(html_z);
                                        if (display_options.includes('k')) final_parts.push(html_k);
                                        if (display_options.includes('n')) final_parts.push(html_n);
                                        
                                        return final_parts.join(` <div>${L("oder", "or")}</div> `);
                                    })()}
                                </div>
                                <div style="font-size: 24px; color: #aaa;">
                                    ${L(`Bisher korrekt: ${cue_correct_count} / 10`, `Correct so far: ${cue_correct_count} / 10`)}
                                </div>
                            </div>
                        </div>
                    `;
                },
                choices: ['z', 'k', 'n'],
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
                        return `<div style="font-size: 30px; color: #4caf50;">${L(`Korrekt! (${cue_correct_count}/10)`, `Correct! (${cue_correct_count}/10)`)}</div>`;
                    } else {
                        cue_correct_count = 0;
                        return `<div style="font-size: 30px; color: #ff6b6b;">${L("Falsch! Zähler zurückgesetzt.", "Wrong! Counter reset.")}</div>`;
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
                stimulus: L(`
                    <div style="text-align: center; color: white;">
                        <h2 style="color: #4caf50;">Geschafft!</h2>
                        <p>Sie haben 10 Pfeile hintereinander korrekt identifiziert.</p>
                        <p>Drücken Sie auf die Rechte Pfeiltaste, um weiterzublättern.</p>
                    </div>
                `, `
                    <div style="text-align: center; color: white;">
                        <h2 style="color: #4caf50;">Well done!</h2>
                        <p>You have correctly identified 10 arrows in a row.</p>
                        <p>Press the right arrow key to continue.</p>
                    </div>
                `),
                choices: ['ArrowRight']
            };

            timeline.push(cue_test_instruction_trial);
            timeline.push(cue_dynamic_loop);
            timeline.push(cue_result_trial);
            
            timeline.push(createInstructionTrial(L(`
                <div style="text-align: center; color: white;">
                    <h2 style="color: #4caf50;">Bereit für das Hauptexperiment</h2>
                    <p>Im Kommenden werden Ihnen einige Probe-Durchläufe präsentiert. Diese sollen Sie mit der Aufgabe vertraut machen.</p>
                    <p>Sie können üben und Antworten geben, diese werden natürlich nicht gespeichert.</p>
                    <p>Bitte nutzen Sie diese Phase, um so gut wie möglich mit dem Experiment vertraut zu werden.</p>
                    <p>Nach diesem Testblock startet das Hauptexperiment.</p>
                </div>
            `, `
                <div style="text-align: center; color: white;">
                    <h2 style="color: #4caf50;">Ready for the Main Experiment</h2>
                    <p>In the following, some practice trials will be presented to you. These are meant to familiarize you with the task.</p>
                    <p>You can practice and give responses; these will of course not be saved.</p>
                    <p>Please use this phase to become as familiar as possible with the experiment.</p>
                    <p>After this practice block, the main experiment begins.</p>
                </div>
            `)));
        }

        let indexed_trials = trial_data.map((row, idx) => ({...row, original_index: idx}));

        // 3. Main Trial Loop
        let trial_timeline = {
            timeline: [
                {
                    type: jsPsychHtmlKeyboardResponse,
                    stimulus: function() {
                        let nonsingletonLoc = jsPsych.timelineVariable('Non-Singleton2Loc', true); 
                        let singletonLoc = jsPsych.timelineVariable('SingletonLoc', true);
                        let targetLoc = jsPsych.timelineVariable('TargetLoc', true);
                        let colorStr = jsPsych.timelineVariable('Color', true); 
                        let cueInstruction = jsPsych.timelineVariable('CueInstruction', true);

                        let colorParts = colorStr.split('-');
                        let targetColor = colorParts[1];
                        let distractorColor = colorParts[3];
                        let nonsingletonColor = colorParts[5];
                        const hexMap = { "red": "#ff6b6b", "green": "#4caf50", "blue": "#4da8da", "yellow": "#ffeb3b", "orange": "#ffa726", "white": "#ffffff", "violet": "#b388ff" };
                        let targetColorHex = hexMap[targetColor] || targetColor;
                        let distractorColorHex = hexMap[distractorColor] || distractorColor;
                        let nonsingletonColorHex = hexMap[nonsingletonColor] || nonsingletonColor;
                        
                        let cuedIndex = -1; // 1=L, 2=U, 3=R
                        let activeColor = 'white';
                        
                        if (cueInstruction.includes('target_location')) {
                            cuedIndex = targetLoc;
                            activeColor = targetColorHex;
                        } else if (cueInstruction.includes('nonsingleton_location')) {
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
                        // Practice trials replay audio from their original block's folder
                        // (cross-cue-type practice samples trials from all blocks).
                        let src_b = jsPsych.timelineVariable('src_block', true);
                        let folder = (typeof src_b === 'number') ? `${base_url}sequences/sce-${subject}_block_${src_b}/` : b_audio_folder;
                        return `${folder}s_${i}.wav`;
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
            timeline_variables: indexed_trials.map(row => ({...row, is_practice: false}))
        };

        // Practice runs ONCE at the start of the experiment (first block of this
        // session) as a TWO-STAGE training (pilot v5), not before every block:
        //   Stage 1: 15 cue-free trials (all-white neutral cue screen) with feedback,
        //            teaching the basic task (identify the rough target voice).
        //   Stage 2: 15 informative-cue trials (5 per cue type) with feedback,
        //            teaching the cue->role contingency (a real-task example).
        // The main experiment itself never shows feedback.
        if (b_idx === 0) {
            let practice_intro_stage1 = {
                type: jsPsychHtmlKeyboardResponse,
                stimulus: L(`<div class="instruction-text">
                    <h2 style="color: #4da8da; margin-bottom: 20px;">Übungsdurchgänge &ndash; Teil 1: Die Grundaufgabe</h2>
                    <p>Bevor das eigentliche Experiment beginnt, üben Sie zunächst in <strong>15 Durchgängen die Grundaufgabe ohne Hinweisreize</strong>.</p>
                    <p>Sie hören in jedem Durchgang gleichzeitig drei Zahlwörter: den <strong>Zielreiz</strong> (raue Stimme), einen <strong>Störreiz</strong> (Kinderstimme) und eine <strong>normale Stimme</strong>.</p>
                    <p>Ihre Aufgabe ist es, die Zahl des <strong>Zielreizes (der rauen Stimme)</strong> über die Antwortbox einzugeben.</p>
                    <p>Alle Pfeile bleiben in diesem Übungsteil <strong>weiß</strong> und liefern keine Information &ndash; hören Sie also genau hin, welche Stimme die raue ist.</p>
                    <p>Nach jeder Antwort erfahren Sie sofort, ob Sie richtig lagen. Diese Durchgänge gehen nicht in die Wertung ein.</p>
                    <p style="margin-top: 30px; color: #aaa;">Drücken Sie die <strong>LEERTASTE</strong>, um mit Teil 1 der Übung zu beginnen.</p>
                </div>`, `<div class="instruction-text">
                    <h2 style="color: #4da8da; margin-bottom: 20px;">Practice Trials &ndash; Part 1: The Basic Task</h2>
                    <p>Before the actual experiment begins, you will first practice <strong>the basic task without cues in 15 trials</strong>.</p>
                    <p>In every trial you will hear three spoken digits simultaneously: the <strong>target stimulus</strong> (rough voice), a <strong>distractor</strong> (child's voice) and a <strong>normal voice</strong>.</p>
                    <p>Your task is to enter the digit of the <strong>target stimulus (the rough voice)</strong> using the response box.</p>
                    <p>All arrows remain <strong>white</strong> in this practice part and carry no information &ndash; so listen carefully to determine which voice is the rough one.</p>
                    <p>After each response you will immediately learn whether you were correct. These trials do not count toward your score.</p>
                    <p style="margin-top: 30px; color: #aaa;">Press the <strong>SPACEBAR</strong> to begin part 1 of the practice.</p>
                </div>`),
                choices: [" "]
            };
            timeline.push(practice_intro_stage1);
            
            // Practice-only feedback (pilot v3: correctness feedback was added
            // because participants previously had to learn the cue->role
            // contingency from instructions alone; pilot v9: miss handling).
            // jsPsych 7.3 NOTE: conditional_function is only evaluated on TIMELINES,
            // never on individual trials - a trial-level conditional_function is
            // silently ignored. Therefore the feedback trials are NOT part of the
            // main trial_timeline at all. Instead, two variants are spliced into a
            // copy of the trial procedure used exclusively for the practice
            // timeline below, each wrapped in its own single-trial timeline so
            // that conditional_function is honoured (exactly one of them runs
            // after each practice response trial):
            //   - practice_feedback_text: after an ACTUAL response -> correctness
            //     text only ("Richtig!" / "Leider falsch." + target digit).
            //   - practice_feedback_miss: after a MISS (no response within the
            //     1750 ms window) -> a live, NEUTRAL response box (genuine
            //     HtmlButtonResponse render, pixel-identical to the main
            //     experiment's ITI box). Nothing glows red automatically: the
            //     frame only flashes red (error-glow, 500 ms) when the participant
            //     clicks AFTER the window has passed, i.e. upon a response OUTSIDE
            //     of the response interval - the exact late-click warning
            //     semantics of the main experiment ITI. (pilot v9 fix: v8 glowed
            //     red on every miss even though no response had occurred, and its
            //     synthetic box rendered slightly narrower than the real one.)
            //     Pilot v10: such a late (ITI) click also receives correctness
            //     feedback - practice is for learning, so the clicked digit is
            //     evaluated against the missed trial's target digit.
            //     Pilot v13: presentation became fully coherent with
            //     practice_feedback_text - first the box flashed red for 500 ms
            //     (the late-click warning of the main experiment ITI, flagging
            //     the TIMING), then the SAME feedback panel as for in-window
            //     responses (identical verdict wording, typography and colors,
            //     plus a too-late note) replaced the display content and
            //     evaluated the DIGIT.
            //     Pilot v14: the 500 ms red flash is DROPPED for practice - it
            //     ate into the remaining trial time, leaving too little time to
            //     read the feedback text. A late click now swaps in the SAME
            //     feedback panel (verdict + too-late note) IMMEDIATELY, so the
            //     text can use the entire rest of the trial.
            // Both variants REPLACE the ITI in practice trials and stay on for
            // the REST of the trial (unused response window + full ITI), so
            // practice pacing stays identical to main trials. This structurally
            // guarantees: feedback during practice, none in the main experiment.
            let practice_feedback_duration = function() {
                // Remaining trial time after the response: the unused part of the
                // 1750 ms response window plus the full ITI. Together with the
                // (early-ending) response trial this keeps practice pacing
                // identical to main trials: response + feedback span exactly
                // 1750 ms + ITI, but filled entirely with feedback.
                const RESPONSE_WINDOW_MS = 1750;
                const last = jsPsych.data.get().filter({phase: 'response'}).last(1).values()[0];
                const rt = (last && typeof last.rt === 'number') ? last.rt : 0;
                const iti_ms = jsPsych.timelineVariable('ITI-Jitter', true) * 1000;
                return Math.max((RESPONSE_WINDOW_MS - rt) + iti_ms, 800);
            };

            let practice_feedback_text = {
                type: jsPsychHtmlKeyboardResponse,
                stimulus: function() {
                    const last = jsPsych.data.get().filter({phase: 'response'}).last(1).values()[0];
                    if (!last || last.response === null) return '';   // defensive: misses are handled by practice_feedback_miss
                    if (last.correct) {
                        return `<div class="instruction-text">
                            <p style="font-size: 32px; color: #4caf50;">${L("Richtig!", "Correct!")}</p>
                        </div>`;
                    }
                    return `<div class="instruction-text">
                        <p style="font-size: 32px; color: #ff6b6b;">${L("Leider falsch.", "Unfortunately wrong.")}</p>
                        <p style="font-size: 24px;">${L(`Die Zielzahl war: <strong style="color: #4da8da;">${last.targetDigit}</strong>`, `The target digit was: <strong style="color: #4da8da;">${last.targetDigit}</strong>`)}</p>
                    </div>`;
                },
                choices: "NO_KEYS",
                trial_duration: practice_feedback_duration,
                data: { phase: 'practice_feedback', is_practice: true, block: current_block_num }
            };

            // Miss feedback: a genuine HtmlButtonResponse screen, so the response
            // box renders pixel-identical to the main experiment's ITI box. The
            // box is live but NEUTRAL - no automatic red on a miss and, since
            // pilot v14, also NO red flash on a late click: unlike the main
            // experiment's ITI warning, a click after the response window has
            // passed shows the feedback text IMMEDIATELY (see the click handler
            // below), so the participant has the full remaining trial time to
            // read it.
            // Pilot v10/v13: that late click ALSO gets correctness feedback for
            // the clicked digit - rendered as the same feedback panel used for
            // in-window responses (see the click handler below).
            let practice_feedback_miss = {
                type: jsPsychHtmlButtonResponse,
                stimulus: '',
                choices: ['1', '2', '3', '4', '5', '6', '7', '8', '9'],
                button_html: '<button class="jspsych-btn virtual-response-box">%choice%</button>',
                response_ends_trial: false,
                trial_duration: practice_feedback_duration,
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
                        btn.addEventListener('click', () => {
                            document.body.classList.add('hide-cursor');
                            const container = document.querySelector('#jspsych-html-button-response-btngroup');
                            if (container && !window.responded_in_trial) {
                                // Disable the box right away: exactly ONE late
                                // response is evaluated per trial (disabled
                                // buttons stop firing clicks via CSS).
                                btns.forEach(b => b.setAttribute('disabled', 'disabled'));
                                // Pilot v10/v13: a late (ITI) click gets the SAME
                                // feedback panel as a response inside the window
                                // (see practice_feedback_text): identical verdict
                                // wording, typography and colors, plus a too-late
                                // note. The clicked digit comes from the button
                                // label; the target digit belongs to the practice
                                // response trial that just missed its window.
                                // Pilot v14: NO red error-glow flash anymore - the
                                // 500 ms flash ate into the remaining trial time
                                // and left too little time to read the text. The
                                // panel is swapped in IMMEDIATELY so it can use
                                // the entire rest of the trial.
                                const clickedDigit = parseInt(btn.innerText, 10);
                                const last = jsPsych.data.get().filter({phase: 'response'}).last(1).values()[0];
                                const targetDigit = (last && last.targetDigit !== undefined && last.targetDigit !== null) ? last.targetDigit : null;
                                let fb;
                                if (targetDigit === null) {
                                    // Defensive: no target digit available -> timing info only.
                                    fb = `<div class="instruction-text"><p style="font-size: 32px; color: #ff6b6b;">${L("Zu spät!", "Too late!")}</p></div>`;
                                } else if (clickedDigit === targetDigit) {
                                    fb = `<div class="instruction-text">
                                        <p style="font-size: 32px; color: #4caf50;">${L("Richtig!", "Correct!")}</p>
                                        <p style="font-size: 24px;">${L("Aber zu spät &ndash; die Zeit war bereits abgelaufen.", "But too late &ndash; the time had already run out.")}</p>
                                    </div>`;
                                } else {
                                    fb = `<div class="instruction-text">
                                        <p style="font-size: 32px; color: #ff6b6b;">${L("Leider falsch.", "Unfortunately wrong.")}</p>
                                        <p style="font-size: 24px;">${L(`Die Zielzahl war: <strong style="color: #4da8da;">${targetDigit}</strong>`, `The target digit was: <strong style="color: #4da8da;">${targetDigit}</strong>`)}</p>
                                        <p style="font-size: 24px;">${L("Außerdem zu spät &ndash; die Zeit war bereits abgelaufen.", "Also too late &ndash; the time had already run out.")}</p>
                                    </div>`;
                                }
                                // Swap the WHOLE display content for the feedback
                                // panel IMMEDIATELY (pilot v14: the 500 ms red
                                // warning flash was dropped so the text gets the
                                // full remaining trial time) - NOT the button
                                // group itself, whose 3-column grid layout would
                                // squeeze the panel into a single grid cell. If
                                // the trial has somehow already ended and the
                                // next one is on screen (a very late click),
                                // leave the DOM untouched.
                                if (container.isConnected !== false) {   // trial already over?
                                    const content = document.querySelector('#jspsych-content') || container.parentElement;
                                    if (content) content.innerHTML = fb;
                                }
                            }
                        });
                    });
                },
                data: { phase: 'practice_feedback', is_practice: true, block: current_block_num }
            };

            // Practice procedure: cue -> delay -> response -> feedback, where the
            // feedback fills the REST of the trial. In practice the response trial
            // ends IMMEDIATELY on the button click (response_ends_trial = true), so
            // the feedback comes on straight after the response and stays on until
            // the nominal end of the trial (response window + ITI). The ITI screen
            // of the main experiment is deliberately NOT part of practice trials:
            // after an actual response only the feedback text is shown, and after
            // a miss the feedback screen itself IS the (neutral, live) response
            // box that carries the immediate correctness feedback (plus a
            // too-late note) for late (ITI) responses - pilot v14: no red
            // warning flash anymore, so the text has the full remaining trial
            // time to be read.
            // NOTE: indexes refer to the main trial_timeline.timeline order:
            // [0]=cue, [1]=delay, [2]=response, [3]=iti.
            let practice_procedure = [];
            practice_procedure.push(trial_timeline.timeline[0]);  // cue
            practice_procedure.push(trial_timeline.timeline[1]);  // delay
            let practice_response_trial = Object.assign({}, trial_timeline.timeline[2]);  // response (copy)
            practice_response_trial.response_ends_trial = true;   // click ends trial -> feedback follows immediately
            practice_procedure.push(practice_response_trial);
            // Text vs. miss feedback: conditional_function is only evaluated on
            // TIMELINE nodes in jsPsych 7.3, so each variant is wrapped in its
            // own single-trial timeline. Exactly one of the two runs per trial.
            practice_procedure.push({
                timeline: [practice_feedback_text],
                conditional_function: function() {
                    const last = jsPsych.data.get().filter({phase: 'response'}).last(1).values()[0];
                    return !!(last && last.response !== null);
                }
            });
            practice_procedure.push({
                timeline: [practice_feedback_miss],
                conditional_function: function() {
                    const last = jsPsych.data.get().filter({phase: 'response'}).last(1).values()[0];
                    return !(last && last.response !== null);
                }
            });

            // Stage 1 timeline: same procedure, but the sampled rows carry
            // CueInstruction 'cue_neutral' -> the cue screen shows three WHITE
            // arrows (exactly like neutral trials in the main experiment), i.e.
            // the basic task is trained without any cue information.
            let stage1_timeline = {
                timeline: practice_procedure,
                timeline_variables: stage1_rows
            };
            timeline.push(stage1_timeline);

            // Stage 2 intro: a real-task example with ONLY target cues (pilot
            // v10: all three cue types were dropped - too confusing and
            // pointless, since each block contains exactly one informative cue
            // type anyway; the block reminder below announces the concrete
            // color of the cue type that the following block actually uses).
            let practice_intro_stage2 = {
                type: jsPsychHtmlKeyboardResponse,
                stimulus: L(`<div class="instruction-text">
                    <h2 style="color: #4da8da; margin-bottom: 20px;">Übungsdurchgänge &ndash; Teil 2: Hinweisreize</h2>
                    <p>Im zweiten Teil der Übung folgt nun ein <strong>realer Beispielblock des eigentlichen Experiments</strong> mit 15 Durchgängen.</p>
                    <p>Anders als eben erscheint vor jedem Durchgang ein <strong>farbiger Hinweisreiz</strong>. In diesem Übungsteil kommt <strong>ausschließlich der Hinweis auf den Zielreiz</strong> (raue Stimme) vor &ndash; er zeigt Ihnen an, aus welcher Richtung die raue Stimme kommen wird.</p>
                    <p>Nach jeder Antwort erfahren Sie sofort, ob Sie richtig lagen. Nutzen Sie diese Rückmeldung, um die Bedeutung der Hinweisfarbe zu lernen. Auch diese Durchgänge gehen nicht in die Wertung ein.</p>
                    <p style="margin-top: 30px; color: #aaa;">Drücken Sie die <strong>LEERTASTE</strong>, um mit Teil 2 der Übung zu beginnen.</p>
                </div>`, `<div class="instruction-text">
                    <h2 style="color: #4da8da; margin-bottom: 20px;">Practice Trials &ndash; Part 2: Cues</h2>
                    <p>In the second part of the practice, a <strong>real example block of the actual experiment</strong> with 15 trials now follows.</p>
                    <p>Unlike just now, a <strong>colored cue</strong> appears before every trial. In this practice part, <strong>only the cue to the target stimulus</strong> (rough voice) occurs &ndash; it tells you from which direction the rough voice will come.</p>
                    <p>After each response you will immediately learn whether you were correct. Use this feedback to learn the meaning of the cue color. These trials also do not count toward your score.</p>
                    <p style="margin-top: 30px; color: #aaa;">Press the <strong>SPACEBAR</strong> to begin part 2 of the practice.</p>
                </div>`),
                choices: [" "]
            };
            timeline.push(practice_intro_stage2);

            let practice_timeline = {
                timeline: practice_procedure,
                timeline_variables: practice_rows
            };
            timeline.push(practice_timeline);
            
            let main_start = {
                type: jsPsychHtmlKeyboardResponse,
                stimulus: L(`<div class="instruction-text">
                    <h2 style="color: #4caf50; margin-bottom: 20px;">Start des Hauptexperiments</h2>
                    <p>Die Übungsdurchgänge sind nun beendet.</p>
                    <p>Das eigentliche Experiment beginnt jetzt. Bitte konzentrieren Sie sich auf die Aufgabe.</p>
                    <p style="margin-top: 30px; color: #aaa;">Drücken Sie die <strong>LEERTASTE</strong>, um zu starten.</p>
                </div>`, `<div class="instruction-text">
                    <h2 style="color: #4caf50; margin-bottom: 20px;">Start of the Main Experiment</h2>
                    <p>The practice trials are now finished.</p>
                    <p>The actual experiment begins now. Please concentrate on the task.</p>
                    <p style="margin-top: 30px; color: #aaa;">Press the <strong>SPACEBAR</strong> to start.</p>
                </div>`),
                choices: [" "]
            };
            timeline.push(main_start);
        }

        timeline.push(getBlockReminderTrial(trial_data));
        timeline.push(trial_timeline);

        const save_data = {
            type: jsPsychPipe,
            action: "save",
            experiment_id: datapipe_id,
            filename: ()=>`sce-${subject}_block_${current_block_num}_data_${getFormattedDate()}.csv`,
            data_string: ()=>formatDataToCSV(current_block_num)
        };
        // Debug runs must never write to DataPipe (would pollute pilot data).
        if (!DEBUG_MODE) {
            timeline.push(save_data);
        }

        const save_mouse_data = {
            type: jsPsychPipe,
            action: "save",
            experiment_id: datapipe_id,
            filename: ()=>`sce-${subject}_block_${current_block_num}_trajectories_${getFormattedDate()}.csv`,
            data_string: ()=>formatMouseDataToCSV(current_block_num)
        };
        if (!DEBUG_MODE) {
            timeline.push(save_mouse_data);
        }

        // Post-block mean accuracy summary (pilot v7): purely informational, so
        // participants can see what they are actually doing - deliberately NOT
        // framed as reward or praise. Computed from the response trials of the
        // block that just finished (practice trials excluded via is_practice;
        // missed/too-slow responses count as incorrect, consistent with
        // data.correct).
        let block_accuracy_trial = {
            type: jsPsychHtmlKeyboardResponse,
            stimulus: function() {
                // Plain-JS exclusion of practice rows (is_practice === false) instead
                // of relying on jsPsych's filter() boolean-matching semantics.
                const block_responses = jsPsych.data.get()
                    .filter({phase: 'response', block: current_block_num})
                    .values()
                    .filter(t => t.is_practice === false);
                const n = block_responses.length;
                const n_correct = block_responses.filter(t => t.correct === true).length;
                const acc = n > 0 ? Math.round(100 * n_correct / n) : 0;
                return `<div class="instruction-text">
                    <h2 style="color: #4da8da; margin-bottom: 20px;">${L(`Block ${current_block_num + 1} von 6 abgeschlossen`, `Block ${current_block_num + 1} of 6 completed`)}</h2>
                    <p>${L(`Ihre mittlere Genauigkeit in diesem Block: <strong>${acc} %</strong> (${n_correct} von ${n} Durchgängen korrekt).`, `Your mean accuracy in this block: <strong>${acc} %</strong> (${n_correct} of ${n} trials correct).`)}</p>
                    <p style="color: #aaa; font-size: 18px;">${L("Diese Zusammenfassung dient lediglich Ihrer Information &uuml;ber die eigene Leistung.", "This summary is solely intended to inform you about your own performance.")}</p>
                    <p style="margin-top: 30px; color: #aaa;">${L("Dr&uuml;cken Sie die <strong>LEERTASTE</strong>, um fortzufahren.", "Press the <strong>SPACEBAR</strong> to continue.")}</p>
                </div>`;
            },
            choices: [" "]
        };
        timeline.push(block_accuracy_trial);

        if (current_block_num < 5) {
            timeline.push({
                type: jsPsychHtmlKeyboardResponse,
                stimulus: function() {
                    let next_msg = "";
                    let next_block_obj = all_blocks_data.find(b => b.block === current_block_num + 1);
                    if (next_block_obj && next_block_obj.data && next_block_obj.data.length > 0) {
                        let informative_trial = next_block_obj.data.find(t => t.CueInstruction !== 'cue_neutral');
                        let n_cue_inst = informative_trial ? informative_trial.CueInstruction : 'cue_neutral';
                        let n_colorStr = next_block_obj.data[0].Color;
                        
                        let info = n_colorStr.split("-");
                        let targetColor = info[1].toLowerCase();
                        let distractorColor = info[3].toLowerCase();
                        let controlColor = info[5].toLowerCase();
                        
                        const hexMap = { "red": "#ff6b6b", "green": "#4caf50", "blue": "#4da8da", "yellow": "#ffeb3b", "orange": "#ffa726", "white": "#ffffff", "violet": "#b388ff" };
                        
                        let active_color_eng = "";
                        let cue_desc = "";
                        
                        if (n_cue_inst.includes('target_location')) {
                            active_color_eng = targetColor;
                            cue_desc = L("den <strong>Zielreiz</strong> (raue Stimme)", "the <strong>target stimulus</strong> (rough voice)");
                        } else if (n_cue_inst.includes('distractor_location')) {
                            active_color_eng = distractorColor;
                            cue_desc = L("den <strong>Störreiz</strong> (Kinderstimme)", "the <strong>distractor</strong> (child's voice)");
                        } else if (n_cue_inst.includes('nonsingleton_location')) {
                            active_color_eng = controlColor;
                            cue_desc = L("die <strong>Normale Stimme</strong>", "the <strong>normal voice</strong>");
                        }
                        
                        let active_ger = localizeColorName(active_color_eng);
                        let active_hex = hexMap[active_color_eng] || active_color_eng;
                        let highlight = `<span style="color: ${active_hex}; font-weight: bold; text-transform: uppercase;">${active_ger}</span>`;
                        
                        next_msg = `<div style="margin-top: 20px; padding: 15px; background: rgba(255,255,255,0.05); border-radius: 8px;">
                            <p style="font-size: 18px; margin-bottom: 10px; color: #4da8da;"><strong>${L("Erinnerung für den nächsten Block:", "Reminder for the next block:")}</strong></p>
                            <p style="font-size: 16px;">${L(`Der farbige Pfeil kündigt ${cue_desc} an.<br>
                            Achten Sie auf den Pfeil mit der Farbe ${highlight}.`, `The colored arrow announces ${cue_desc}.<br>
                            Pay attention to the arrow with the color ${highlight}.`)}</p>
                        </div>`;
                    }

                    return `
                    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; color: white; background: #121212;">
                        <div class="glass-container" style="text-align: center; max-width: 600px;">
                            <h2 style="color: #4da8da;">${L("Dieser Block ist zu Ende.", "This block is over.")}</h2>
                            <p>${L("Bitte machen Sie eine kurze Pause von 60 Sekunden.", "Please take a short break of 60 seconds.")}</p>
                            ${next_msg}
                            <p style="margin-top: 20px;">${L(`Der nächste Block startet automatisch in <strong style="font-size: 24px; color: #ff6b6b;" id="countdown">60</strong> Sekunden.`, `The next block starts automatically in <strong style="font-size: 24px; color: #ff6b6b;" id="countdown">60</strong> seconds.`)}</p>
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