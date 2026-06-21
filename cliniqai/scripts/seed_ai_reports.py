import os
import sys
import json
import logging
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

from google import genai
from google.genai import types

# Load env vars from the parent directory
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
load_dotenv(env_path)
# Fallback to local .env if run from cliniqai
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

MONGODB_URI = os.getenv("MONGODB_URI")
if not MONGODB_URI:
    logger.error("MONGODB_URI is not set in .env")
    sys.exit(1)

client = MongoClient(MONGODB_URI)
db = client["cliniqai"]
patients_collection = db["patients"]

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    logger.error("GOOGLE_API_KEY is not set in .env")
    sys.exit(1)

genai_client = genai.Client(api_key=GOOGLE_API_KEY)

MODEL_NAME = "gemini-3.5-flash"

def generate_report(patient_data, report_type):
    prompt = f"""
You are an expert AI medical system generating a highly realistic, hospital-grade {report_type} for a patient.
Patient details:
Name: {patient_data.get('name', 'Unknown')}
Age: {patient_data.get('age', 'Unknown')}
Gender: {patient_data.get('gender', 'Unknown')}
Conditions: {', '.join(patient_data.get('conditions', []))}

Generate a JSON object representing the medical report. It must contain EXACTLY these keys:
1. "report_id": A random string like "REP-12345"
2. "date": A date in YYYY-MM-DD format (recent)
3. "type": "{report_type.replace(' ', '_').lower()}"
4. "name": "{report_type}"
5. "doctor": A realistic doctor name
6. "hospital": A realistic clinic or hospital name
7. "hosp_id": "HSP_DEMO_001"
8. "notes": A brief 1-2 sentence summary of the findings.
9. "file_url": "/ui/assets/report_1.png" (Use this exact string for demo)
10. "details": A highly detailed, realistic string containing the full medical reading. 

Return ONLY valid JSON. No markdown formatting around the JSON block.
"""
    try:
        response = genai_client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        return json.loads(response.text)
    except Exception as e:
        logger.error(f"Error generating {report_type}: {e}")
        return None

def seed_fallback_patients_if_empty():
    if patients_collection.count_documents({}) == 0:
        logger.info("MongoDB is empty. Seeding initial patient records...")
        fallback_patients = [
            {
                "patient_id": "demo-priya-sharma",
                "phone": "9876543210",
                "name": "Priya Sharma",
                "age": 34,
                "gender": "Female",
                "known_allergies": ["penicillin"],
                "conditions": ["Cough", "Hypertension", "Joint Pain"],
                "visits": [
                    {
                        "visit_id": "v-priya-1",
                        "date": "2026-03-05",
                        "doctor": "Dr. Patel (Nashik Clinic)",
                        "diagnosis": ["Severe Cough"],
                        "file_url": "/ui/assets/prescription_1.png",
                        "medicines": [{"name": "Amoxicillin", "dose": "500mg"}]
                    },
                    {
                        "visit_id": "v-priya-2",
                        "date": "2026-03-10",
                        "doctor": "City Hospital, Nashik",
                        "diagnosis": ["Hypertension"],
                        "file_url": "/ui/assets/prescription_2.png",
                        "medicines": [{"name": "Amlodipine", "dose": "5mg"}]
                    },
                    {
                        "visit_id": "v-priya-3",
                        "date": "2026-03-15",
                        "doctor": "Dr. Gupta's Clinic, Nashik",
                        "diagnosis": ["Osteoarthritis"],
                        "file_url": "/ui/assets/prescription_3.png",
                        "medicines": [{"name": "Ibuprofen", "dose": "400mg"}]
                    }
                ],
                "reports": [
                    {
                        "report_id": "rpt-priya-1",
                        "type": "blood_test",
                        "name": "Complete Blood Count (CBC)",
                        "date": "2026-03-06",
                        "doctor": "Dr. Patel",
                        "hospital": "Nashik Clinic",
                        "hosp_id": "HSP_NASHIK_001",
                        "notes": "Post-treatment follow-up. WBC slightly elevated.",
                        "file_url": "/ui/assets/report_1.png",
                        "file_type": "image/jpeg",
                        "created_at": "2026-03-06T12:00:00Z"
                    },
                    {
                        "report_id": "rpt-priya-2",
                        "type": "x_ray",
                        "name": "Chest X-Ray (PA View)",
                        "date": "2026-03-05",
                        "doctor": "Dr. Patel",
                        "hospital": "Nashik Clinic",
                        "hosp_id": "HSP_NASHIK_001",
                        "notes": "Mild bronchial thickening noted. No consolidation.",
                        "file_url": "/ui/assets/report_2.png",
                        "file_type": "image/jpeg",
                        "created_at": "2026-03-05T14:00:00Z"
                    },
                    {
                        "report_id": "rpt-priya-3",
                        "type": "complete_health_report",
                        "name": "Annual Health Checkup 2026",
                        "date": "2026-03-01",
                        "doctor": "Dr. Gupta",
                        "hospital": "Gupta Clinic",
                        "hosp_id": "HSP_NASHIK_002",
                        "notes": "General health is good. Blood pressure is slightly elevated. Needs follow-up.",
                        "file_url": "/ui/assets/report_3.png",
                        "file_type": "image/jpeg",
                        "created_at": "2026-03-01T10:00:00Z"
                    }
                ]
            },
            {
                "patient_id": "demo-rahul-verma",
                "phone": "9988776655",
                "name": "Rahul Verma",
                "age": 45,
                "gender": "Male",
                "known_allergies": ["sulfa drugs"],
                "conditions": ["Diabetes Type 2", "Hyperlipidemia"],
                "visits": [],
                "reports": []
            }
        ]
        patients_collection.insert_many(fallback_patients)
        logger.info("Inserted mock patients.")

def seed_database():
    seed_fallback_patients_if_empty()
    
    patients = list(patients_collection.find({}))
    report_types = ["Complete Blood Count (CBC)", "Chest X-Ray", "MRI Brain", "Urine Routine"]

    for patient in patients:
        # Skip Priya Sharma as she has pre-seeded rich UI demo reports
        if patient.get("patient_id") == "demo-priya-sharma":
            continue
            
        logger.info(f"Generating reports for {patient.get('name')} (Phone: {patient.get('phone')})...")
        new_reports = []
        for r_type in report_types:
            report_data = generate_report(patient, r_type)
            if report_data:
                new_reports.append(report_data)
        
        if new_reports:
            patients_collection.update_one(
                {"_id": patient["_id"]},
                {"$set": {"reports": new_reports}}
            )
            logger.info(f"Successfully seeded {len(new_reports)} reports for {patient.get('name')}.")

if __name__ == "__main__":
    seed_database()
