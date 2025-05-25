import os
import time
import streamlit as st
from datetime import datetime
from recorder import Recorder
from transcriptor import Transcriptor
from painter import StableDiffusionPainter as Painter
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set page config
st.set_page_config(
    page_title="VoiceDraw",
    page_icon="🎨",
    layout="wide"
)

# Initialize session state
if "audio_file" not in st.session_state:
    st.session_state.audio_file = None
if "transcript" not in st.session_state:
    st.session_state.transcript = None
if "image_path" not in st.session_state:
    st.session_state.image_path = None
if "recorder" not in st.session_state:
    st.session_state.recorder = Recorder()
if "history" not in st.session_state:
    st.session_state.history = []
if 'is_recording' not in st.session_state:
    st.session_state.is_recording = False
if 'recording_start_time' not in st.session_state:
    st.session_state.recording_start_time = None
if 'elapsed_time' not in st.session_state:
    st.session_state.elapsed_time = 0
if 'input_method' not in st.session_state:
    st.session_state.input_method = "upload"  # Default to upload method
if 'stability_api_key' not in st.session_state:
    st.session_state.stability_api_key = os.getenv("STABILITY_API_KEY", "")
if 'recording_time' not in st.session_state:
    st.session_state.recording_time = 5  # Default recording time in seconds

# Create necessary directories
os.makedirs("recordings", exist_ok=True)
os.makedirs("transcripts", exist_ok=True)
os.makedirs("images", exist_ok=True)

# Title and description
st.title("🎨 VoiceDraw")
st.markdown("Sesli mesajınızı görsellere dönüştürün!")

# Function to update the elapsed time
def update_elapsed_time():
    if st.session_state.is_recording and st.session_state.recording_start_time:
        st.session_state.elapsed_time = time.time() - st.session_state.recording_start_time
    return st.session_state.elapsed_time

# Function to start recording
def start_recording():
    if not st.session_state.is_recording:
        st.session_state.is_recording = True
        st.session_state.recording_start_time = time.time()
        st.session_state.elapsed_time = 0

# Function to stop recording
def stop_recording():
    if st.session_state.is_recording:
        st.session_state.is_recording = False
        st.session_state.recording_start_time = None
        st.session_state.elapsed_time = 0

# Function to handle recording completion
def recording_complete(audio_file):
    st.session_state.is_recording = False
    st.session_state.recording_start_time = None
    st.session_state.audio_file = audio_file
    st.session_state.elapsed_time = 0

