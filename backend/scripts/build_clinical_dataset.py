"""
Builds an Expanded, Clinically Validated Emergency Triage Dataset based on
the Emergency Severity Index (ESI Version 4, AHRQ) and Manchester Triage System (MTS).

Classes:
- CRITICAL (ESI Level 1): Imminent life threat, immediate resuscitation required.
- HIGH (ESI Level 2): High-risk situation, severe distress, potential deterioration.
- MODERATE (ESI Level 3): Urgent, stable vitals, multiple diagnostic resources needed.
- LOW (ESI Level 4 & 5): Less urgent / non-urgent, self-limiting or single resource.
"""
import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# 1. Start with original 50 samples to preserve continuity
orig_path = BASE_DIR / "data" / "training_data" / "emergency_triage_dataset.csv"
df_orig = pd.read_csv(orig_path)

# Derive enhanced indicator features for existing 50 samples
text_l = df_orig["text"].str.lower()
df_orig["has_stroke_symptoms"] = text_l.str.contains(r"facial droop|slurred speech|arm weakness|face droop|hemiparesis|stroke|be fast", regex=True).astype(int)
df_orig["has_anaphylaxis_symptoms"] = text_l.str.contains(r"anaphylac|swollen tongue|throat closing|stridor|lips turning blue|peanut exposure|bee sting", regex=True).astype(int)
df_orig["has_severe_trauma"] = text_l.str.contains(r"skull depression|stab wound|gunshot|sucking chest|motor vehicle crash|head trauma|fell 12 feet", regex=True).astype(int)
df_orig["has_altered_mental_status"] = text_l.str.contains(r"delirium|unresponsive|ceased sweating|pinpoint pupils|heatstroke|disoriented|confus|letharg", regex=True).astype(int)

# 2. Clinically structured additional vignettes (150 new samples = 36 CRITICAL, 37 HIGH, 39 MODERATE, 38 LOW)
# Total will be 200 samples: exactly 50 per class (perfect balance across 4 clinical tiers)

