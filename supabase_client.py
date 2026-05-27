import os
import time
import streamlit as st
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# =====================================================
# CREATE SUPABASE CLIENT (CACHED - PREVENTS RECONNECT)
# =====================================================


@st.cache_resource
def init_supabase():

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        raise ValueError("Supabase URL or Key missing in .env")

    return create_client(url, key)


# Global client
supabase = init_supabase()


# =====================================================
# SAFE EXECUTION (RETRY + AUTO RECONNECT)
# =====================================================

def safe_execute(query):

    global supabase

    for _ in range(3):

        try:
            return query.execute()

        except Exception as e:

            print("Database retry:", e)

            # reconnect client
            supabase = init_supabase()

            time.sleep(1)

    return None

# =====================================================
# SAVE AI RESPONSE
# =====================================================

def save_case(patient_name, question, ai_response):

    try:

        data = {
            "patient_name": patient_name,
            "question": question,
            "ai_response": ai_response,
            "doctor_status": "pending"
        }

        response = safe_execute(
            supabase.table("doctor_cases").insert(data)
        )

        return response.data if response else None

    except Exception as e:
        print("Save case error:", e)
        return None


# =====================================================
# GET DOCTOR PENDING CASES
# =====================================================

def get_pending_cases():

    try:

        response = safe_execute(
            supabase.table("doctor_cases")
            .select("*")
            .eq("doctor_status", "pending")
            .order("created_at", desc=True)
        )

        return response.data if response else []

    except Exception as e:
        print("Fetch pending cases error:", e)
        return []


# =====================================================
# UPDATE DOCTOR DECISION
# =====================================================

def update_case(case_id, status, medicines):

    try:

        response = safe_execute(
            supabase.table("doctor_cases")
            .update({
                "doctor_status": status,
                "medicines": medicines
            })
            .eq("id", case_id)
        )

        print("UPDATE RESPONSE:", response)

        if response is not None:
            return True

        return False

    except Exception as e:
        print("Update case error:", e)
        return False
# =====================================================
# GET PATIENT CASES
# =====================================================

def get_patient_cases(patient_name):

    try:

        response = safe_execute(
            supabase.table("doctor_cases")
            .select("*")
            .eq("patient_name", patient_name)
            .order("created_at", desc=True)
        )

        return response.data if response else []

    except Exception as e:
        print("Fetch patient cases error:", e)
        return []


# =====================================================
# ADMIN FUNCTIONS
# =====================================================

def get_doctor_requests():

    try:

        response = safe_execute(
            supabase.table("users")
            .select("*")
            .eq("role", "pending_doctor")
        )

        return response.data if response else []

    except Exception as e:
        print("Fetch doctor requests error:", e)
        return []


# =====================================================
# APPROVE DOCTOR
# =====================================================

def approve_doctor(user_id):

    try:

        response = safe_execute(
            supabase.table("users")
            .update({"role": "doctor"})
            .eq("id", str(user_id))
        )

        return response.data if response else None

    except Exception as e:
        print("Approve doctor error:", e)
        return None


# =====================================================
# REJECT DOCTOR
# =====================================================

def reject_doctor(user_id):

    try:

        response = safe_execute(
            supabase.table("users")
            .update({"role": "patient"})
            .eq("id", str(user_id))
        )

        return response.data if response else None

    except Exception as e:
        print("Reject doctor error:", e)
        return None