# Main app interface
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1️⃣ Ses Girişi")
    
    # Radio buttons to select input method
    input_method = st.radio(
        "Giriş yöntemi seçin:",
        ["Ses Dosyası Yükle", "Mikrofon ile Kaydet"],
        horizontal=True,
        index=0 if st.session_state.input_method == "upload" else 1
    )
    
    # Update the input method in session state based on selection
    st.session_state.input_method = "upload" if input_method == "Ses Dosyası Yükle" else "record"
    
    # File upload method
    if st.session_state.input_method == "upload":
        uploaded_file = st.file_uploader("Ses dosyası seç (WAV formatı)", type=["wav"])
        
        if uploaded_file is not None:
            st.session_state.audio_file = st.session_state.recorder.save_uploaded_audio(uploaded_file)
            st.success(f"Ses dosyası başarıyla yüklendi: {os.path.basename(st.session_state.audio_file)}")
    
    # Microphone recording method
    else:
        # Add recording duration slider
        recording_time = st.slider(
            "Kayıt süresi (saniye):", 
            min_value=3, 
            max_value=30, 
            value=st.session_state.recording_time,
            step=1
        )
        
        # Save recording time to session state
        if recording_time != st.session_state.recording_time:
            st.session_state.recording_time = recording_time
        
        # Display recording controls
        if not st.session_state.is_recording:
            if st.button("🎙️ Kayıt Başlat"):
                start_recording()
                
                # Create a progress bar placeholder
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Get the recording duration from session state
                duration = st.session_state.recording_time
                
                # Start the recording in a non-blocking way
                st.session_state.recorder.start_recording()
                
                # Show progress
                for i in range(duration):
                    # Update progress bar
                    progress_bar.progress((i + 1) / duration)
                    status_text.text(f"Kayıt yapılıyor... {i + 1}/{duration} saniye")
                    time.sleep(1)
                
                # Stop recording after the duration
                audio_file = st.session_state.recorder.stop_recording()
                
                # Wait a moment for the file to be saved (the callback in recorder will handle this)
                time.sleep(1.5)
                
                # Find the latest recording
                recordings_dir = "recordings"
                if os.path.exists(recordings_dir):
                    files = [os.path.join(recordings_dir, f) for f in os.listdir(recordings_dir) 
                             if f.startswith("mic_") and f.endswith(".wav")]
                    if files:
                        # Sort by modification time (newest first)
                        latest_file = max(files, key=os.path.getmtime)
                        st.session_state.audio_file = latest_file
                        status_text.text(f"Ses kaydı tamamlandı: {os.path.basename(latest_file)}")
                    else:
                        status_text.text("Kayıt dosyası bulunamadı!")
                
                # Reset recording state
                recording_complete(st.session_state.audio_file)
                st.rerun()
        else:
            # Provide feedback that recording is in progress
            st.write("📊 Kayıt devam ediyor...")
            progress_placeholder = st.empty()
            
            # Show dynamic progress bar
            elapsed = update_elapsed_time()
            progress = min(1.0, elapsed / st.session_state.recording_time)
            progress_placeholder.progress(progress)
            
            # Show time remaining
            time_remaining = max(0, st.session_state.recording_time - elapsed)
            st.write(f"⏱️ Kalan süre: {time_remaining:.1f} saniye")
            
            # Stop button
            if st.button("⏹️ Kayıt Durdur"):
                st.session_state.recorder.stop_recording()
                stop_recording()
                st.rerun()
    
    # Display audio and transcribe button if audio is available
    if st.session_state.audio_file and os.path.exists(st.session_state.audio_file):
        st.audio(st.session_state.audio_file)
        
        if st.button("🔄 Metne Dönüştür"):
            with st.spinner("Ses metne dönüştürülüyor..."):
                try:
                    # Initialize transcriptor
                    transcriptor = Transcriptor()
                    
                    # Transcribe audio to text
                    st.session_state.transcript = transcriptor.transcribe(st.session_state.audio_file, language="en")
                    
                    if st.session_state.transcript:
                        # Save transcript to file
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        transcript_file = f"transcripts/transcript_{timestamp}.txt"
                        transcriptor.save_transcript(st.session_state.transcript, transcript_file)
                    else:
                        st.error("Ses tanıma başarısız oldu. Lütfen farklı bir ses dosyası deneyin.")
                    
                except Exception as e:
                    st.error(f"Transkripsiyon hatası: {str(e)}")
            st.rerun()

    # Display transcript if available
    st.subheader("2️⃣ Konuşma Metni")
    
    if st.session_state.transcript:
        st.success("✅ Ses metne dönüştürüldü!")
        
        # Display the transcript in a text area that can be edited
        edited_transcript = st.text_area("Metni düzenleyebilirsiniz:", st.session_state.transcript, height=150)
        
        # Update transcript if edited
        if edited_transcript != st.session_state.transcript:
            st.session_state.transcript = edited_transcript
        
        # API Key alanı
        api_key = st.text_input(
            "Stability AI API Key (Şu anda API ile görüntü oluşturuyoruz)",
            value=st.session_state.stability_api_key,
            type="password"
        )
        
        if api_key != st.session_state.stability_api_key:
            st.session_state.stability_api_key = api_key
            # API key'i .env yerine os.environ'a kaydedelim
            os.environ["STABILITY_API_KEY"] = api_key
            st.success("API anahtarı güncellendi!")
        
        # Generate image button
        if st.button("🖼️ Görüntü Oluştur"):
            if not st.session_state.stability_api_key:
                st.error("Görüntü oluşturmak için bir Stability AI API anahtarı gerekiyor.")
            else:
                with st.spinner("Görüntü oluşturuluyor (Bu işlem biraz zaman alabilir)..."):
                    try:
                        painter = Painter()
                        # Optimize edilmiş boyut
                        image_path = painter.paint(
                            prompt=edited_transcript, 
                            width=1024, 
                            height=1024, 
                            steps=30
                        )
                        
                        if image_path and os.path.exists(image_path):
                            st.session_state.image_path = image_path
                            
                            # Add to history
                            st.session_state.history.append({
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "transcript": edited_transcript,
                                "image_path": image_path
                            })
                        else:
                            st.error("Görüntü oluşturulamadı. API anahtarınızı kontrol edin.")
                    except Exception as e:
                        st.error(f"Görüntü oluşturma hatası: {str(e)}")
                st.rerun()
    else:
        st.info("Henüz bir ses kaydı transkript edilmedi veya metin girilmedi.")
        # Allow direct text input
        direct_text = st.text_area("İsterseniz doğrudan metin girebilirsiniz:", height=150)
        if direct_text.strip() and st.button("Bu Metinden Görüntü Oluştur"):
            st.session_state.transcript = direct_text
            st.rerun()

