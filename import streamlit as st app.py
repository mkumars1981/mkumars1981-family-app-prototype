import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import re
from datetime import date
from PIL import Image

# --- CONFIGURATION ---
st.set_page_config(page_title="Family Manager AI", page_icon="👨‍👩‍👧‍👦")

# Session state for tasks
if "tasks" not in st.session_state:
    st.session_state.tasks = [
        {"child": "Rohan", "subject": "Science", "task": "Solar System Project", "due_date": "2025-12-12", "priority": "High"},
        {"child": "Priya", "subject": "Math", "task": "Chapter 4 Revisions", "due_date": "2025-12-14", "priority": "Medium"},
        {"child": "General", "subject": "School Fees", "task": "Pay Q3 Fees", "due_date": "2025-12-20", "priority": "High"},
    ]

# --- SIDEBAR ---
api_key = st.sidebar.text_input("Enter Google Gemini API Key", type="password")

# --- UTILS ---
def extract_json(text: str):
    """Try to extract a JSON object from model text."""
    if not text:
        raise ValueError("Model returned empty text")

    # Remove common fences
    cleaned = text.replace("```json", "").replace("```", "").strip()

    # Try direct JSON first
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # Fallback: find first {...} block heuristically
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = cleaned[start:end+1]
        try:
            return json.loads(candidate)
        except Exception:
            pass

    # Fallback: regex for a minimal JSON object
    match = re.search(r"\{[\s\S]*\}", cleaned)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass

    raise ValueError("Could not parse JSON from model output")

# --- BACKEND LOGIC (The AI Brain) ---
def analyze_content(content_type, content_data):
    if not api_key:
        return None, "Please enter an API Key first."

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
    except Exception as e:
        return None, f"Gemini configuration error: {e}"

    current_date = date.today().strftime("%Y-%m-%d")
    prompt = f"""
    You are an AI assistant for a parent. Today is {current_date}.
    Analyze the following {content_type} and extract details into valid JSON:
    {{
        "child": "Name or 'General'",
        "subject": "Subject/Activity",
        "task": "Summary of task",
        "due_date": "YYYY-MM-DD",
        "priority": "High/Medium/Low"
    }}
    Only return the JSON. No explanations.
    """

    try:
        if content_type == "Image":
            # content_data is a PIL Image
            response = model.generate_content([prompt, content_data])
        else:
            # Text/Email
            response = model.generate_content([prompt, content_data])

        # Handle safety or empty responses
        text_out = getattr(response, "text", None) or ""
        if not text_out:
            return None, "Model returned no text. Try again or simplify the input."

        extracted = extract_json(text_out)
        return extracted, None

    except Exception as e:
        return None, str(e)

# --- FRONTEND UI (The App) ---
st.title("👨‍👩‍👧‍👦 Family Central Tracker")
st.markdown("### Powered by Gemini AI")

tab1, tab2 = st.tabs(["📅 Dashboard", "➕ Add New Task"])

# --- TAB 1: DASHBOARD ---
with tab1:
    st.header("Upcoming Deadlines")

    df = pd.DataFrame(st.session_state.tasks)

    def color_priority(val):
        return "background-color: #ffcccb" if val == "High" else ""

    st.dataframe(df.style.applymap(color_priority, subset=["priority"]), use_container_width=True)

# --- TAB 2: INPUTS ---
with tab2:
    st.header("Process School Updates")
    input_method = st.radio("Choose Input Type:", ["📸 Upload Circular (Photo)", "📧 Paste Email Text"])

    extracted_data = None
    error = None

    if input_method == "📸 Upload Circular (Photo)":
        uploaded_file = st.file_uploader("Upload a photo of the circular", type=["jpg", "jpeg", "png"])
        if uploaded_file and st.button("Analyze Image"):
            img = Image.open(uploaded_file)
            with st.spinner("Gemini is reading the image..."):
                extracted_data, error = analyze_content("Image", img)

    else:
        email_text = st.text_area("Paste the forwarded email content here")
        if email_text and st.button("Analyze Email"):
            with st.spinner("Parsing email details..."):
                extracted_data, error = analyze_content("Email Text", email_text)

    if error:
        st.error(error)

    if extracted_data:
        st.success("Analysis complete")
        st.subheader("Extracted Task")

        col1, col2 = st.columns(2)
        with col1:
            st.info(f"Child: {extracted_data.get('child')}")
            st.info(f"Subject: {extracted_data.get('subject')}")
        with col2:
            st.warning(f"Due Date: {extracted_data.get('due_date')}")
            st.error(f"Priority: {extracted_data.get('priority')}")

        st.caption(f"Task Summary: {extracted_data.get('task')}")

        if st.button("Save to Dashboard"):
            # Validate minimal fields
            record = {
                "child": extracted_data.get("child") or "General",
                "subject": extracted_data.get("subject") or "Misc",
                "task": extracted_data.get("task") or "Task",
                "due_date": extracted_data.get("due_date") or "",
                "priority": extracted_data.get("priority") or "Low",
            }
            st.session_state.tasks.append(record)
            st.toast("Task saved to dashboard")