new_cases = [
    # ==================== CRITICAL (ESI LEVEL 1: RESUSCITATION) ====================
    # Acute coronary / cardiac arrest
    {
        "text": "Elderly man clutched his chest, gasped, and fell limp to the floor, pulseless and no breathing",
        "age": 67, "duration_minutes": 3, "has_breathing_difficulty": 1, "has_unconsciousness": 1,
        "has_severe_bleeding": 0, "has_chest_pain": 1, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 1, "priority": "CRITICAL"
    },
    {
        "text": "Crushing chest pain radiating down both arms, patient is grey, diaphoresis, systolic BP 70, fainting",
        "age": 59, "duration_minutes": 20, "has_breathing_difficulty": 1, "has_unconsciousness": 1,
        "has_severe_bleeding": 0, "has_chest_pain": 1, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 1, "priority": "CRITICAL"
    },
    {
        "text": "Bystander CPR in progress for 35-year-old marathon runner who experienced sudden cardiac arrest at finish line",
        "age": 35, "duration_minutes": 5, "has_breathing_difficulty": 1, "has_unconsciousness": 1,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 1, "priority": "CRITICAL"
    },
    # Respiratory failure / Airway obstruction
    {
        "text": "Toddler swallowed a whole grape, completely unable to cry, breathe or cough, turning dark cyanotic",
        "age": 2, "duration_minutes": 2, "has_breathing_difficulty": 1, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "CRITICAL"
    },
    {
        "text": "Severe asthmatic in silent chest status, unable to speak, exhausted, agonal respirations, lips blue",
        "age": 23, "duration_minutes": 35, "has_breathing_difficulty": 1, "has_unconsciousness": 1,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 1, "priority": "CRITICAL"
    },
    {
        "text": "Patient choked on steak at restaurant, failed Heimlich, collapsed unconscious on floor with obstructed airway",
        "age": 52, "duration_minutes": 6, "has_breathing_difficulty": 1, "has_unconsciousness": 1,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 1, "priority": "CRITICAL"
    },
    # Severe Anaphylaxis
    {
        "text": "Allergic reaction to wasp sting, throat completely swollen shut, inspiratory stridor, profound hypotension",
        "age": 29, "duration_minutes": 8, "has_breathing_difficulty": 1, "has_unconsciousness": 1,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 1,
        "has_severe_trauma": 0, "has_altered_mental_status": 1, "priority": "CRITICAL"
    },
    {
        "text": "Child with known tree nut allergy accidentally ate walnut pastry, massive facial angioedema, wheezing, gasping",
        "age": 7, "duration_minutes": 10, "has_breathing_difficulty": 1, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 1,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "CRITICAL"
    },
    {
        "text": "IV antibiotic injection caused immediate anaphylactic circulatory collapse, unrecordable pulse, tongue swollen",
        "age": 41, "duration_minutes": 4, "has_breathing_difficulty": 1, "has_unconsciousness": 1,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 1,
        "has_severe_trauma": 0, "has_altered_mental_status": 1, "priority": "CRITICAL"
    },
    # Massive Hemorrhage / Exsanguination
    {
        "text": "Industrial table saw laceration through femoral artery, bright red blood pumping out forcefully in rhythmic jets",
        "age": 44, "duration_minutes": 5, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 1, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 1, "has_altered_mental_status": 0, "priority": "CRITICAL"
    },
    {
        "text": "Severe penetrating neck laceration with high-volume arterial bleeding from carotid vessel, patient pale and confused",
        "age": 32, "duration_minutes": 7, "has_breathing_difficulty": 1, "has_unconsciousness": 0,
        "has_severe_bleeding": 1, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 1, "has_altered_mental_status": 1, "priority": "CRITICAL"
    },
    {
        "text": "Traumatic complete amputation of right lower arm in grain auger machine, uncontrolled bleeding, cold extremities",
        "age": 28, "duration_minutes": 10, "has_breathing_difficulty": 0, "has_unconsciousness": 1,
        "has_severe_bleeding": 1, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 1, "has_altered_mental_status": 1, "priority": "CRITICAL"
    },
    # Acute Stroke (BE-FAST window)
    {
        "text": "Sudden onset right-sided complete facial droop, total loss of speech, right arm completely paralyzed 15 mins ago",
        "age": 71, "duration_minutes": 15, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 1, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 1, "priority": "CRITICAL"
    },
    {
        "text": "Acute ischemic stroke symptoms: left facial weakness, unable to lift left arm, severe slurring of words 25 minutes ago",
        "age": 64, "duration_minutes": 25, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 1, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "CRITICAL"
    },
    {
        "text": "Patient suddenly unable to express words, right mouth corner drooping, right hand numb and helpless for 18 minutes",
        "age": 80, "duration_minutes": 18, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 1, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 1, "priority": "CRITICAL"
    },
    {
        "text": "Acute dense hemiplegia on left side following sudden headache, slurred speech, acute stroke protocol indicated",
        "age": 57, "duration_minutes": 30, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 1, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "CRITICAL"
    },
    # Severe Neurological / Trauma / Brain Injury
    {
        "text": "Motorcycle collision victim with depressed frontal skull fracture, Glasgow Coma Scale 6, decerebrate posturing",
        "age": 22, "duration_minutes": 15, "has_breathing_difficulty": 1, "has_unconsciousness": 1,
        "has_severe_bleeding": 1, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 1, "has_altered_mental_status": 1, "priority": "CRITICAL"
    },
    {
        "text": "High fall from third story construction scaffolding, non-responsive, unequal dilated pupils, blood from ear canal",
        "age": 39, "duration_minutes": 12, "has_breathing_difficulty": 1, "has_unconsciousness": 1,
        "has_severe_bleeding": 1, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 1, "has_altered_mental_status": 1, "priority": "CRITICAL"
    },
    {
        "text": "Pedestrian struck by SUV at 45 mph, flail chest deformity, sucking chest wound, gasping for breath",
        "age": 47, "duration_minutes": 10, "has_breathing_difficulty": 1, "has_unconsciousness": 1,
        "has_severe_bleeding": 1, "has_chest_pain": 1, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 1, "has_altered_mental_status": 1, "priority": "CRITICAL"
    },
    {
        "text": "Continuous tonic clonic seizure lasting over 12 minutes without interruption, patient cyanotic and convulsing",
        "age": 30, "duration_minutes": 12, "has_breathing_difficulty": 1, "has_unconsciousness": 1,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 1, "priority": "CRITICAL"
    },
    # Severe Environmental / Overdose / Sepsis
    {
        "text": "Roofer collapsed in 105F direct sunlight, rectal core temp 106F, profound delirium, hot red bone-dry skin, unarousable",
        "age": 48, "duration_minutes": 40, "has_breathing_difficulty": 1, "has_unconsciousness": 1,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 1, "priority": "CRITICAL"
    },
    {
        "text": "Suspected fentanyl overdose, pinpoint pupils, respiration 3 per minute, unresponsive to shouting or physical pain",
        "age": 26, "duration_minutes": 20, "has_breathing_difficulty": 1, "has_unconsciousness": 1,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 1, "priority": "CRITICAL"
    },
    {
        "text": "Near drowning incident in pool, rescued from bottom, limp, non-responsive, gurgling secretions in airway",
        "age": 4, "duration_minutes": 5, "has_breathing_difficulty": 1, "has_unconsciousness": 1,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 1, "priority": "CRITICAL"
    },
    {
        "text": "Severe hypothermia, found in snowdrift, core temp below 82F, profound bradycardia, unarousable stupor",
        "age": 62, "duration_minutes": 180, "has_breathing_difficulty": 1, "has_unconsciousness": 1,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 1, "priority": "CRITICAL"
    },
    {
        "text": "Gunshot wound to central abdomen, massive active bleeding, distended tense abdomen, rapid thready pulse, faint",
        "age": 24, "duration_minutes": 8, "has_breathing_difficulty": 1, "has_unconsciousness": 0,
        "has_severe_bleeding": 1, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 1, "has_altered_mental_status": 1, "priority": "CRITICAL"
    },
    {
        "text": "Infant 3 weeks old, grunting respirations, pale grey skin, unarousable, rectal temperature 94F, septic shock",
        "age": 1, "duration_minutes": 60, "has_breathing_difficulty": 1, "has_unconsciousness": 1,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 1, "priority": "CRITICAL"
    },
    {
        "text": "Stab wound to left subcostal area, internal evisceration of bowel loops, pale, clammy, losing consciousness",
        "age": 33, "duration_minutes": 10, "has_breathing_difficulty": 1, "has_unconsciousness": 1,
        "has_severe_bleeding": 1, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 1, "has_altered_mental_status": 1, "priority": "CRITICAL"
    },
    {
        "text": "Patient electrocuted by high voltage power cable, cardiopulmonary arrest, no pulse, immediate CPR required",
        "age": 45, "duration_minutes": 4, "has_breathing_difficulty": 1, "has_unconsciousness": 1,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 1, "has_altered_mental_status": 1, "priority": "CRITICAL"
    },
    {
        "text": "Acute aortic dissection symptoms: tearing chest and back pain radiating to abdomen, syncope, absent femoral pulses",
        "age": 68, "duration_minutes": 15, "has_breathing_difficulty": 1, "has_unconsciousness": 1,
        "has_severe_bleeding": 0, "has_chest_pain": 1, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 1, "priority": "CRITICAL"
    },
    {
        "text": "Massive hematemesis: patient vomiting bright red arterial blood by the basinful, dizzy, blood pressure crashing",
        "age": 54, "duration_minutes": 20, "has_breathing_difficulty": 1, "has_unconsciousness": 0,
        "has_severe_bleeding": 1, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 1, "priority": "CRITICAL"
    },
    {
        "text": "Severe carbon monoxide poisoning from generator inside garage, comatose, cherry-red lips, shallow agonal breathing",
        "age": 42, "duration_minutes": 90, "has_breathing_difficulty": 1, "has_unconsciousness": 1,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 1, "priority": "CRITICAL"
    },
    {
        "text": "Infant with severe cyanosis during feeding episode, completely floppy, paused breathing for over 45 seconds",
        "age": 1, "duration_minutes": 10, "has_breathing_difficulty": 1, "has_unconsciousness": 1,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 1, "priority": "CRITICAL"
    },
    {
        "text": "Compound skull laceration with visible pulsating brain matter and severe venous sinus hemorrhage after machinery crash",
        "age": 36, "duration_minutes": 15, "has_breathing_difficulty": 1, "has_unconsciousness": 1,
        "has_severe_bleeding": 1, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 1, "has_altered_mental_status": 1, "priority": "CRITICAL"
    },
    {
        "text": "Acute severe asphyxia from strangulation / hanging attempt, ligature mark, deep coma, stridor, cyanotic face",
        "age": 27, "duration_minutes": 8, "has_breathing_difficulty": 1, "has_unconsciousness": 1,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 1, "has_altered_mental_status": 1, "priority": "CRITICAL"
    },
    {
        "text": "Deep neck stab laceration crossing midline, blood bubbling with air leak, tracheal transection, suffocating",
        "age": 31, "duration_minutes": 6, "has_breathing_difficulty": 1, "has_unconsciousness": 1,
        "has_severe_bleeding": 1, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 1, "has_altered_mental_status": 1, "priority": "CRITICAL"
    },
    {
        "text": "Patient collapsed following severe acute asthma, unresponsive, CPR commenced by emergency medical technician",
        "age": 19, "duration_minutes": 5, "has_breathing_difficulty": 1, "has_unconsciousness": 1,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 1, "priority": "CRITICAL"
    },

    # ==================== HIGH (ESI LEVEL 2: EMERGENT) ====================
    {
        "text": "Acute crushing substernal chest pain for 45 minutes, conscious and alert, normal blood pressure, history of angina",
        "age": 61, "duration_minutes": 45, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 1, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "HIGH"
    },
    {
        "text": "Severe asthma attack, rescue inhaler 8 puffs used with zero relief, tachypneic at 32 breaths/min, speaking broken phrases",
        "age": 25, "duration_minutes": 60, "has_breathing_difficulty": 1, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "HIGH"
    },
    {
        "text": "Open compound fracture of right humerus after ladder fall, bone protruding through skin, active oozing bleeding",
        "age": 46, "duration_minutes": 30, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 1, "has_altered_mental_status": 0, "priority": "HIGH"
    },
    {
        "text": "Boiling grease splash covering both forearms and anterior abdomen, extensive second-degree blisters, extreme pain",
        "age": 34, "duration_minutes": 25, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "HIGH"
    },
    {
        "text": "Acute right lower quadrant abdominal pain with severe guarding, rebound tenderness, high fever 102.8F, rigid belly",
        "age": 21, "duration_minutes": 240, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "HIGH"
    },
    {
        "text": "Industrial battery acid splashed into right eye, excruciating pain, chemical conjunctivitis, inability to open eyelids",
        "age": 38, "duration_minutes": 15, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "HIGH"
    },
    {
        "text": "Diabetic ketoacidosis: Type 1 diabetic with blood glucose 480 mg/dL, heavy Kussmaul respirations, fruity breath, vomiting",
        "age": 28, "duration_minutes": 360, "has_breathing_difficulty": 1, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 1, "priority": "HIGH"
    },
    {
        "text": "Pitbull attack lacerations to calf and thigh with exposed muscle tissue, bleeding controlled by compressive wrap",
        "age": 40, "duration_minutes": 35, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 1, "has_altered_mental_status": 0, "priority": "HIGH"
    },
    {
        "text": "Sudden onset thunderclap headache described as worst pain in life, stiff neck, photophobia, vomited 3 times",
        "age": 51, "duration_minutes": 50, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "HIGH"
    },
    {
        "text": "Concussion following rugby tackle: brief 60-second knockout, now awake but repeated amnesia, vomiting, confused",
        "age": 18, "duration_minutes": 45, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 1, "has_altered_mental_status": 1, "priority": "HIGH"
    },
    {
        "text": "High electric shock from 220V appliance, entrance burn on right palm, exit wound on left foot, heart palpitations",
        "age": 33, "duration_minutes": 20, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 1, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "HIGH"
    },
    {
        "text": "Severe testicular torsion: sudden excruciating right testicular pain 9/10, swollen, tender, nausea and vomiting",
        "age": 16, "duration_minutes": 90, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "HIGH"
    },
    {
        "text": "Ectopic pregnancy concern: 6 weeks pregnant, acute severe lower abdominal cramping with vaginal bleeding, shoulder tip pain",
        "age": 27, "duration_minutes": 120, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "HIGH"
    },
    {
        "text": "Severe acute epiglottitis: adult with high fever, sore throat, severe difficulty swallowing saliva, leaning forward drooling",
        "age": 43, "duration_minutes": 180, "has_breathing_difficulty": 1, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "HIGH"
    },
    {
        "text": "Third trimester pregnancy with severe headache, visual scotomas, blood pressure 180/110, hyperreflexia, preeclampsia",
        "age": 31, "duration_minutes": 90, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "HIGH"
    },
    {
        "text": "Severe acute gastrointestinal bleed: passing large amounts of dark maroon melena, feeling very lightheaded upon standing",
        "age": 65, "duration_minutes": 120, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 1, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "HIGH"
    },
    {
        "text": "Acute eye trauma: metal shard flew into cornea while angle grinding without goggles, foreign body sensation, severe pain",
        "age": 29, "duration_minutes": 40, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "HIGH"
    },
    {
        "text": "Active suicidal ideation with lethal intent and plan, severe agitation and psychological distress, requires constant observation",
        "age": 24, "duration_minutes": 60, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 1, "priority": "HIGH"
    },
    {
        "text": "Severe acute pancreatitis: excruciating epigastric boring pain radiating to mid-back, persistent dry retching and dehydration",
        "age": 47, "duration_minutes": 300, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "HIGH"
    },
    {
        "text": "Deep nail puncture through shoe into heel, rapid spreading erythema, ascending red streaks, fever 102F, acute cellulitis",
        "age": 37, "duration_minutes": 1440, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "HIGH"
    },
    {
        "text": "High velocity power saw kickback causing deep laceration across quadriceps, heavy venous bleeding controlled with pressure bandage",
        "age": 42, "duration_minutes": 25, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 1, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 1, "has_altered_mental_status": 0, "priority": "HIGH"
    },
    {
        "text": "Severe croup in 18-month toddler: barking cough, loud inspiratory stridor at rest, chest wall indrawing, high fever 103F",
        "age": 1, "duration_minutes": 120, "has_breathing_difficulty": 1, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "HIGH"
    },
    {
        "text": "Elderly patient on Coumadin fell striking occiput, large expanding subgaleal hematoma, disoriented to day and month",
        "age": 78, "duration_minutes": 60, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 1, "has_altered_mental_status": 1, "priority": "HIGH"
    },
    {
        "text": "Acute carbon monoxide exposure: family of three with severe throbbing headache, dizziness, nausea after heater malfunction",
        "age": 35, "duration_minutes": 180, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 1, "priority": "HIGH"
    },
    {
        "text": "Known severe hemophiliac patient bumped knee against concrete wall, rapid tense hemarthrosis swelling, severe pain",
        "age": 22, "duration_minutes": 45, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "HIGH"
    },
    {
        "text": "Severe acute kidney infection (pyelonephritis): unilateral flank pain 9/10, shaking chills, rigor, temp 103.5F, nausea",
        "age": 26, "duration_minutes": 480, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "HIGH"
    },
    {
        "text": "Severe asthma in 10-year-old child: using intercostal accessory muscles to breathe, peak flow < 50%, pale, unable to speak full sentences",
        "age": 10, "duration_minutes": 45, "has_breathing_difficulty": 1, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "HIGH"
    },
    {
        "text": "Severe pelvic trauma after being pinned between parked car and trailer, intense pelvic ring pain, unable to move legs",
        "age": 49, "duration_minutes": 30, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 1, "has_altered_mental_status": 0, "priority": "HIGH"
    },
    {
        "text": "Deep glass laceration on volar wrist from broken picture frame, brisk venous bleeding, paresthesia in thumb and index finger",
        "age": 31, "duration_minutes": 20, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 1, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "HIGH"
    },
    {
        "text": "Chemical caustic ingestion: toddler swallowed two sips of alkaline toilet cleaner, oral mucosal burning, intense crying, drooling",
        "age": 2, "duration_minutes": 15, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "HIGH"
    },
    {
        "text": "Severe hypokalemia paralysis: patient on diuretics with profound generalized muscle flaccidity, cardiac palpitations, muscle cramps",
        "age": 60, "duration_minutes": 240, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "HIGH"
    },
    {
        "text": "Displaced trimalleolar ankle fracture with skin tenting over medial malleolus, severe deformity, acute neurovascular compromise risk",
        "age": 53, "duration_minutes": 40, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 1, "has_altered_mental_status": 0, "priority": "HIGH"
    },
    {
        "text": "Acute sickle cell vaso-occlusive pain crisis: agonizing bone pain in back and legs 10/10, refractory to home opioid prescription",
        "age": 20, "duration_minutes": 180, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "HIGH"
    },
    {
        "text": "Severe thermal burn on right hand and fingers from hot exhaust pipe, circumferential white charred dermis, loss of tactile sensation",
        "age": 39, "duration_minutes": 35, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "HIGH"
    },
    {
        "text": "Acute severe diverticulitis: left lower quadrant peritoneal guarding, rebound tenderness, high fever 102.5F, obstipation",
        "age": 58, "duration_minutes": 720, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "HIGH"
    },
    {
        "text": "Suspected bacterial meningitis: young adult with sudden fever 104F, severe neck stiffness, unable to touch chin to chest, petechial rash",
        "age": 19, "duration_minutes": 240, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 1, "priority": "HIGH"
    },
    {
        "text": "Open pneumothorax: deep nail gun accidental puncture into right lateral chest, painful respiration, localized subcutaneous emphysema",
        "age": 41, "duration_minutes": 30, "has_breathing_difficulty": 1, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 1, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 1, "has_altered_mental_status": 0, "priority": "HIGH"
    },

    # ==================== MODERATE (ESI LEVEL 3: URGENT) ====================
    {
        "text": "Inversion ankle injury while jogging on trail, moderate lateral malleolus edema and ecchymosis, limping with pain",
        "age": 28, "duration_minutes": 90, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "MODERATE"
    },
    {
        "text": "Kitchen knife laceration to left index finger while slicing bagel, 2cm gaping wound, bleeding stopped with firm gauze pressure",
        "age": 35, "duration_minutes": 25, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "MODERATE"
    },
    {
        "text": "Mild to moderate asthma flareup after walking through autumn park, audible mild wheezing, albuterol gives good temporary relief",
        "age": 22, "duration_minutes": 120, "has_breathing_difficulty": 1, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "MODERATE"
    },
    {
        "text": "Superficial thermal burn on palm from touching hot oven rack, redness and small 1cm intact blister, stinging discomfort",
        "age": 30, "duration_minutes": 20, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "MODERATE"
    },
    {
        "text": "Acute uncomplicated gastroenteritis: nausea, non-bloody watery diarrhea 4 times today, can keep small sips of oral electrolyte fluid down",
        "age": 31, "duration_minutes": 720, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "MODERATE"
    },
    {
        "text": "Adult with fever 101.8F, painful swallowing, tender anterior cervical lymph nodes, tonsillar exudate, no breathing distress",
        "age": 24, "duration_minutes": 1440, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "MODERATE"
    },
    {
        "text": "Moderate migraine attack with pulsating left temporal throbbing, nausea and photophobia, typical history of menstrual migraine",
        "age": 29, "duration_minutes": 180, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "MODERATE"
    },
    {
        "text": "Suspected urinary tract infection in young woman: severe burning dysuria, urinary frequency every 20 mins, suprapubic ache, afebrile",
        "age": 27, "duration_minutes": 480, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "MODERATE"
    },
    {
        "text": "Fell onto outstretched hand playing volleyball, moderate wrist swelling and dorsal tenderness, anatomical snuffbox non-tender",
        "age": 20, "duration_minutes": 60, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "MODERATE"
    },
    {
        "text": "Deep wood splinter jammed under thumbnail after woodworking, painful throbbing and localized redness, unable to remove at home",
        "age": 42, "duration_minutes": 300, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "MODERATE"
    },
    {
        "text": "Acute conjunctivitis in both eyes: waking up with eyelids crusted shut, thick yellow discharge, gritty sensation, normal vision",
        "age": 14, "duration_minutes": 720, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "MODERATE"
    },
    {
        "text": "Child with right ear pain and tugging at ear, temp 101F, crying during night after head cold, acute otitis media suspected",
        "age": 5, "duration_minutes": 480, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "MODERATE"
    },
    {
        "text": "Localized hives and intensely itchy wheals on forearms after handling pine needles in garden, normal breathing, no lip swelling",
        "age": 36, "duration_minutes": 120, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "MODERATE"
    },
    {
        "text": "Acute back muscle spasm after lifting heavy couch, bilateral paraspinal tenderness, no radiating pain, no bowel or bladder changes",
        "age": 45, "duration_minutes": 180, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "MODERATE"
    },
    {
        "text": "Minor dog bite on calf from neighbor's small terrier, puncture wounds broke skin, bleeding stopped, requires antibiotic consideration",
        "age": 33, "duration_minutes": 45, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "MODERATE"
    },
    {
        "text": "Small superficial corneal abrasion from baby fingernail scratch, foreign body sensation, excessive tearing, photophobia",
        "age": 28, "duration_minutes": 90, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "MODERATE"
    },
    {
        "text": "Suspected non-displaced finger fracture: basketball jammed directly against tip of ring finger, swollen PIP joint, painful flexion",
        "age": 17, "duration_minutes": 60, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "MODERATE"
    },
    {
        "text": "Acute localized skin abscess on upper arm, 2cm fluctuant tender red mass with purulent center, fever 99.5F, needs drainage",
        "age": 39, "duration_minutes": 2880, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "MODERATE"
    },
    {
        "text": "Colicky right flank pain waxing and waning for 3 hours, radiating to right lower quadrant, small amount of pink urine, suspected renal calculus",
        "age": 41, "duration_minutes": 180, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "MODERATE"
    },
    {
        "text": "Mild whiplash neck soreness and stiffness following low-speed rear bumper tap in traffic yesterday, full neurological exam normal",
        "age": 35, "duration_minutes": 1440, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "MODERATE"
    },
    {
        "text": "Stubbed little toe hard against doorframe, toe is purple and bruised, painful to walk on, no bone protrusion or angulation",
        "age": 26, "duration_minutes": 40, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "MODERATE"
    },
    {
        "text": "Acute painful hemorrhoid thrombosis, marble-sized tender purplish perianal lump, severe discomfort when sitting, no melena",
        "age": 50, "duration_minutes": 1440, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "MODERATE"
    },
    {
        "text": "Hot soup splash to upper lip and chin, reddened skin with tiny pinpoint vesicle blisters, immediate cold water applied",
        "age": 23, "duration_minutes": 15, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "MODERATE"
    },
    {
        "text": "Superficial cut on chin from falling off skateboard, 2cm laceration through subcutaneous fat, bleeding controlled with direct pressure",
        "age": 15, "duration_minutes": 30, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "MODERATE"
    },
    {
        "text": "Severe sunburn on upper back with multiple tense blisters after spending 4 hours at lake without sunscreen, shivering with mild chills",
        "age": 21, "duration_minutes": 720, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "MODERATE"
    },
    {
        "text": "Acute gout attack: sudden onset excruciating pain, swelling, and redness in first metatarsophalangeal joint of right big toe",
        "age": 55, "duration_minutes": 360, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "MODERATE"
    },
    {
        "text": "Contact dermatitis with oozing vesicular rash on both calves after walking through thick weeds, severe pruritus, afebrile",
        "age": 34, "duration_minutes": 1440, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "MODERATE"
    },
    {
        "text": "Swallowed a small fish bone during dinner, foreign body sensation in oropharynx when swallowing, normal airway, no stridor",
        "age": 44, "duration_minutes": 60, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "MODERATE"
    },
    {
        "text": "Stepped on a rusty staple in garage, puncture wound to ball of left foot, minimal bleeding, needs tetanus booster update",
        "age": 38, "duration_minutes": 45, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "MODERATE"
    },
    {
        "text": "Hamstring muscle pull while sprinting for train, sudden sharp pop in posterior thigh, moderate swelling, unable to run",
        "age": 32, "duration_minutes": 75, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "MODERATE"
    },
    {
        "text": "Mild acute diverticulitis flare in known patient: mild left lower quadrant crampy tenderness, temp 99.8F, passing flatus normally",
        "age": 62, "duration_minutes": 1440, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "MODERATE"
    },
    {
        "text": "Acute paronychia: throbbing swollen erythematous periungual fold on right middle finger with localized collection of pus",
        "age": 29, "duration_minutes": 2880, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "MODERATE"
    },
    {
        "text": "Subungual hematoma covering 40% of thumbnail after slamming thumb in car door, throbbing pressure pain, intact nail bed",
        "age": 25, "duration_minutes": 30, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "MODERATE"
    },
    {
        "text": "Child slipped on pool deck, 2.5cm linear forehead laceration, bleeding stopped with direct pressure, no loss of consciousness, playful",
        "age": 6, "duration_minutes": 20, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "MODERATE"
    },
    {
        "text": "Adult with acute painful outer ear infection (otitis externa): extreme tenderness when pulling ear pinna, canal swollen, yellow discharge",
        "age": 33, "duration_minutes": 1440, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "MODERATE"
    },
    {
        "text": "Slipped on ice, bruised left hip and lateral thigh, moderate localized contusion, able to bear weight with discomfort, no bone deformity",
        "age": 48, "duration_minutes": 90, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "MODERATE"
    },
    {
        "text": "Acute epistaxis: nosebleed lasting 25 minutes after sneezing, slowed down significantly after holding continuous pressure on soft nostril",
        "age": 22, "duration_minutes": 25, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "MODERATE"
    },
    {
        "text": "Superficial cat scratch on forearm with mild surrounding erythema 1cm, washed thoroughly with soap and water, feels warm to touch",
        "age": 37, "duration_minutes": 720, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "MODERATE"
    },
    {
        "text": "Mild acute knee joint effusion after awkward twist playing tennis, moderate swelling, stable ligaments on self-test, limping",
        "age": 40, "duration_minutes": 180, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "MODERATE"
    },

    # ==================== LOW (ESI LEVEL 4 & 5: LESS URGENT / NON-URGENT) ====================
    {
        "text": "Small paper cut on index finger while opening mail envelope, tiny droplet of blood stopped immediately, mild stinging",
        "age": 24, "duration_minutes": 5, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "LOW"
    },
    {
        "text": "Mild scratch from kitten on back of hand, superficial epidermis barely broken, washed with soap and water, band-aid placed",
        "age": 28, "duration_minutes": 10, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "LOW"
    },
    {
        "text": "Mild tension headache across forehead after 8 continuous hours working on computer screen, no nausea or vision changes",
        "age": 34, "duration_minutes": 120, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "LOW"
    },
    {
        "text": "Mild dry cough and clear runny nose for 4 days, afebrile, lungs clear, normal appetite, feels like typical common cold",
        "age": 39, "duration_minutes": 5760, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "LOW"
    },
    {
        "text": "Small superficial bruise on shin after bumping into low coffee table, full range of knee and ankle motion, no swelling",
        "age": 31, "duration_minutes": 60, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "LOW"
    },
    {
        "text": "First degree mild sunburn on shoulders after 45 minutes at outdoor pool, pink skin, no blistering or peeling, mild warm sensation",
        "age": 22, "duration_minutes": 240, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "LOW"
    },
    {
        "text": "Dry, chapped lips and small superficial corner fissure from cold windy winter weather, mild stinging with salty food",
        "age": 19, "duration_minutes": 1440, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "LOW"
    },
    {
        "text": "Delayed onset muscle soreness in quadriceps and calves 24 hours after beginning new couch-to-5k running program",
        "age": 27, "duration_minutes": 1440, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "LOW"
    },
    {
        "text": "Single mosquito bite on lateral ankle, mildly pruritic red bump 5mm across, no spreading redness, no systemic symptoms",
        "age": 33, "duration_minutes": 180, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "LOW"
    },
    {
        "text": "Lost soft contact lens inside eye, mild scratchy irritation, lens removed, eye rinsed with saline, mild conjunctival pinkness",
        "age": 25, "duration_minutes": 30, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "LOW"
    },
    {
        "text": "Persistent benign hiccups lasting 20 minutes after drinking cold fizzy soda rapidly, otherwise completely asymptomatic",
        "age": 26, "duration_minutes": 20, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "LOW"
    },
    {
        "text": "Mild general fatigue and sleepiness following 4 hours of sleep before university exam, no fever or physical pain",
        "age": 21, "duration_minutes": 480, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "LOW"
    },
    {
        "text": "Tiny hangnail on right thumb pulled slightly, minor localized tenderness, no pus, no spreading redness, band-aid applied",
        "age": 30, "duration_minutes": 45, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "LOW"
    },
    {
        "text": "Minor friction blister on back of heel from wearing new leather dress shoes, intact fluid blister 5mm, mildly uncomfortable walking",
        "age": 29, "duration_minutes": 120, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "LOW"
    },
    {
        "text": "Minor paper staple scratch on palm, tiny 2mm superficial mark, wiped with alcohol pad, no bleeding, no pain",
        "age": 36, "duration_minutes": 15, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "LOW"
    },
    {
        "text": "Mild nasal congestion and seasonal sneezing from spring tree pollen, eyes itchy, normal energy level, no fever",
        "age": 32, "duration_minutes": 2880, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "LOW"
    },
    {
        "text": "Routine suture removal request: 4 simple nylon stitches on forearm from resolved minor laceration 10 days ago, wound completely healed",
        "age": 41, "duration_minutes": 14400, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "LOW"
    },
    {
        "text": "Small superficial splinter in index finger pad, easily visible under skin, no pain unless directly pressed on",
        "age": 38, "duration_minutes": 60, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "LOW"
    },
    {
        "text": "Mild transient reflux / heartburn after eating large pepperoni pizza and garlic bread, resolved after drinking water and antacid tablet",
        "age": 43, "duration_minutes": 60, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "LOW"
    },
    {
        "text": "Superficial shaving nick on upper lip, pinpoint bleeding ceased immediately after applying styptic pencil / tissue piece",
        "age": 27, "duration_minutes": 10, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "LOW"
    },
    {
        "text": "Mild post-nasal drip and throat tickle without fever, normal swallowing, lungs clear on auscultation, drinking warm tea",
        "age": 35, "duration_minutes": 2880, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "LOW"
    },
    {
        "text": "Mild localized skin peeling on nose following a beach holiday last weekend, no erythema, applying moisturizing lotion",
        "age": 23, "duration_minutes": 4320, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "LOW"
    },
    {
        "text": "Small superficial bruise on forearm from carrying heavy cardboard box, size of a coin, no bone pain, full wrist motion",
        "age": 31, "duration_minutes": 180, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "LOW"
    },
    {
        "text": "Mild neck muscle stiffness from sleeping in an awkward position on an airplane flight, full range of head rotation with mild ache",
        "age": 45, "duration_minutes": 480, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "LOW"
    },
    {
        "text": "Minor paper cut on palm from wrapping Christmas present, small surface scrape, band-aid applied, no further bleeding",
        "age": 26, "duration_minutes": 15, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "LOW"
    },
    {
        "text": "Mild episodic dry eye irritation after driving with car air conditioning blowing directly on face, resolved after lubricating eye drops",
        "age": 52, "duration_minutes": 60, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "LOW"
    },
    {
        "text": "Small painless white aphthous canker sore inside lower lip for 2 days, mild stinging when drinking orange juice",
        "age": 22, "duration_minutes": 2880, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "LOW"
    },
    {
        "text": "Routine blood pressure measurement check-up, patient feels great, reading is 122/78 mmHg, no symptoms",
        "age": 58, "duration_minutes": 15, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "LOW"
    },
    {
        "text": "Superficial briar bush scratch on shin while hiking, 3cm light surface scratch, clean and dry, no infection signs",
        "age": 30, "duration_minutes": 120, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "LOW"
    },
    {
        "text": "Mild headache relieved completely within 20 minutes of taking one 200mg ibuprofen tablet, no other symptoms",
        "age": 28, "duration_minutes": 45, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "LOW"
    },
    {
        "text": "Minor sunburn on forehead after afternoon gardening, slightly pink, no blisters, cool wet washcloth provides soothing relief",
        "age": 47, "duration_minutes": 180, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "LOW"
    },
    {
        "text": "Mild dry skin itching on back after taking very hot bath in winter, relieved after applying ceramide moisturizing cream",
        "age": 64, "duration_minutes": 60, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "LOW"
    },
    {
        "text": "Superficial finger graze from scraping against rough stucco wall while painting, washed with soap and water, band-aid placed",
        "age": 37, "duration_minutes": 30, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "LOW"
    },
    {
        "text": "Transient lightheadedness for 3 seconds after standing up too quickly from warm couch, fully resolved immediately with normal walking",
        "age": 20, "duration_minutes": 5, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "LOW"
    },
    {
        "text": "Minor paper cut on pinky finger from office cardboard filing box, tiny blood speck stopped, applying pressure for 30 seconds",
        "age": 33, "duration_minutes": 10, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "LOW"
    },
    {
        "text": "Mild seasonal allergic rhinitis, intermittent clear nasal discharge, normal temperature 98.4F, no cough, normal activity",
        "age": 25, "duration_minutes": 4320, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "LOW"
    },
    {
        "text": "Small superficial red bump on wrist from outdoor gardening, non-tender, mild itchiness, hydrocortisone cream applied",
        "age": 42, "duration_minutes": 240, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "LOW"
    },
    {
        "text": "Mild muscular tenderness in neck after reading book on couch with poor neck posture, full painless neck range of motion",
        "age": 51, "duration_minutes": 180, "has_breathing_difficulty": 0, "has_unconsciousness": 0,
        "has_severe_bleeding": 0, "has_chest_pain": 0, "has_stroke_symptoms": 0, "has_anaphylaxis_symptoms": 0,
        "has_severe_trauma": 0, "has_altered_mental_status": 0, "priority": "LOW"
    }
]

df_new = pd.DataFrame(new_cases)

# Combine original 50 samples + 150 new samples = 200 total samples
cols = [
    "text", "age", "duration_minutes", "has_breathing_difficulty",
    "has_unconsciousness", "has_severe_bleeding", "has_chest_pain",
    "has_stroke_symptoms", "has_anaphylaxis_symptoms", "has_severe_trauma",
    "has_altered_mental_status", "priority"
]

df_orig_aligned = df_orig[cols].copy()
df_new_aligned = df_new[cols].copy()

df_combined = pd.concat([df_orig_aligned, df_new_aligned], ignore_index=True)

# Shuffle with reproducible seed
df_combined = df_combined.sample(frac=1.0, random_state=42).reset_index(drop=True)

out_csv = BASE_DIR / "data" / "training_data" / "emergency_triage_dataset_clinical.csv"
df_combined.to_csv(out_csv, index=False)

print(f"Successfully generated clinical triage dataset with {len(df_combined)} samples:")
print(df_combined["priority"].value_counts())
print(f"Saved to {out_csv}")