with col2:
    # Image display section
    st.subheader("3️⃣ Oluşturulan Görüntü")
    
    if st.session_state.image_path and os.path.exists(st.session_state.image_path):
        st.success("✅ Görüntü başarıyla oluşturuldu!")
        st.image(st.session_state.image_path, caption="Oluşturulan görüntü")
        
        # Download button
        with open(st.session_state.image_path, "rb") as file:
            btn = st.download_button(
                label="📥 Görüntüyü İndir",
                data=file,
                file_name=os.path.basename(st.session_state.image_path),
                mime="image/png"
            )
        
        # New recording button
        if st.button("🔄 Yeni Kayıt"):
            st.session_state.audio_file = None
            st.session_state.transcript = None
            st.session_state.image_path = None
            st.rerun()
    else:
        st.info("Görüntü oluşturmak için önce ses kaydı yükleyin veya metne dönüştürün.")
        
        # API hakkında bilgi
        st.markdown("""
        ### 📝 Stability AI API Kullanımı
        
        Bu uygulama şimdi görüntüleri oluşturmak için Stability AI'nin API'sini kullanıyor.
        Görüntü oluşturmak için bir API anahtarı gerekiyor.
        
        **API anahtarı almak için:**
        1. [Stability AI](https://platform.stability.ai/) sitesine gidin
        2. Bir hesap oluşturun
        3. API anahtarını alın ve sol paneldeki metin kutusuna girin
        
        ![Stability AI](https://storage.googleapis.com/stability-ai-assets/Stable-Diffusion-XL.jpg)
        """)

# Show history in expandable section
with st.expander("📋 Geçmiş Oluşturmalar"):
    if not st.session_state.history:
        st.info("Henüz bir görsel oluşturulmadı.")
    else:
        # Display history in reverse order (newest first)
        for idx, item in enumerate(reversed(st.session_state.history)):
            st.write(f"**{item['timestamp']}**")
            cols = st.columns(2)
            with cols[0]:
                st.write(f"{item['transcript']}")
            with cols[1]:
                st.image(item['image_path'], caption=f"Görsel #{len(st.session_state.history)-idx}")
                
                # Download button for the historical image
                with open(item['image_path'], "rb") as file:
                    st.download_button(
                        label="📥 İndir",
                        data=file,
                        file_name=os.path.basename(item['image_path']),
                        mime="image/png",
                        key=f"download_{idx}"
                    )
            st.markdown("---")

# Footer
st.markdown("---")
st.markdown("🔊 VoiceDraw | Ses, Metin, Görüntü dönüşümü uygulaması")
