import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import json
import io
import time

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Slip Manager AI", page_icon="💸", layout="wide")

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {font-size: 2.5rem; color: #4CAF50; text-align: center; font-weight: bold;}
    .sub-header {font-size: 1.2rem; color: #666; text-align: center;}
    .roast-box {background-color: #ffebee; border-left: 5px solid #ff5252; padding: 20px; border-radius: 5px; margin-top: 20px;}
    .stat-box {background-color: #e8f5e9; padding: 15px; border-radius: 10px; text-align: center;}
</style>
""", unsafe_allow_html=True)

# --- 2. SIDEBAR & SETUP ---
with st.sidebar:
    st.header("⚙️ ตั้งค่าระบบ")
    
    # เช็คว่ามี Key ใน Secrets หรือยัง
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
        st.success("✅ ระบบพร้อมใช้งาน (API Key เชื่อมต่อแล้ว)")
    else:
        # ถ้าไม่มีใน Secrets ค่อยให้กรอกเอง (เผื่อเอาไว้เทสต์)
        api_key = st.text_input("ใส่ Gemini API Key ของคุณ", type="password")
        st.warning("⚠️ ยังไม่ได้ฝัง API Key ใน Secrets")
    
    st.markdown("---")
    st.write("### 🔒 Privacy Mode")
    st.caption("ระบบทำงานบน RAM ประมวลผลเสร็จลบข้อมูลทิ้งทันที ไม่มีการบันทึกภาพลง Server")

# --- 3. MAIN APP ---
st.markdown('<div class="main-header">💸 AI Slip Manager</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">โยนสลิปเข้ามารวมกันที่นี่ เดี๋ยวพี่ AI เคลียร์บัญชีให้ (ฟรี!)</div>', unsafe_allow_html=True)
st.write("")

# File Uploader
uploaded_files = st.file_uploader("📂 ลากรูปสลิปมาวางตรงนี้ (รองรับทีละหลายรูป)", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)

if uploaded_files and api_key:
    genai.configure(api_key=api_key)
    
    if st.button(f"🚀 เริ่มประมวลผล ({len(uploaded_files)} รูป)"):
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        results = []
        
        # --- 4. AI PROCESSING LOGIC ---
      model = genai.GenerativeModel('gemini-1.5-flash')
        
        for i, uploaded_file in enumerate(uploaded_files):
            try:
                # Load image
                image = Image.open(uploaded_file)
                status_text.text(f"กำลังอ่านใบที่ {i+1}/{len(uploaded_files)}: {uploaded_file.name}...")
                
                # Prompt Engineering (หัวใจสำคัญ)
                prompt = """
                Analyze this Thai Bank Slip image. Extract data into JSON format with these keys:
                - date: DD/MM/YYYY
                - time: HH:MM
                - amount: number only (float)
                - receiver: name of receiver/shop
                - category: Guess category in Thai (e.g., อาหาร, ช้อปปิ้ง, ค่าเดินทาง, บิลน้ำไฟ, โอนทั่วไป)
                
                If it's NOT a slip, return {"status": "error"}.
                Output ONLY raw JSON string.
                """
                
                response = model.generate_content([prompt, image])
                
                # Cleaning JSON string (AI บางทีชอบแถม markdown)
                json_str = response.text.replace('```json', '').replace('```', '').strip()
                data = json.loads(json_str)
                
                if data.get("status") != "error":
                    data['filename'] = uploaded_file.name
                    results.append(data)
                
            except Exception as e:
                st.error(f"Error reading file {uploaded_file.name}: {e}")
            
            # Update Progress
            progress_bar.progress((i + 1) / len(uploaded_files))
            
        status_text.text("✅ เรียบร้อย! มาดูผลประกอบการกัน")
        
        # --- 5. DISPLAY RESULTS ---
        if results:
            df = pd.DataFrame(results)
            
            # Reorder columns
            cols = ['date', 'time', 'category', 'receiver', 'amount', 'filename']
            # Handle missing cols just in case
            df = df.reindex(columns=cols) 
            
            # Show Metrics
            total_amount = df['amount'].sum()
            col1, col2, col3 = st.columns(3)
            col1.metric("จำนวนสลิป", f"{len(df)} ใบ")
            col2.metric("ยอดรวมทั้งหมด", f"{total_amount:,.2f} บาท")
            col3.metric("หมวดหมู่จ่ายเยอะสุด", df['category'].mode()[0] if not df.empty else "-")
            
            st.divider()
            
            # Data Table
            st.subheader("📋 ตารางรายรับ-รายจ่าย")
            st.dataframe(df, use_container_width=True)
            
            # --- 6. FEATURE: AI FINANCIAL ROAST (ปากแจ๋ว) ---
            st.subheader("🔥 AI ขอวิจารณ์การเงินคุณ (โหมดปากแจ๋ว)")
            with st.spinner("AI กำลังเรียบเรียงคำด่า..."):
                roast_prompt = f"""
                นี่คือรายการใช้จ่ายของฉันในเดือนนี้: {df.to_string()}
                ช่วยวิจารณ์นิสัยการใช้เงินของฉันแบบ "เพื่อนสนิทปากแจ๋ว" (Sarcastic & Funny)
                - เน้นแซะเรื่องที่จ่ายเยอะที่สุด
                - ใช้ภาษาวัยรุ่น ไทย
                - ความยาวไม่เกิน 3 บรรทัด
                """
                roast_res = model.generate_content(roast_prompt)
                st.markdown(f'<div class="roast-box">🤖 <b>AI Says:</b><br>{roast_res.text}</div>', unsafe_allow_html=True)
            
            # --- 7. EXPORT TO EXCEL ---
            st.divider()
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Sheet1')
            
            st.download_button(
                label="📥 ดาวน์โหลดไฟล์ Excel",
                data=buffer.getvalue(),
                file_name="my_slips_summary.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

elif not api_key:
    st.warning("⚠️ กรุณาใส่ API Key ที่เมนูด้านซ้ายก่อนเริ่มใช้งาน")
