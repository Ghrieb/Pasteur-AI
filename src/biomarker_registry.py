"""Medical Knowledge Layer — Institut Pasteur biomarker registry.

Each entry contains:
  code, canonical_name, french_name, category, system,
  dashboard_group, description, unit
"""

import re
from difflib import SequenceMatcher

BIOMARKER_REGISTRY: dict[str, dict] = {
    # ── Hématologie / NFS ─────────────────────────────────
    "Globules Blancs": {
        "code": "WBC", "canonical_name": "White Blood Cells",
        "french_name": "Globules Blancs", "category": "Hematology",
        "system": "Hematopoietic", "dashboard_group": "Blood Count",
        "description": "Total white blood cell count; elevated in infection, inflammation, or leukemia.",
        "unit": "10*3/uL",
    },
    "Globules Rouges": {
        "code": "RBC", "canonical_name": "Red Blood Cells",
        "french_name": "Globules Rouges", "category": "Hematology",
        "system": "Hematopoietic", "dashboard_group": "Blood Count",
        "description": "Total red blood cell count; low in anemia, high in polycythemia.",
        "unit": "10*6/uL",
    },
    "Hémoglobine": {
        "code": "HGB", "canonical_name": "Hemoglobin",
        "french_name": "Hémoglobine", "category": "Hematology",
        "system": "Hematopoietic", "dashboard_group": "Blood Count",
        "description": "Oxygen-carrying protein; low indicates anemia, high in polycythemia.",
        "unit": "g/dL",
    },
    "Hématocrite": {
        "code": "HCT", "canonical_name": "Hematocrit",
        "french_name": "Hématocrite", "category": "Hematology",
        "system": "Hematopoietic", "dashboard_group": "Blood Count",
        "description": "Volume percentage of red blood cells; low in anemia, high in polycythemia.",
        "unit": "%",
    },
    "V.G.M": {
        "code": "MCV", "canonical_name": "Mean Corpuscular Volume",
        "french_name": "V.G.M", "category": "Hematology",
        "system": "Hematopoietic", "dashboard_group": "Blood Count",
        "description": "Average red blood cell size; low in microcytic anemia, high in macrocytic anemia.",
        "unit": "fL",
    },
    "T.G.M.H": {
        "code": "MCH", "canonical_name": "Mean Corpuscular Hemoglobin",
        "french_name": "T.G.M.H", "category": "Hematology",
        "system": "Hematopoietic", "dashboard_group": "Blood Count",
        "description": "Average hemoglobin mass per red blood cell.",
        "unit": "pg",
    },
    "C.C.M.H": {
        "code": "MCHC", "canonical_name": "Mean Corpuscular Hemoglobin Concentration",
        "french_name": "C.C.M.H", "category": "Hematology",
        "system": "Hematopoietic", "dashboard_group": "Blood Count",
        "description": "Hemoglobin concentration per unit volume of red blood cells.",
        "unit": "g/dL",
    },
    "Indice de distribution des GR": {
        "code": "RDW", "canonical_name": "Red Cell Distribution Width",
        "french_name": "Indice de distribution des GR", "category": "Hematology",
        "system": "Hematopoietic", "dashboard_group": "Blood Count",
        "description": "Variability in red blood cell size; elevated in iron deficiency or B12 deficiency.",
        "unit": "%",
    },
    "Plaquettes": {
        "code": "PLT", "canonical_name": "Platelets",
        "french_name": "Plaquettes", "category": "Hematology",
        "system": "Hematopoietic", "dashboard_group": "Blood Count",
        "description": "Cell fragments involved in clotting; low in thrombocytopenia, high in thrombocytosis.",
        "unit": "10*3/uL",
    },
    "Volume plaquettaire moyen": {
        "code": "MPV", "canonical_name": "Mean Platelet Volume",
        "french_name": "Volume plaquettaire moyen", "category": "Hematology",
        "system": "Hematopoietic", "dashboard_group": "Blood Count",
        "description": "Average platelet size; increased in platelet destruction disorders.",
        "unit": "fL",
    },
    "Indice de distribution plaquettaire": {
        "code": "PDW", "canonical_name": "Platelet Distribution Width",
        "french_name": "Indice de distribution plaquettaire", "category": "Hematology",
        "system": "Hematopoietic", "dashboard_group": "Blood Count",
        "description": "Variability in platelet size; correlates with platelet activation.",
        "unit": "fL",
    },
    # ── Equilibre Leucocytaire ──────────────────────────
    "P. Neutrophiles": {
        "code": "NEUT", "canonical_name": "Neutrophils",
        "french_name": "P. Neutrophiles", "category": "Hematology",
        "system": "Hematopoietic", "dashboard_group": "White Cell Differential",
        "description": "Primary defense against bacterial infection; elevated in bacterial infections.",
        "unit": "10*3/mm3",
    },
    "P. Neutrophiles %": {
        "code": "NEUT_PCT", "canonical_name": "Neutrophils Percentage",
        "french_name": "P. Neutrophiles %", "category": "Hematology",
        "system": "Hematopoietic", "dashboard_group": "White Cell Differential",
        "description": "Neutrophils as a percentage of total white blood cells.",
        "unit": "%",
    },
    "P. Eosinophiles": {
        "code": "EO", "canonical_name": "Eosinophils",
        "french_name": "P. Eosinophiles", "category": "Hematology",
        "system": "Hematopoietic", "dashboard_group": "White Cell Differential",
        "description": "Elevated in allergic reactions, parasitic infections, and asthma.",
        "unit": "10*3/mm3",
    },
    "P. Eosinophiles %": {
        "code": "EO_PCT", "canonical_name": "Eosinophils Percentage",
        "french_name": "P. Eosinophiles %", "category": "Hematology",
        "system": "Hematopoietic", "dashboard_group": "White Cell Differential",
        "description": "Eosinophils as a percentage of total white blood cells.",
        "unit": "%",
    },
    "P. Basophiles": {
        "code": "BASO", "canonical_name": "Basophils",
        "french_name": "P. Basophiles", "category": "Hematology",
        "system": "Hematopoietic", "dashboard_group": "White Cell Differential",
        "description": "Least common granulocyte; involved in inflammatory and allergic responses.",
        "unit": "10*3/mm3",
    },
    "P. Basophiles%": {
        "code": "BASO_PCT", "canonical_name": "Basophils Percentage",
        "french_name": "P. Basophiles%", "category": "Hematology",
        "system": "Hematopoietic", "dashboard_group": "White Cell Differential",
        "description": "Basophils as a percentage of total white blood cells.",
        "unit": "%",
    },
    "Monocytes": {
        "code": "MONO", "canonical_name": "Monocytes",
        "french_name": "Monocytes", "category": "Hematology",
        "system": "Hematopoietic", "dashboard_group": "White Cell Differential",
        "description": "Migrate to tissues as macrophages; elevated in chronic infections and inflammation.",
        "unit": "10*3/mm3",
    },
    "Monocytes %": {
        "code": "MONO_PCT", "canonical_name": "Monocytes Percentage",
        "french_name": "Monocytes %", "category": "Hematology",
        "system": "Hematopoietic", "dashboard_group": "White Cell Differential",
        "description": "Monocytes as a percentage of total white blood cells.",
        "unit": "%",
    },
    "Lymphocytes": {
        "code": "LYMPH", "canonical_name": "Lymphocytes",
        "french_name": "Lymphocytes", "category": "Hematology",
        "system": "Hematopoietic", "dashboard_group": "White Cell Differential",
        "description": "Key to adaptive immunity; T-cells, B-cells, NK cells; elevated in viral infections.",
        "unit": "10*3/mm3",
    },
    "Lymphocytes%": {
        "code": "LYMPH_PCT", "canonical_name": "Lymphocytes Percentage",
        "french_name": "Lymphocytes%", "category": "Hematology",
        "system": "Hematopoietic", "dashboard_group": "White Cell Differential",
        "description": "Lymphocytes as a percentage of total white blood cells.",
        "unit": "%",
    },
    # ── VS (Vitesse de Sédimentation) ────────────────────
    "Première heure": {
        "code": "ESR_1H", "canonical_name": "Erythrocyte Sedimentation Rate 1H",
        "french_name": "Première heure", "category": "Hematology",
        "system": "Hematopoietic", "dashboard_group": "Inflammation",
        "description": "Nonspecific inflammation marker; rate of red cell沉降 after one hour.",
        "unit": "mm",
    },
    "Deuxième heure": {
        "code": "ESR_2H", "canonical_name": "Erythrocyte Sedimentation Rate 2H",
        "french_name": "Deuxième heure", "category": "Hematology",
        "system": "Hematopoietic", "dashboard_group": "Inflammation",
        "description": "Extended sedimentation reading; used to calculate sedimentation velocity.",
        "unit": "mm",
    },
    # ── Hormonologie ────────────────────────────────────
    "TSH us": {
        "code": "TSH", "canonical_name": "Thyroid Stimulating Hormone (ultrasensitive)",
        "french_name": "TSH us", "category": "Thyroid Function",
        "system": "Endocrine", "dashboard_group": "Thyroid",
        "description": "Pituitary hormone regulating thyroid; high in hypothyroidism, low in hyperthyroidism.",
        "unit": "m[IU]/L",
    },
    "FT4": {
        "code": "FT4", "canonical_name": "Free Thyroxine",
        "french_name": "FT4", "category": "Thyroid Function",
        "system": "Endocrine", "dashboard_group": "Thyroid",
        "description": "Active thyroid hormone; low in hypothyroidism, high in hyperthyroidism.",
        "unit": "ng/dL",
    },
    "FT3": {
        "code": "FT3", "canonical_name": "Free Triiodothyronine",
        "french_name": "FT3", "category": "Thyroid Function",
        "system": "Endocrine", "dashboard_group": "Thyroid",
        "description": "Most potent thyroid hormone; regulates metabolism and development.",
        "unit": "pg/mL",
    },
    "Vitamine D (25-OH Vit D)": {
        "code": "VITD", "canonical_name": "25-Hydroxyvitamin D",
        "french_name": "Vitamine D (25-OH Vit D)", "category": "Vitamins & Nutrition",
        "system": "Metabolic", "dashboard_group": "Vitamins",
        "description": "Vitamin D status marker; deficiency linked to bone disorders and immune dysfunction.",
        "unit": "ng/mL",
    },
    "Vitamine B12": {
        "code": "VITB12", "canonical_name": "Vitamin B12",
        "french_name": "Vitamine B12", "category": "Vitamins & Nutrition",
        "system": "Metabolic", "dashboard_group": "Vitamins",
        "description": "Essential for nerve function and RBC formation; deficiency causes macrocytic anemia.",
        "unit": "pg/mL",
    },
    "Vitamine B9 (Folates)": {
        "code": "FOLATE", "canonical_name": "Folate / Vitamin B9",
        "french_name": "Vitamine B9 (Folates)", "category": "Vitamins & Nutrition",
        "system": "Metabolic", "dashboard_group": "Vitamins",
        "description": "Essential for DNA synthesis; deficiency during pregnancy causes neural tube defects.",
        "unit": "ng/mL",
    },
    "Ferritine": {
        "code": "FERRITIN", "canonical_name": "Ferritin",
        "french_name": "Ferritine", "category": "Iron Studies",
        "system": "Hematopoietic", "dashboard_group": "Iron",
        "description": "Iron storage protein; low indicates iron deficiency, high indicates iron overload.",
        "unit": "ng/mL",
    },
    "Cortisol à 8 heures": {
        "code": "CORTISOL_8H", "canonical_name": "Cortisol (8 AM)",
        "french_name": "Cortisol à 8 heures", "category": "Adrenal Function",
        "system": "Endocrine", "dashboard_group": "Adrenal",
        "description": "Morning cortisol; low in adrenal insufficiency, high in Cushing's syndrome.",
        "unit": "ug/dL",
    },
    "Anticorps Anti-Tg": {
        "code": "ANTI_TG", "canonical_name": "Anti-Thyroglobulin Antibodies",
        "french_name": "Anticorps Anti-Tg", "category": "Autoimmunity",
        "system": "Endocrine", "dashboard_group": "Thyroid",
        "description": "Autoantibodies against thyroglobulin; marker for Hashimoto's thyroiditis.",
        "unit": "[IU]/mL",
    },
    "Anticorps Anti-TPO": {
        "code": "ANTI_TPO", "canonical_name": "Anti-Thyroid Peroxidase Antibodies",
        "french_name": "Anticorps Anti-TPO", "category": "Autoimmunity",
        "system": "Endocrine", "dashboard_group": "Thyroid",
        "description": "Autoantibodies against thyroid peroxidase; key marker for autoimmune thyroid disease.",
        "unit": "[IU]/mL",
    },
    # ── Marqueurs tumoraux ──────────────────────────────
    "PSA Total": {
        "code": "PSA", "canonical_name": "Prostate-Specific Antigen (Total)",
        "french_name": "PSA Total", "category": "Tumor Markers",
        "system": "Reproductive", "dashboard_group": "Prostate",
        "description": "Prostate cancer screening marker; elevated in malignancy and benign prostatic hyperplasia.",
        "unit": "ng/mL",
    },
    "PSA Libre": {
        "code": "PSA_FREE", "canonical_name": "Prostate-Specific Antigen (Free)",
        "french_name": "PSA Libre", "category": "Tumor Markers",
        "system": "Reproductive", "dashboard_group": "Prostate",
        "description": "Unbound PSA; low free-to-total ratio suggests higher cancer risk.",
        "unit": "ng/mL",
    },
    # ── Biochimie ───────────────────────────────────────
    "Glycémie à jeun": {
        "code": "GLU", "canonical_name": "Fasting Glucose",
        "french_name": "Glycémie à jeun", "category": "Diabetes & Glucose",
        "system": "Endocrine", "dashboard_group": "Diabetes",
        "description": "Blood sugar after fasting; elevated in diabetes and prediabetes.",
        "unit": "g/L",
    },
    "HbA1c (Hb glyquée)": {
        "code": "HBA1C", "canonical_name": "Glycated Hemoglobin A1c",
        "french_name": "HbA1c (Hb glyquée)", "category": "Diabetes & Glucose",
        "system": "Endocrine", "dashboard_group": "Diabetes",
        "description": "Three-month average blood glucose; gold standard for diabetes monitoring.",
        "unit": "%",
    },
    "Urée": {
        "code": "UREA", "canonical_name": "Urea",
        "french_name": "Urée", "category": "Kidney Function",
        "system": "Renal", "dashboard_group": "Kidney",
        "description": "Nitrogen waste product; elevated in kidney impairment and dehydration.",
        "unit": "g/L",
    },
    "Créatinine": {
        "code": "CREAT", "canonical_name": "Creatinine",
        "french_name": "Créatinine", "category": "Kidney Function",
        "system": "Renal", "dashboard_group": "Kidney",
        "description": "Muscle waste product filtered by kidneys; key marker of renal function.",
        "unit": "mg/L",
    },
    "Acide Urique": {
        "code": "UA", "canonical_name": "Uric Acid",
        "french_name": "Acide Urique", "category": "Kidney Function",
        "system": "Renal", "dashboard_group": "Kidney",
        "description": "Purine metabolism end-product; elevated in gout and kidney disease.",
        "unit": "mg/L",
    },
    "Cholestérol Total": {
        "code": "CHOL", "canonical_name": "Total Cholesterol",
        "french_name": "Cholestérol Total", "category": "Lipid Profile",
        "system": "Cardiovascular", "dashboard_group": "Lipids",
        "description": "Total cholesterol; elevated levels increase cardiovascular disease risk.",
        "unit": "g/L",
    },
    "Cholestérol HDL": {
        "code": "HDL", "canonical_name": "HDL Cholesterol",
        "french_name": "Cholestérol HDL", "category": "Lipid Profile",
        "system": "Cardiovascular", "dashboard_group": "Lipids",
        "description": "'Good' cholesterol; high levels are protective against heart disease.",
        "unit": "g/L",
    },
    "Cholestérol LDL": {
        "code": "LDL", "canonical_name": "LDL Cholesterol",
        "french_name": "Cholestérol LDL", "category": "Lipid Profile",
        "system": "Cardiovascular", "dashboard_group": "Lipids",
        "description": "'Bad' cholesterol; elevated levels lead to atherosclerosis.",
        "unit": "g/L",
    },
    "Triglycérides": {
        "code": "TG", "canonical_name": "Triglycerides",
        "french_name": "Triglycérides", "category": "Lipid Profile",
        "system": "Cardiovascular", "dashboard_group": "Lipids",
        "description": "Blood fat; elevated levels increase cardiovascular and pancreatitis risk.",
        "unit": "g/L",
    },
    "Calcium Total": {
        "code": "CA", "canonical_name": "Total Calcium",
        "french_name": "Calcium Total", "category": "Bone & Mineral",
        "system": "Musculoskeletal", "dashboard_group": "Bone",
        "description": "Total serum calcium; abnormal in parathyroid disorders, bone disease, or malignancy.",
        "unit": "mg/L",
    },
    "Fer sérique": {
        "code": "FE", "canonical_name": "Serum Iron",
        "french_name": "Fer sérique", "category": "Iron Studies",
        "system": "Hematopoietic", "dashboard_group": "Iron",
        "description": "Circulating iron; low in iron deficiency, high in hemochromatosis.",
        "unit": "ug/dL",
    },
    "ASAT": {
        "code": "AST", "canonical_name": "Aspartate Aminotransferase",
        "french_name": "ASAT", "category": "Liver Function",
        "system": "Digestive", "dashboard_group": "Liver",
        "description": "Liver enzyme; elevated in hepatitis, cirrhosis, or muscle injury (also found in heart/muscle).",
        "unit": "U/L",
    },
    "ALAT": {
        "code": "ALT", "canonical_name": "Alanine Aminotransferase",
        "french_name": "ALAT", "category": "Liver Function",
        "system": "Digestive", "dashboard_group": "Liver",
        "description": "Liver-specific enzyme; elevated in hepatitis, fatty liver, or drug-induced liver injury.",
        "unit": "U/L",
    },
    "Phosphatase Alcaline": {
        "code": "ALP", "canonical_name": "Alkaline Phosphatase",
        "french_name": "Phosphatase Alcaline", "category": "Liver Function",
        "system": "Digestive", "dashboard_group": "Liver",
        "description": "Elevated in bile duct obstruction, bone disease, or liver disease.",
        "unit": "U/L",
    },
    "Gamma GT": {
        "code": "GGT", "canonical_name": "Gamma-Glutamyl Transferase",
        "french_name": "Gamma GT", "category": "Liver Function",
        "system": "Digestive", "dashboard_group": "Liver",
        "description": "Elevated in bile duct disease, alcohol use, or liver enzyme induction.",
        "unit": "U/L",
    },
    "Bilirubine Totale": {
        "code": "TBIL", "canonical_name": "Total Bilirubin",
        "french_name": "Bilirubine Totale", "category": "Liver Function",
        "system": "Digestive", "dashboard_group": "Liver",
        "description": "Total bilirubin; elevated in jaundice, liver disease, or hemolysis.",
        "unit": "mg/L",
    },
    "Bilirubine Directe": {
        "code": "DBIL", "canonical_name": "Direct Bilirubin",
        "french_name": "Bilirubine Directe", "category": "Liver Function",
        "system": "Digestive", "dashboard_group": "Liver",
        "description": "Conjugated bilirubin; elevated in obstructive jaundice and hepatocellular disease.",
        "unit": "mg/L",
    },
    "Bilirubine Indirecte": {
        "code": "IBIL", "canonical_name": "Indirect Bilirubin",
        "french_name": "Bilirubine Indirecte", "category": "Liver Function",
        "system": "Digestive", "dashboard_group": "Liver",
        "description": "Unconjugated bilirubin; elevated in hemolysis and Gilbert's syndrome.",
        "unit": "mg/L",
    },
    "Protéine C Réactive (CRP)": {
        "code": "CRP", "canonical_name": "C-Reactive Protein",
        "french_name": "Protéine C Réactive (CRP)", "category": "Inflammation",
        "system": "Immune", "dashboard_group": "Inflammation",
        "description": "Acute-phase protein; rapidly elevated in infection, inflammation, and tissue injury.",
        "unit": "mg/L",
    },
    "CRP": {
        "code": "CRP", "canonical_name": "C-Reactive Protein",
        "french_name": "CRP", "category": "Inflammation",
        "system": "Immune", "dashboard_group": "Inflammation",
        "description": "Acute-phase protein; rapidly elevated in infection, inflammation, and tissue injury.",
        "unit": "mg/L",
    },

    # ── Coagulation ─────────────────────────────────────
    "TP (Taux de Prothrombine)": {
        "code": "PT", "canonical_name": "Prothrombin Time",
        "french_name": "TP (Taux de Prothrombine)", "category": "Coagulation",
        "system": "Hematopoietic", "dashboard_group": "Coagulation",
        "description": "Measures extrinsic coagulation pathway; prolonged in liver disease, vitamin K deficiency, or anticoagulant therapy.",
        "unit": "%",
    },
    "TCK (Temps de Céphaline Kaolin)": {
        "code": "APTT", "canonical_name": "Activated Partial Thromboplastin Time",
        "french_name": "TCK (Temps de Céphaline Kaolin)", "category": "Coagulation",
        "system": "Hematopoietic", "dashboard_group": "Coagulation",
        "description": "Measures intrinsic coagulation pathway; prolonged in hemophilia, lupus anticoagulant, or heparin therapy.",
        "unit": "s",
    },
    "Fibrinogène": {
        "code": "FIB", "canonical_name": "Fibrinogen",
        "french_name": "Fibrinogène", "category": "Coagulation",
        "system": "Hematopoietic", "dashboard_group": "Coagulation",
        "description": "Acute-phase protein converted to fibrin in clotting; low in DIC, high in inflammation.",
        "unit": "g/L",
    },
    "D-Dimères": {
        "code": "DDIM", "canonical_name": "D-Dimer",
        "french_name": "D-Dimères", "category": "Coagulation",
        "system": "Hematopoietic", "dashboard_group": "Coagulation",
        "description": "Fibrin degradation product; elevated in DIC, pulmonary embolism, and deep vein thrombosis.",
        "unit": "ug/L",
    },

    # ── Cardiac Markers ─────────────────────────────────
    "Troponine": {
        "code": "TROP", "canonical_name": "Troponin",
        "french_name": "Troponine", "category": "Cardiac Markers",
        "system": "Cardiovascular", "dashboard_group": "Cardiac Markers",
        "description": "Gold standard for myocardial injury; elevated in acute coronary syndrome and myocardial infarction.",
        "unit": "ng/L",
    },
    "CK-MB": {
        "code": "CKMB", "canonical_name": "Creatine Kinase MB",
        "french_name": "CK-MB", "category": "Cardiac Markers",
        "system": "Cardiovascular", "dashboard_group": "Cardiac Markers",
        "description": "Cardiac-specific isoenzyme of creatine kinase; elevated in myocardial infarction.",
        "unit": "U/L",
    },

    # ── Electrolytes (Ionogramme) ───────────────────────
    "Sodium (Na)": {
        "code": "NA", "canonical_name": "Sodium",
        "french_name": "Sodium (Na)", "category": "Electrolytes",
        "system": "Metabolic", "dashboard_group": "Electrolytes",
        "description": "Major extracellular cation; low in hyponatremia, high in hypernatremia — affects hydration and nerve function.",
        "unit": "mmol/L",
    },
    "Potassium (K)": {
        "code": "K", "canonical_name": "Potassium",
        "french_name": "Potassium (K)", "category": "Electrolytes",
        "system": "Metabolic", "dashboard_group": "Electrolytes",
        "description": "Major intracellular cation; low in hypokalemia, high in hyperkalemia — critical for cardiac rhythm.",
        "unit": "mmol/L",
    },
    "Chlore (Cl)": {
        "code": "CL", "canonical_name": "Chloride",
        "french_name": "Chlore (Cl)", "category": "Electrolytes",
        "system": "Metabolic", "dashboard_group": "Electrolytes",
        "description": "Major extracellular anion; changes parallel sodium in acid-base disorders.",
        "unit": "mmol/L",
    },
    "Bicarbonates (HCO3)": {
        "code": "HCO3", "canonical_name": "Bicarbonate",
        "french_name": "Bicarbonates (HCO3)", "category": "Electrolytes",
        "system": "Metabolic", "dashboard_group": "Electrolytes",
        "description": "Major buffer in acid-base regulation; low in metabolic acidosis, high in metabolic alkalosis.",
        "unit": "mmol/L",
    },
    "Magnésium": {
        "code": "MG", "canonical_name": "Magnesium",
        "french_name": "Magnésium", "category": "Electrolytes",
        "system": "Metabolic", "dashboard_group": "Electrolytes",
        "description": "Essential for enzyme function and neuromuscular transmission; deficiency causes arrhythmia and tetany.",
        "unit": "mg/L",
    },
    "Phosphore": {
        "code": "PHOS", "canonical_name": "Phosphorus",
        "french_name": "Phosphore", "category": "Bone & Mineral",
        "system": "Metabolic", "dashboard_group": "Bone",
        "description": "Essential for bone mineralization and energy metabolism; abnormal in renal disease and parathyroid disorders.",
        "unit": "mg/L",
    },

    # ── Pancreatic Enzymes ──────────────────────────────
    "Amylase": {
        "code": "AMY", "canonical_name": "Amylase",
        "french_name": "Amylase", "category": "Pancreatic Function",
        "system": "Digestive", "dashboard_group": "Pancreas",
        "description": "Pancreatic enzyme; highly elevated in acute pancreatitis, also elevated in mumps and renal failure.",
        "unit": "U/L",
    },
    "Lipase": {
        "code": "LIP", "canonical_name": "Lipase",
        "french_name": "Lipase", "category": "Pancreatic Function",
        "system": "Digestive", "dashboard_group": "Pancreas",
        "description": "Most specific marker for acute pancreatitis; remains elevated longer than amylase.",
        "unit": "U/L",
    },

    # ── Diabetes & Glucose (additions) ──────────────────
    "Glycémie Postprandiale": {
        "code": "GLU_PP", "canonical_name": "Postprandial Glucose",
        "french_name": "Glycémie Postprandiale", "category": "Diabetes & Glucose",
        "system": "Endocrine", "dashboard_group": "Diabetes",
        "description": "Blood glucose measured after a meal; used to assess glucose tolerance and diabetes control.",
        "unit": "g/L",
    },
    "Insuline": {
        "code": "INS", "canonical_name": "Insulin",
        "french_name": "Insuline", "category": "Diabetes & Glucose",
        "system": "Endocrine", "dashboard_group": "Diabetes",
        "description": "Pancreatic hormone regulating glucose uptake; low in type 1 diabetes, high in insulin resistance.",
        "unit": "u[IU]/mL",
    },
    "Peptide C": {
        "code": "CPEP", "canonical_name": "C-Peptide",
        "french_name": "Peptide C", "category": "Diabetes & Glucose",
        "system": "Endocrine", "dashboard_group": "Diabetes",
        "description": "Marker of endogenous insulin secretion; distinguishes type 1 from type 2 diabetes.",
        "unit": "ng/mL",
    },
    "Glucose Urinaire (Glycosurie)": {
        "code": "GLU_U", "canonical_name": "Urine Glucose",
        "french_name": "Glucose Urinaire (Glycosurie)", "category": "Diabetes & Glucose",
        "system": "Renal", "dashboard_group": "Diabetes",
        "description": "Glucose in urine; appears when blood glucose exceeds renal threshold (~1.8 g/L).",
        "unit": "g/L",
    },

    # ── Kidney Function (additions) ─────────────────────
    "Clearance de la Créatinine (DFG)": {
        "code": "EGFR", "canonical_name": "Estimated Glomerular Filtration Rate",
        "french_name": "Clearance de la Créatinine (DFG)", "category": "Kidney Function",
        "system": "Renal", "dashboard_group": "Kidney",
        "description": "Calculated kidney filtration rate; below 60 mL/min indicates chronic kidney disease.",
        "unit": "mL/min",
    },
    "Créatinine Urinaire (Créatininurie)": {
        "code": "CREAT_U", "canonical_name": "Urine Creatinine",
        "french_name": "Créatinine Urinaire (Créatininurie)", "category": "Kidney Function",
        "system": "Renal", "dashboard_group": "Kidney",
        "description": "Urinary creatinine excretion; used to normalize other urinary analytes and assess 24h collection adequacy.",
        "unit": "g/24h",
    },
    "Micro-Albuminurie": {
        "code": "MALB", "canonical_name": "Microalbuminuria",
        "french_name": "Micro-Albuminurie", "category": "Kidney Function",
        "system": "Renal", "dashboard_group": "Kidney",
        "description": "Small amounts of albumin in urine; early marker of diabetic nephropathy and cardiovascular risk.",
        "unit": "mg/L",
    },
    "Acide Urique Urinaire": {
        "code": "UA_U", "canonical_name": "Urine Uric Acid",
        "french_name": "Acide Urique Urinaire", "category": "Kidney Function",
        "system": "Renal", "dashboard_group": "Kidney",
        "description": "Urinary uric acid; helps classify hyperuricemia as overproduction vs underexcretion.",
        "unit": "mg/24h",
    },
    "Urée Urinaire": {
        "code": "UREA_U", "canonical_name": "Urine Urea",
        "french_name": "Urée Urinaire", "category": "Kidney Function",
        "system": "Renal", "dashboard_group": "Kidney",
        "description": "Urinary urea nitrogen; used to assess nitrogen balance and dietary protein intake.",
        "unit": "g/24h",
    },
    "Protéine Urinaire": {
        "code": "PRO_U", "canonical_name": "Urine Protein",
        "french_name": "Protéine Urinaire", "category": "Kidney Function",
        "system": "Renal", "dashboard_group": "Kidney",
        "description": "Protein in urine; elevated in glomerular or tubular kidney disease.",
        "unit": "g/24h",
    },
    "Calcium Urinaire": {
        "code": "CA_U", "canonical_name": "Urine Calcium",
        "french_name": "Calcium Urinaire", "category": "Kidney Function",
        "system": "Renal", "dashboard_group": "Kidney",
        "description": "Urinary calcium excretion; elevated in hyperparathyroidism, low in hypoparathyroidism.",
        "unit": "mg/24h",
    },
    "Magnésium Urinaire": {
        "code": "MG_U", "canonical_name": "Urine Magnesium",
        "french_name": "Magnésium Urinaire", "category": "Kidney Function",
        "system": "Renal", "dashboard_group": "Kidney",
        "description": "Urinary magnesium; helps evaluate renal magnesium handling in deficiency or excess states.",
        "unit": "mg/24h",
    },
    "Phosphore Urinaire": {
        "code": "PHOS_U", "canonical_name": "Urine Phosphorus",
        "french_name": "Phosphore Urinaire", "category": "Kidney Function",
        "system": "Renal", "dashboard_group": "Kidney",
        "description": "Urinary phosphorus; assesses renal phosphate handling in bone and parathyroid disorders.",
        "unit": "g/24h",
    },

    # ── Lipids (additions) ──────────────────────────────
    "Apolipoprotéine A1": {
        "code": "APOA1", "canonical_name": "Apolipoprotein A1",
        "french_name": "Apolipoprotéine A1", "category": "Lipid Profile",
        "system": "Cardiovascular", "dashboard_group": "Lipids",
        "description": "Major protein component of HDL; low levels indicate increased cardiovascular risk.",
        "unit": "g/L",
    },
    "Apolipoprotéine B": {
        "code": "APOB", "canonical_name": "Apolipoprotein B",
        "french_name": "Apolipoprotéine B", "category": "Lipid Profile",
        "system": "Cardiovascular", "dashboard_group": "Lipids",
        "description": "Major protein component of LDL and VLDL; elevated levels strongly predict atherosclerosis.",
        "unit": "g/L",
    },
    "LDL Direct": {
        "code": "LDL_DIRECT", "canonical_name": "Direct LDL Cholesterol",
        "french_name": "LDL Direct", "category": "Lipid Profile",
        "system": "Cardiovascular", "dashboard_group": "Lipids",
        "description": "Directly measured LDL cholesterol (not calculated by Friedewald); accurate in non-fasting samples.",
        "unit": "g/L",
    },

    # ── Iron Studies (additions) ────────────────────────
    "Transferrine": {
        "code": "TRF", "canonical_name": "Transferrin",
        "french_name": "Transferrine", "category": "Iron Studies",
        "system": "Hematopoietic", "dashboard_group": "Iron",
        "description": "Iron transport protein; elevated in iron deficiency, low in iron overload and chronic disease.",
        "unit": "g/L",
    },

    # ── Liver / Proteins ────────────────────────────────
    "Albumine": {
        "code": "ALB", "canonical_name": "Albumin",
        "french_name": "Albumine", "category": "Liver Function",
        "system": "Digestive", "dashboard_group": "Liver",
        "description": "Major serum protein synthesized by liver; low in cirrhosis, nephrotic syndrome, and malnutrition.",
        "unit": "g/L",
    },
    "Protéines Totales": {
        "code": "TPROT", "canonical_name": "Total Protein",
        "french_name": "Protéines Totales", "category": "Liver Function",
        "system": "Digestive", "dashboard_group": "Liver",
        "description": "Sum of albumin and globulins; abnormal in liver disease, multiple myeloma, and dehydration.",
        "unit": "g/L",
    },

    # ── Inflammation (additions) ────────────────────────
    "Haptoglobine": {
        "code": "HP", "canonical_name": "Haptoglobin",
        "french_name": "Haptoglobine", "category": "Inflammation",
        "system": "Immune", "dashboard_group": "Inflammation",
        "description": "Acute-phase protein that binds free hemoglobin; low in hemolysis, high in inflammation.",
        "unit": "g/L",
    },

    # ── Immunology ──────────────────────────────────────
    "ALSO (Antistreptolysines O)": {
        "code": "ASO", "canonical_name": "Antistreptolysin O",
        "french_name": "ALSO (Antistreptolysines O)", "category": "Immunology",
        "system": "Immune", "dashboard_group": "Immunology",
        "description": "Antibody against streptolysin O; elevated after group A streptococcal infection (rheumatic fever, glomerulonephritis).",
        "unit": "[IU]/mL",
    },
    "ACE": {
        "code": "ACE", "canonical_name": "Angiotensin-Converting Enzyme",
        "french_name": "ACE", "category": "Immunology",
        "system": "Immune", "dashboard_group": "Immunology",
        "description": "Elevated in sarcoidosis and other granulomatous diseases; also used in Gaucher disease monitoring.",
        "unit": "U/L",
    },

    # ── Tumor Markers ───────────────────────────────────
    "CA-125": {
        "code": "CA125", "canonical_name": "Cancer Antigen 125",
        "french_name": "CA-125", "category": "Tumor Markers",
        "system": "Reproductive", "dashboard_group": "Tumor Markers",
        "description": "Ovarian cancer marker; elevated in epithelial ovarian tumors, also in endometriosis and pelvic inflammation.",
        "unit": "U/mL",
    },
    "CA 15-3": {
        "code": "CA153", "canonical_name": "Cancer Antigen 15-3",
        "french_name": "CA 15-3", "category": "Tumor Markers",
        "system": "Reproductive", "dashboard_group": "Tumor Markers",
        "description": "Breast cancer marker; used for monitoring treatment response and recurrence.",
        "unit": "U/mL",
    },
    "CA 19-9": {
        "code": "CA199", "canonical_name": "Cancer Antigen 19-9",
        "french_name": "CA 19-9", "category": "Tumor Markers",
        "system": "Digestive", "dashboard_group": "Tumor Markers",
        "description": "Pancreatic cancer marker; also elevated in cholangiocarcinoma and benign biliary obstruction.",
        "unit": "U/mL",
    },
    "B-HCG": {
        "code": "HCG", "canonical_name": "Beta-Human Chorionic Gonadotropin",
        "french_name": "B-HCG", "category": "Tumor Markers",
        "system": "Reproductive", "dashboard_group": "Tumor Markers",
        "description": "Pregnancy hormone; also a marker for germ cell tumors, trophoblastic disease, and some cancers.",
        "unit": "m[IU]/mL",
    },

    # ── CSF Analysis (LCR) ──────────────────────────────
    "Glucose (LCR)": {
        "code": "GLU_CSF", "canonical_name": "Cerebrospinal Fluid Glucose",
        "french_name": "Glucose (LCR)", "category": "CSF Analysis",
        "system": "Nervous", "dashboard_group": "CSF",
        "description": "CSF glucose; low in bacterial meningitis, normal in viral meningitis (compared to blood glucose).",
        "unit": "g/L",
    },
    "Protéine (LCR)": {
        "code": "PRO_CSF", "canonical_name": "Cerebrospinal Fluid Protein",
        "french_name": "Protéine (LCR)", "category": "CSF Analysis",
        "system": "Nervous", "dashboard_group": "CSF",
        "description": "CSF protein; elevated in meningitis, multiple sclerosis, and Guillain-Barré syndrome.",
        "unit": "g/L",
    },

    # ── Hematology (additions) ──────────────────────────
    "Taux de Réticulocytes": {
        "code": "RETIC", "canonical_name": "Reticulocyte Count",
        "french_name": "Taux de Réticulocytes", "category": "Hematology",
        "system": "Hematopoietic", "dashboard_group": "Blood Count",
        "description": "Immature red blood cells; elevated in hemolytic anemia and blood loss, low in bone marrow failure.",
        "unit": "%",
    },

    # ── Urinalysis ──────────────────────────────────────
    "Chimie des Urines": {
        "code": "URINALYSIS", "canonical_name": "Urinalysis (Chemistry)",
        "french_name": "Chimie des Urines", "category": "Urinalysis",
        "system": "Renal", "dashboard_group": "Urinalysis",
        "description": "Complete urine dipstick analysis (pH, protein, glucose, ketones, blood, nitrite, leukocytes, bilirubin, urobilinogen).",
        "unit": "",
    },

    # ── Immunohematology / Blood Bank ───────────────────
    "Groupe Sanguin": {
        "code": "BLOOD_GROUP", "canonical_name": "Blood Group (ABO + Rh)",
        "french_name": "Groupe Sanguin", "category": "Immunohematology",
        "system": "Hematopoietic", "dashboard_group": "Blood Bank",
        "description": "ABO and Rh blood typing result (A/B/AB/O and Rh+/Rh-).",
        "unit": "",
    },
    "Groupe Sanguin Phénotype": {
        "code": "BLOOD_PHENOTYPE", "canonical_name": "Blood Group Phenotype",
        "french_name": "Groupe Sanguin Phénotype", "category": "Immunohematology",
        "system": "Hematopoietic", "dashboard_group": "Blood Bank",
        "description": "Extended red blood cell phenotype (Rh, Kell, Duffy, Kidd systems) for transfusion compatibility.",
        "unit": "",
    },
    "RAI (Recherche d'Agglutinines Irrégulières)": {
        "code": "RAI", "canonical_name": "Antibody Screening / IAT",
        "french_name": "RAI (Recherche d'Agglutinines Irrégulières)", "category": "Immunohematology",
        "system": "Hematopoietic", "dashboard_group": "Blood Bank",
        "description": "Screening for irregular red cell antibodies; essential before transfusion and during pregnancy.",
        "unit": "",
    },
    "Recherche des Hémolysines": {
        "code": "HEMOLYSIN", "canonical_name": "Hemolysin Screening",
        "french_name": "Recherche des Hémolysines", "category": "Immunohematology",
        "system": "Hematopoietic", "dashboard_group": "Blood Bank",
        "description": "Screening for cold or warm hemolysins; positive in autoimmune hemolytic anemia.",
        "unit": "",
    },
    "Test de Coombs Direct": {
        "code": "COOMBS_D", "canonical_name": "Direct Coombs Test (DAT)",
        "french_name": "Test de Coombs Direct", "category": "Immunohematology",
        "system": "Hematopoietic", "dashboard_group": "Blood Bank",
        "description": "Direct antiglobulin test; detects antibodies bound to red cells in autoimmune hemolytic anemia or HDFN.",
        "unit": "",
    },
    "Frottis Sanguin": {
        "code": "BLOOD_SMEAR", "canonical_name": "Peripheral Blood Smear",
        "french_name": "Frottis Sanguin", "category": "Hematology",
        "system": "Hematopoietic", "dashboard_group": "Blood Count",
        "description": "Microscopic examination of blood cells; assesses morphology, detects blasts, parasites, and cellular abnormalities.",
        "unit": "",
    },
}

