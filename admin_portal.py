import streamlit as st
import pandas as pd
import plotly.express as px
from supabase_client import supabase, approve_doctor, reject_doctor, safe_execute


def show_admin_portal():

    st.set_page_config(page_title="Admin Portal", layout="wide")

    # =====================================================
    # SESSION SAFETY CHECK
    # =====================================================

    if "role" not in st.session_state:
        st.error("Session expired. Please login again.")
        st.stop()

    if st.session_state.role != "admin":
        st.error("Unauthorized access")
        st.stop()

    # =====================================================
    # BACKGROUND FIX
    # =====================================================

    st.markdown("""
    <style>
    .stApp {
        background-color: #f8fafc !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # =====================================================
    # HEADER
    # =====================================================

    col1, col2 = st.columns([8,1])

    with col1:
        st.title("🛡 Admin Dashboard")

    with col2:
        if st.button("🚪 Logout", key="admin_logout"):

            st.session_state.clear()
            st.session_state.page = "login"
            st.rerun()

    # =====================================================
    # FETCH USER DATA
    # =====================================================

    try:

        pending_response = safe_execute(
            supabase.table("users").select("*").eq("role","pending_doctor")
        )

        approved_response = safe_execute(
            supabase.table("users").select("*").eq("role","doctor")
        )

        patient_response = safe_execute(
            supabase.table("users").select("*").eq("role","patient")
        )

        pending_users = pending_response.data if pending_response else []
        approved_docs = approved_response.data if approved_response else []
        patient_users = patient_response.data if patient_response else []

    except Exception as e:

        st.error(f"Database error: {e}")
        st.stop()

    # =====================================================
    # FETCH AI CASE DATA
    # =====================================================

    try:

        cases_response = safe_execute(
            supabase.table("doctor_cases").select("*")
        )

        all_cases = cases_response.data if cases_response else []

    except:
        all_cases = []

    # =====================================================
    # DASHBOARD ANALYTICS
    # =====================================================

    st.subheader("Platform Analytics")

    pending_cases = [c for c in all_cases if c.get("doctor_status") == "pending"]
    approved_cases = [c for c in all_cases if c.get("doctor_status") == "approved"]
    rejected_cases = [c for c in all_cases if c.get("doctor_status") == "rejected"]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("⏳ Pending Doctors", len(pending_users))
    c2.metric("🧑‍⚕️ Approved Doctors", len(approved_docs))
    c3.metric("👨‍⚕️ Total Patients", len(patient_users))
    c4.metric("📋 Total AI Cases", len(all_cases))

    c5, c6, c7 = st.columns(3)

    c5.metric("🟡 Pending Cases", len(pending_cases))
    c6.metric("✅ Approved Cases", len(approved_cases))
    c7.metric("❌ Rejected Cases", len(rejected_cases))

    st.divider()

    # =====================================================
    # CASE ANALYTICS CHART
    # =====================================================

    st.subheader("📊 Case Status Analytics")

    if all_cases:

        df_chart = pd.DataFrame(all_cases)

        status_count = df_chart["doctor_status"].value_counts().reset_index()
        status_count.columns = ["Status", "Count"]

        fig = px.pie(
            status_count,
            names="Status",
            values="Count",
            title="AI Case Status Distribution"
        )

        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("No analytics data available")

    st.divider()

    # =====================================================
    # DOCTOR APPROVAL REQUESTS
    # =====================================================

    st.subheader("Doctor Approval Requests")

    if len(pending_users) == 0:
        st.success("No doctor requests")

    else:

        for user in pending_users:

            st.write("### 👨‍⚕️ Doctor Request")

            st.write("**Username:**", user.get("username"))
            st.write("**Email:**", user.get("email"))

            if user.get("doctor_id"):
                st.write("**Doctor ID:**", user.get("doctor_id"))

            if user.get("license_file"):

                st.write("📄 **Doctor License**")

                st.markdown(
                    f"[🔍 Open License Document]({user['license_file']})",
                    unsafe_allow_html=True
                )

                if st.button(
                    "Preview License",
                    key=f"preview_license_{user['id']}"
                ):

                    st.components.v1.iframe(
                        user["license_file"],
                        height=500
                    )

            col1, col2 = st.columns(2)

            with col1:

                if st.button(
                    "✅ Approve",
                    key=f"approve_doctor_{user['id']}"
                ):

                    response = approve_doctor(user["id"])

                    if response:
                        st.success("Doctor approved successfully")
                        st.rerun()
                    else:
                        st.error("Approval failed")

            with col2:

                if st.button(
                    "❌ Reject",
                    key=f"reject_doctor_{user['id']}"
                ):

                    response = reject_doctor(user["id"])

                    if response:
                        st.warning("Doctor rejected")
                        st.rerun()
                    else:
                        st.error("Reject failed")

            st.divider()

    # =====================================================
    # APPROVED DOCTORS
    # =====================================================

    st.subheader("Approved Doctors")

    if approved_docs:

        for doc in approved_docs:

            st.write("👨‍⚕️ **Doctor:**", doc.get("username"))
            st.write("📧 **Email:**", doc.get("email"))

            if doc.get("doctor_id"):
                st.write("🆔 **Doctor ID:**", doc.get("doctor_id"))

            st.divider()

    else:
        st.info("No approved doctors yet")

    # =====================================================
    # FILTER AI CASES
    # =====================================================

    st.subheader("🔎 Filter AI Cases")

    status_filter = st.selectbox(
        "Filter by Status",
        ["All", "pending", "approved", "rejected"]
    )

    filtered_cases = all_cases

    if status_filter != "All":
        filtered_cases = [
            c for c in all_cases
            if c.get("doctor_status") == status_filter
        ]

    search = st.text_input("Search Patient")

    if search:
        filtered_cases = [
            c for c in filtered_cases
            if search.lower() in c.get("patient_name","").lower()
        ]

    # =====================================================
    # AI CASE TABLE VIEW
    # =====================================================

    st.subheader("📋 AI Case Records")

    if filtered_cases:

        df = pd.DataFrame(filtered_cases)

        display_cols = [
            "patient_name",
            "question",
            "doctor_status",
            "created_at"
        ]

        df = df[display_cols]

        df.columns = [
            "Patient",
            "Question",
            "Status",
            "Created At"
        ]

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info("No cases found")