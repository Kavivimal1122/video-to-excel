import streamlit as st
import cv2
import pytesseract
import pandas as pd
import re
import tempfile
import os

# --- 91 CLUB LOGIC FUNCTIONS ---
def get_color(num):
    if num in [1, 3, 7, 9]: return "Green"
    if num in [2, 4, 6, 8]: return "Red"
    if num in [0, 5]: return "Violet"
    return "Unknown"

def get_size(num):
    return "Big" if num >= 5 else "Small"

# --- STREAMLIT UI ---
st.set_page_config(page_title="91 Club Results Extractor", layout="wide")
st.title("📊 91 Club Video to Excel Converter")
st.markdown("### Upload your screen recording to extract Period, Result, Color, and Size.")

uploaded_file = st.file_uploader("Upload Game History Video (MP4)", type=['mp4', 'mov'])

if uploaded_file:
    tfile = tempfile.NamedTemporaryFile(delete=False)
    tfile.write(uploaded_file.read())
    
    if st.button("🚀 Start Deep Scan (x4 Slow-Read)"):
        cap = cv2.VideoCapture(tfile.name)
        raw_data = []
        
        progress_bar = st.progress(0)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # SLOW-READ LOGIC: We read every 2nd frame to ensure fast page flips are caught
        frame_step = 2 
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break
            
            curr = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
            if curr % frame_step == 0:
                progress_bar.progress(min(curr / total_frames, 1.0))
                
                # 1. CROP: Focus on the middle 60% of the screen to avoid UI noise
                h, w, _ = frame.shape
                cropped = frame[int(h*0.2):int(h*0.8), int(w*0.1):int(w*0.9)]
                
                # 2. PRE-PROCESS: Grayscale + Threshold for sharp text
                gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
                _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
                
                # 3. OCR: Extract digits
                text = pytesseract.image_to_string(thresh, config='--psm 6 digits')
                
                # Find 13-digit Periods and 1-digit Results
                periods = re.findall(r'\d{12,15}', text)
                results = re.findall(r'\b\d{1}\b', text)
                
                for i in range(min(len(periods), len(results))):
                    r_val = int(results[i])
                    raw_data.append({
                        "Period Number": int(periods[i]),
                        "Result Number": r_val,
                        "Result Color": get_color(r_val),
                        "Size": get_size(r_val)
                    })

        cap.release()
        
        if raw_data:
            df = pd.DataFrame(raw_data)
            # CLEANING: Remove duplicates and sort by Period Number
            df = df.drop_duplicates(subset=['Period Number']).sort_values(by='Period Number')
            
            st.success(f"✅ Extracted {len(df)} Unique Results!")
            st.dataframe(df)
            
            # EXCEL EXPORT
            output = "91_Club_Data.xlsx"
            df.to_excel(output, index=False)
            with open(output, "rb") as f:
                st.download_button("📥 Download Final Excel Sheet", f, file_name=output)
        else:
            st.error("No results found. Try a clearer video recording.")
