import os
import json
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=API_KEY) if API_KEY else None


# ---------------- SAFE GROQ CALL ----------------
def safe_groq_call(messages, temperature=0):
    if not client:
        return None
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            temperature=temperature
        )
        return response.choices[0].message.content.strip()
    except:
        return None


# ---------------- EXTRACT LAB VALUES ----------------
def extract_lab_values(report_text):

    if not report_text or report_text.strip() == "":
        return {}

    if not client:
        return {}

    prompt = f"""
Extract medical details from this report.
Return ONLY valid JSON.

Fields:
Name, Age, Gender,
Hemoglobin,
White Blood Cells,
Platelets,
Blood Sugar Fasting,
Blood Sugar PP,
TSH,
Total Cholesterol

If not found return null.

Report:
{report_text}
"""

    raw_output = safe_groq_call(
        [{"role": "user", "content": prompt}],
        temperature=0
    )

    if not raw_output:
        return {}

    try:
        parsed = json.loads(raw_output)

        # If all values are null → treat as empty
        if isinstance(parsed, dict) and all(v is None for v in parsed.values()):
            return {}

        return parsed

    except:
        match = re.search(r"\{.*\}", raw_output, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group())
                if all(v is None for v in parsed.values()):
                    return {}
                return parsed
            except:
                return {}
        return {}


# ---------------- NORMAL RANGES ----------------
normal_ranges = {
    "Hemoglobin": (13, 17),
    "White Blood Cells": (4000, 11000),
    "Platelets": (150000, 400000),
    "Blood Sugar Fasting": (70, 99),
    "Blood Sugar PP": (70, 140),
    "TSH": (0.4, 5),
    "Total Cholesterol": (0, 200)
}


def extract_number(value):
    try:
        match = re.search(r"[-+]?\d*\.?\d+", str(value))
        return float(match.group()) if match else None
    except:
        return None


# ---------------- FLAG ABNORMAL ----------------
def flag_abnormal(labs):

    if not labs:
        return {}

    flagged = {}

    for test, value in labs.items():

        if test not in normal_ranges:
            continue

        num = extract_number(value)
        if num is None:
            continue

        low, high = normal_ranges[test]

        if num < low:
            status = "Low"
        elif num > high:
            status = "High"
        else:
            status = "Normal"

        flagged[test] = {
            "value": value,
            "normal_range": f"{low} - {high}",
            "status": status
        }

    return flagged


# ---------------- SUMMARY GENERATOR ----------------
def generate_structured_summary(labs, risk, flagged):

    if not client:
        return "⚠ AI unavailable. Check GROQ_API_KEY."

    prompt = f"""
You are MediChat Clinical AI.

Patient:
Name: {labs.get("Name", "Not mentioned")}
Age: {labs.get("Age", "Not mentioned")}
Gender: {labs.get("Gender", "Not mentioned")}

Flagged:
{flagged}

Risk Level: {risk}

Provide:
- Interpretation
- Medicines table (INR cost)
- Foods to eat
- Foods to avoid
- Exercise
- Final summary
- Disclaimer
"""

    response = safe_groq_call(
        [{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return response if response else "⚠ Could not generate summary."