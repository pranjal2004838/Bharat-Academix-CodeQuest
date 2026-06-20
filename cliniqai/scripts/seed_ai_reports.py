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

Generate a JSON object representing the medical report. It must contain:
1. "report_id": A random string like "REP-12345"
2. "date": A date in YYYY-MM-DD format (recent)
3. "type": "{report_type}"
4. "doctor": A realistic doctor or lab technician name
5. "summary": A brief 1-2 sentence summary of the findings.
6. "details": A highly detailed, realistic string containing the full medical reading. 
   - For Blood/Urine: include realistic values, reference ranges, and units in a tabular/structured text format.
   - For X-Ray/MRI: include Clinical Indication, Findings, and Impression. Use medical jargon.

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
                "visits": []
            },
            {
                "patient_id": "demo-rahul-verma",
                "phone": "9988776655",
                "name": "Rahul Verma",
                "age": 45,
                "gender": "Male",
                "known_allergies": ["sulfa drugs"],
                "conditions": ["Diabetes Type 2", "Hyperlipidemia"],
                "visits": []
            }
        ]
        patients_collection.insert_many(fallback_patients)
        logger.info("Inserted mock patients.")

def seed_database():
    seed_fallback_patients_if_empty()
    
    patients = list(patients_collection.find({}))
    report_types = ["Complete Blood Count (CBC)", "Chest X-Ray", "MRI Brain", "Urine Routine"]

    for patient in patients:
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
