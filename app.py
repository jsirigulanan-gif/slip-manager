import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import json
import io
import time
import altair as alt

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Slip Manager AI", page_icon="💸", layout="wide")

# Custom CSS for Infographic feel
st.markdown("""
<style>
    .main-header {font-size: 2.5rem; color: #4CAF50; text-align: center; font-weight: bold; margin-bottom: 10px;}
    .sub-header {font-size: 1.2rem; color: #666; text-align: center; margin-bottom: 30px;}
    .card {padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px;}
    .card-green {background-color: #e8f5e9; border-left: 5px solid #4caf50;}
    .card-yellow {background-color: #fff3e0; border-left: 5px solid #ff9800;}
    .card-red {background-color: #ffebee; border-left: 5px solid #f44336;}
    .big-number {font-size: 2rem; font-weight: bold; color: #333;}
</style>
""", unsafe_allow_html=True)

# --- 2. SIDEBAR & SETUP ---
with st.sidebar:
    st.header("⚙️ ตั้งค่าระบบ")
    
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
        st.success("✅ ระบบพร้อมใช้งาน")
    else:
        api_key = st.text_input("ใส่ Gemini API Key ของคุณ", type="password")
        st.warning("⚠️ ยังไม่ได้ฝัง API Key ใน Secrets")
    
    st.markdown("---")
    st.write("### 🔒 Privacy Mode")
    st.caption("ประมวลผลบน RAM และลบทิ้งทันที ไม่มีการเก็บข้อมูลลง Server")

# --- 3. MAIN APP ---
st.markdown('<div class="main-header">💸 AI Slip Manager & Analyst</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">เปลี่ยนกองสลิป เป็นข้อมูลการเงินระดับ Infographic (ฟรี!)</div>', unsafe_allow_html=True)

# File Uploader
uploaded_files = st.file_uploader("📂 ลากรูปสลิปทั้งหมดมาวางที่นี่ (รองรับทีละ 50+ รูป)", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)

if uploaded_files and api_key:
    genai.configure(api_key=api_key)
    
    if st.button(f"🚀 เริ่มวิเคราะห์ ({len(uploaded_files)} รูป)"):
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        results = []
        
        # ใช้โมเดล 2.0 Flash ที่คุณมีสิทธิ์ใช้
        model = genai.GenerativeModel('models/gemini-2.0-flash')
        
        for i, uploaded_file in enumerate(uploaded_files):
            try:
                image = Image.open(uploaded_file)
                status_text.text(f"กำลังสแกนใบที่ {i+1}/{len(uploaded_files)}...")
                
                # Prompt: สั่งให้แยกประเภทให้ละเอียดขึ้น
                prompt = """
                Analyze this Thai Bank Slip. Return JSON only:
                {
                    "date": "DD/MM/YYYY",
                    "time": "HH:MM",
                    "amount": float,
                    "receiver": "name",
                    "category": "Guess category (e.g., อาหาร, ช้อปปิ้ง, เดินทาง, บิล, โอนให้คนอื่น, อื่นๆ)"
                }
                If not a slip, return {"status": "error"}.
                """
                
                response = model.generate_content([prompt, image])
                text = response.text.replace('```json', '').replace('```', '').strip()
                data = json.loads(text)
                
                if data.get("status") != "error":
                    data['filename'] = uploaded_file.name
                    results.append(data)
                
            except Exception:
                pass # ข้ามไฟล์ที่ error
            
            progress_bar.progress((i + 1) / len(uploaded_files))
            
        status_text.empty()
        
        # --- 4. DISPLAY DASHBOARD ---
        if results:
            df = pd.DataFrame(results)
            
            # เตรียมข้อมูล
            total_amount = df['amount'].sum()
            category_group = df.groupby('category')['amount'].sum().reset_index()
            
            # --- ส่วนที่ 1: KPI Cards ---
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f'<div class="card card-green"><div class="sub-header">💰 ยอดรวมทั้งหมด</div><div class="big-number">{total_amount:,.0f} บาท</div></div>', unsafe_allow_html=True)
            with c2:
                top_cat = category_group.sort_values('amount', ascending=False).iloc[0]
                st.markdown(f'<div class="card card-red"><div class="sub-header">💸 จ่ายหนักสุดที่</div><div class="big-number">{top_cat["category"]}</div><div style="text-align:center">{top_cat["amount"]:,.0f} บาท</div></div>', unsafe_allow_html=True)
            with c3:
                st.markdown(f'<div class="card card-yellow"><div class="sub-header">🧾 จำนวนสลิป</div><div class="big-number">{len(df)} ใบ</div></div>', unsafe_allow_html=True)

            st.divider()

            # --- ส่วนที่ 2: Infographic Chart & AI Analysis ---
            col_chart, col_ai = st.columns([1, 1])
            
            with col_chart:
                st.subheader("📊 วงเงินของคุณหายไปไหน?")
                # สร้าง Donut Chart ด้วย Altair
                chart = alt.Chart(category_group).mark_arc(innerRadius=60).encode(
                    theta=alt.Theta(field="amount", type="quantitative"),
                    color=alt.Color(field="category", type="nominal", title="หมวดหมู่"),
                    tooltip=['category', 'amount']
                ).properties(height=350)
                st.altair_chart(chart, use_container_width=True)

            with col_ai:
                st.subheader("🤖 AI Financial Coach")
                with st.spinner("AI กำลังวิเคราะห์พฤติกรรมการใช้เงิน..."):
                    # Prompt พิเศษสำหรับขอคำแนะนำ
                    analysis_prompt = f"""
                    ข้อมูลการใช้จ่าย: {category_group.to_string()}
                    ยอดรวม: {total_amount}
                    
                    ขอ Output 2 ส่วน (ภาษาไทย):
                    1. [คำเตือน]: เตือนเรื่องหมวดหมู่ที่ใช้เงินเยอะผิดปกติ แบบจริงจัง
                    2. [คำแนะนำ]: แนะนำวิธีลดค่าใช้จ่ายในหมวดนั้นๆ แบบทำได้จริง
                    
                    ตอบสั้นๆ กระชับ แยกหัวข้อชัดเจน
                    """
                    advice_res = model.generate_content(analysis_prompt)
                    
                    # แสดงผลแบบกล่องข้อความสวยๆ
                    st.info(f"💡 **คำแนะนำ (Advice):**\n\n{advice_res.text}")
                    st.warning("⚠️ **ข้อควรระวัง:** ระวังหมวดหมู่ที่กราฟกินพื้นที่เยอะที่สุด!")

            st.divider()
            
            # --- ส่วนที่ 3: ตารางละเอียด ---
            with st.expander("ดูรายการสลิปทั้งหมด (ตาราง Excel)"):
                st.dataframe(df)

            # ปุ่มโหลด Excel
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
            
            st.download_button("📥 ดาวน์โหลด Excel ไปทำบัญชีต่อ", buffer.getvalue(), "myslips.xlsx")

elif not api_key:
    st.info("👈 กรุณาใส่ API Key ด้านซ้ายมือเพื่อเริ่มใช้งาน")
