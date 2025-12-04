import streamlit as st
import google.generativeai as genai

# Setup
st.title("🤖 Model Checker")

# Check Secrets
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    st.success(f"API Key Found! (Length: {len(api_key)})")
    
    # List Models
    st.write("### 📋 Available Models:")
    try:
        models = genai.list_models()
        found_any = False
        for m in models:
            if 'generateContent' in m.supported_generation_methods:
                st.code(m.name) # จะโชว์ชื่อจริงที่ต้องใช้
                found_any = True
        
        if not found_any:
            st.error("No compatible models found!")
            
    except Exception as e:
        st.error(f"Error listing models: {e}")
else:
    st.error("No API Key found in secrets.")