# ── Reverse index by code ─────────────────────────────

CODE_TO_ENTRY: dict[str, dict] = {}
for name, entry in BIOMARKER_REGISTRY.items():
    code = entry["code"]
    if code not in CODE_TO_ENTRY:
        CODE_TO_ENTRY[code] = {**entry, "variants": []}
    CODE_TO_ENTRY[code]["variants"].append(name)


# ── Normalization ─────────────────────────────────────

def normalize(test_name: str) -> dict:
    """Return canonical biomarker info for a test name.

    Returns dict with keys: code, canonical_name, french_name, name_en, name_fr,
    category, system, dashboard_group, description, unit, confidence.

    Matching strategy: exact → parenthetical strip → prefix match → fuzzy (≥0.7).
    """
    cleaned = test_name.strip().rstrip(":").strip()

    # 1. Exact match
    if cleaned in BIOMARKER_REGISTRY:
        entry = BIOMARKER_REGISTRY[cleaned]
        return _build_result(entry, cleaned, 1.0)

    # 2. Strip parenthetical suffix (e.g. "CRP (Prot C reactive)" → "CRP")
    base = re.sub(r"\s*\(.+?\)\s*$", "", cleaned).strip()
    if base != cleaned and base in BIOMARKER_REGISTRY:
        entry = BIOMARKER_REGISTRY[base]
        return _build_result(entry, cleaned, 0.95)

    # 3. Prefix match
    for known_name, entry in BIOMARKER_REGISTRY.items():
        if cleaned.startswith(known_name) or known_name.startswith(cleaned):
            return _build_result(entry, cleaned, 0.9)

    # 4. Fuzzy match
    best_score = 0.0
    best = None
    for known_name, entry in BIOMARKER_REGISTRY.items():
        score = SequenceMatcher(None, cleaned.lower(), known_name.lower()).ratio()
        if score > best_score:
            best_score = score
            best = entry

    if best and best_score >= 0.7:
        return _build_result(best, cleaned, round(best_score, 2))

    # 5. Unknown
    return {
        "code": "UNKNOWN", "canonical_name": cleaned, "french_name": cleaned,
        "name_en": cleaned, "name_fr": cleaned,
        "category": "", "system": "", "dashboard_group": "",
        "description": "", "unit": "", "confidence": 0.0,
    }


