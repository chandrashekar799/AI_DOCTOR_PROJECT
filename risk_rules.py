import re

def extract_number(value):
    try:
        match = re.search(r"[-+]?\d*\.?\d+", str(value))
        return float(match.group()) if match else None
    except:
        return None


def calculate_risk(labs):

    if not labs or not isinstance(labs, dict):
        return "Low", None

    score = 0
    anemia_stage = None

    fasting = extract_number(labs.get("Blood Sugar Fasting"))
    if fasting is not None:
        if fasting >= 126:
            score += 3
        elif fasting >= 100:
            score += 1

    hb = extract_number(labs.get("Hemoglobin"))
    if hb is not None:
        if hb < 8:
            anemia_stage = "Severe Anemia"
            score += 3
        elif hb < 10:
            anemia_stage = "Moderate Anemia"
            score += 2
        elif hb < 12:
            anemia_stage = "Mild Anemia"
            score += 1

    if score >= 6:
        risk = "High"
    elif score >= 3:
        risk = "Moderate"
    else:
        risk = "Low"

    return risk, anemia_stage