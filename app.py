import streamlit as st
import cv2
import pytesseract
import pandas as pd
import re
import os
import tempfile

# Helper functions for 91 Club logic
def get_color(num):
    if num in [1, 3, 7, 9]: return "Green"
    if num in [2, 4, 6, 8]: return "Red"
    if num in [0, 5]: return "Violet"
    return "Unknown"

def get_size(num):
    return "Big" if num >= 5 else "Small"

st.title("🎰 91 Club Video to Excel Converter")
st.write("Upload your fast-recording video to extract 500+ results.")

uploaded_file = st.file_uploader("Upload Video (MP4)", type=['mp4', 'mov', 'avi'])

if uploaded_file is not None:
    # Save uploaded video to a temporary file
    tfile = tempfile.NamedTemporaryFile(delete=False)
    tfile.write(uploaded_file.read())
    
    if st.button("Start Extraction"):
        cap = cv2.VideoCapture(tfile.name)
        raw_data = []
        
        progress_bar = st.progress(0)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # We process every 2nd frame to ensure we don't miss fast page flips
        frame_step = 2 
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
            
            if current_frame % frame_step == 0:
                # Update progress
                progress_bar.progress(current_frame / total_frames)
                
                # Image Preprocessing for OCR
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                # Zooming in or cropping the frame here would improve accuracy
                
                text = pytesseract.image_to_string(gray, config='--psm 6 digits')
                
                # Regex to find Period (13+ digits) and Result (1 digit)
                periods = re.findall(r'\d{12,15}', text)
                results = re.findall(r'\b\d{1}\b', text)
                
                for i in range(min(len(periods), len(results))):
                    p_val = int(periods[i])
                    r_val = int(results[i])
                    raw_data.append({
                        "Period Number": p_val,
                        "Result Number": r_val,
                        "Result Color": get_color(r_val),
                        "Size": get_size(r_val)
                    })

        cap.release()
        
        # --- Data Cleaning ---
        if raw_data:
            df = pd.DataFrame(raw_data)
            # 1. Remove Duplicates
            df = df.drop_duplicates(subset=['Period Number'])
            # 2. Sort Ascending (Oldest to Newest)
            df = df.sort_values(by='Period Number', ascending=True)
            
            st.success(f"Extraction Complete! Found {len(df)} unique results.")
            st.dataframe(df.head(20)) # Show preview
            
            # 3. Convert to Excel for Download
            output_path = "91_Club_Results.xlsx"
            df.to_excel(output_path, index=False)
            
            with open(output_path, "rb") as file:
                st.download_button(
                    label="📥 Download Excel Sheet",
                    data=file,
                    file_name="91_Club_Results.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.error("No data found. Ensure the video is clear and the history table is visible.")