def _build_result(entry: dict, matched_name: str, confidence: float) -> dict:
    """Build return dict from a registry entry, adding backward-compat keys."""
    return {
        "code": entry["code"],
        "canonical_name": entry["canonical_name"],
        "french_name": entry["french_name"],
        "name_en": entry["canonical_name"],
        "name_fr": matched_name,
        "category": entry["category"],
        "system": entry["system"],
        "dashboard_group": entry["dashboard_group"],
        "description": entry["description"],
        "unit": entry["unit"],
        "confidence": confidence,
    }


# ── Attach codes to report JSON ───────────────────────

def attach_codes_to_report(report: dict) -> dict:
    """Mutate a JSON report dict, adding knowledge-layer fields to each test."""
    for t in report.get("tests", []):
        info = normalize(t.get("test_name", ""))
        t["code"] = info["code"]
        t["biomarker"] = info["name_en"]
        t["normalization_confidence"] = info["confidence"]
        t["category"] = info["category"]
        t["dashboard_group"] = info["dashboard_group"] or t.get("section", "")
    return report


# ── Seed data for biomarkers table ────────────────────

def get_seed_rows() -> list[dict]:
    """Return list of rows for populating the biomarkers table."""
    seen: set[str] = set()
    rows = []
    for entry in BIOMARKER_REGISTRY.values():
        code = entry["code"]
        if code in seen:
            continue
        seen.add(code)
        rows.append({
            "code": code,
            "name_fr": entry["french_name"],
            "name_en": entry["canonical_name"],
            "unit": entry["unit"],
            "category": entry["category"],
            "system": entry["system"],
            "dashboard_group": entry["dashboard_group"],
            "description": entry["description"],
        })
    return rows
