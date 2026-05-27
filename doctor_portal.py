import streamlit as st
from supabase_client import get_pending_cases, update_case, supabase

# Prevent session loss
if "role" not in st.session_state:
    st.session_state.role = "doctor"


def show_doctor_portal():

    # =====================================================
    # HEADER
    # =====================================================

    col1, col2 = st.columns([8,1])

    with col1:
        st.title("🩺 Doctor Dashboard")

    with col2:
        if st.button("🚪 Logout", key="doctor_logout"):

            for key in list(st.session_state.keys()):
                del st.session_state[key]

            st.session_state.page = "login"
            st.rerun()

    # =====================================================
    # SESSION SAFETY
    # =====================================================

    if "role" not in st.session_state:
        st.error("Session expired. Please login again.")
        st.stop()

    if st.session_state.role != "doctor":
        st.error("Unauthorized access")
        st.stop()

    # =====================================================
    # PENDING CASES
    # =====================================================

    st.subheader("Pending AI Cases")

    cases = get_pending_cases()

    if not cases:
        st.success("No pending AI cases")

    else:

        for case in cases:

            st.subheader(f"Patient: {case['patient_name']}")

            st.write("Patient Question:")
            st.write(case["question"])

            st.write("AI Diagnosis:")
            st.info(case["ai_response"])

            medicines = st.text_area(
                "Suggested Medicines",
                key=f"med_{case['id']}"
            )

            col1, col2 = st.columns(2)

            # APPROVE
            if col1.button("Approve", key=f"a{case['id']}"):

                if medicines.strip() == "":
                    st.warning("Please enter medicines before approving")

                else:
                    result = update_case(case["id"], "approved", medicines)

                    if result:
                        st.success("Approved")
                        st.rerun()
                    else:
                        st.error("Database update failed")

            # REJECT
            if col2.button("Reject", key=f"r{case['id']}"):

                result = update_case(case["id"], "rejected", "")

                if result:
                    st.error("Rejected")
                    st.rerun()
                else:
                    st.error("Database update failed")

            st.divider()

    # =====================================================
    # SAFE REFRESH
    # =====================================================

    if st.session_state.get("refresh"):
        st.session_state.refresh = False
        st.rerun()

    # =====================================================
    # REVIEWED CASES
    # =====================================================

    st.subheader("Reviewed Cases")

    try:

        from supabase_client import safe_execute

        reviewed = safe_execute(
            supabase.table("doctor_cases")
            .select("*")
            .in_("doctor_status", ["approved", "rejected"])
            .order("created_at", desc=True)
        )

        reviewed_cases = reviewed.data if reviewed else []

    except Exception as e:

        st.error(f"Database error: {e}")
        reviewed_cases = []

    if reviewed_cases:

        for case in reviewed_cases:

            st.write(f"Patient: {case['patient_name']}")

            st.write("Question:")
            st.write(case["question"])

            st.write("AI Diagnosis:")
            st.info(case["ai_response"])

            status = case.get("doctor_status", "pending")

            if status == "approved":
                st.success("Approved")

            elif status == "rejected":
                st.error("Rejected")

            if case.get("medicines"):
                st.write("Medicines:")
                st.write(case["medicines"])

            st.divider()

    else:
        st.info("No reviewed cases yet")