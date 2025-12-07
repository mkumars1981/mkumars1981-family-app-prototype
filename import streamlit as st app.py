import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
from datetime import date

# --- CONFIGURATION ---
st.set_page_config(page_title="Family Manager AI", page_icon="👨‍👩‍👧‍👦")

# Placeholder for API Key (In real app, use st.secrets)
api_key = st.sidebar.text_input("Enter Google Gemini API Key", type="password")

# --- BACKEND LOGIC (The AI Brain) ---
def analyze_content(content_type, content_data):
    if not api_key:
        return None, "Please enter an API Key first."
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
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
    """
    
    try:
        if content_type == "Image":
            response = model.generate_content([prompt, content_data])
        else: # Text/Email
            response = model.generate_content([prompt, content_data])
            
        # Clean up JSON string if model adds markdown
        clean_text = response.text.replace("```json", "").replace("```", "")
        return json.loads(clean_text), None
    except Exception as e:
        return None, str(e)

# --- FRONTEND UI (The App) ---
st.title("👨‍👩‍👧‍👦 Family Central Tracker")
st.markdown("### Powered by Gemini AI")

# TABS for navigation
tab1, tab2 = st.tabs(["📅 Dashboard", "➕ Add New Task"])

# --- TAB 1: DASHBOARD ---
with tab1:
    st.header("Upcoming Deadlines")
    
    # Mock Data to show what the dashboard looks like
    mock_data = [
        {"child": "Rohan", "subject": "Science", "task": "Solar System Project", "due_date": "2025-12-12", "priority": "High"},
        {"child": "Priya", "subject": "Math", "task": "Chapter 4 Revisions", "due_date": "2025-12-14", "priority": "Medium"},
        {"child": "General", "subject": "School Fees", "task": "Pay Q3 Fees", "due_date": "2025-12-20", "priority": "High"},
    ]
    
    # Convert to DataFrame for a nice table
    df = pd.DataFrame(mock_data)
    
    # Color code high priority
    def color_priority(val):
        color = '#ffcccb' if val == 'High' else ''
        return f'background-color: {color}'

    st.dataframe(df.style.applymap(color_priority, subset=['priority']), use_container_width=True)

# --- TAB 2: INPUTS ---
with tab2:
    st.header("Process School Updates")
    input_method = st.radio("Choose Input Type:", ["📸 Upload Circular (Photo/PDF)", "📧 Paste Email Text"])
    
    extracted_data = None
    
    if input_method == "📸 Upload Circular (Photo/PDF)":
        uploaded_file = st.file_uploader("Take a photo of the circular", type=["jpg", "png", "jpeg"])
        if uploaded_file and st.button("Analyze Image"):
            # Setup image for Gemini
            from PIL import Image
            img = Image.open(uploaded_file)
            with st.spinner("Gemini is reading the handwriting..."):
                extracted_data, error = analyze_content("Image", img)

    else:
        email_text = st.text_area("Paste the forwarded email content here")
        if email_text and st.button("Analyze Email"):
            with st.spinner("Parsing email details..."):
                extracted_data, error = analyze_content("Email Text", email_text)

    # Display Results
    if extracted_data:
        st.success("Analysis Complete!")
        st.subheader("✅ Extracted Task")
        
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**Child:** {extracted_data.get('child')}")
            st.info(f"**Subject:** {extracted_data.get('subject')}")
        with col2:
            st.warning(f"**Due Date:** {extracted_data.get('due_date')}")
            st.error(f"**Priority:** {extracted_data.get('priority')}")
            
        st.caption(f"Task Summary: {extracted_data.get('task')}")
        
        if st.button("Save to Dashboard"):

            st.toast("Task saved to database!")

