import os
import wave
import tempfile
import traceback
import numpy as np
import sounddevice as sd
import soundfile as sf
import threading
import time
from datetime import datetime

class Recorder:
    def __init__(self, output_directory="recordings"):
        """
        Initialize the recorder
        
        Args:
            output_directory (str): Directory to save recordings
        """
        self.output_directory = output_directory
        self.channels = 1
        self.sample_rate = 16000
        self.recording = False
        self.audio_data = []
        self.recording_thread = None
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        
        # Check if sounddevice is working
        try:
            devices = sd.query_devices()
            input_devices = [d for d in devices if d['max_input_channels'] > 0]
            if not input_devices:
                print("UYARI: Ses girişi olan cihaz bulunamadı!")
            else:
                print(f"Kullanılabilir ses girişi cihazları: {len(input_devices)}")
        except Exception as e:
            print(f"Ses cihazları kontrol edilirken hata: {e}")
    
    def start_recording(self, callback=None):
        """
        Start recording audio from microphone
        
        Args:
            callback: Optional callback function to call when recording is complete
        
        Returns:
            bool: True if recording started successfully, False otherwise
        """
        if self.recording:
            print("Kayıt zaten devam ediyor...")
            return True
            
        try:
            self.recording = True
            self.audio_data = []
            
            # Start a recording thread
            def record_thread():
                frames = []
                
                def audio_callback(indata, frame_count, time_info, status):
                    if self.recording:
                        frames.append(indata.copy())
                
                with sd.InputStream(
                    samplerate=self.sample_rate,
                    channels=self.channels,
                    callback=audio_callback
                ):
                    while self.recording:
                        sd.sleep(100)  # Sleep for 100ms to reduce CPU usage
                        
                # Save the recording when finished
                if frames:
                    audio_array = np.concatenate(frames, axis=0)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = os.path.join(self.output_directory, f"mic_{timestamp}.wav")
                    sf.write(filename, audio_array, self.sample_rate)
                    print(f"Kayıt şuraya kaydedildi: {filename}")
                    if callback:
                        callback(filename)
                    return filename
                else:
                    print("Kayıt verileri toplanamadı")
                    if callback:
                        callback(None)
                    return None
            
            # Start the recording thread
            self.recording_thread = threading.Thread(target=record_thread)
            self.recording_thread.daemon = True
            self.recording_thread.start()
            
            print("Kayıt başlatıldı...")
            return True
        except Exception as e:
            print(f"Kaydı başlatırken hata: {e}")
            traceback.print_exc()
            self.recording = False
            return False
    
    def record_audio(self, max_duration=5):
        """
        Record audio for a specific duration
        
        Args:
            max_duration (int): Maximum recording duration in seconds
        
        Returns:
            str: Path to the saved audio file
        """
        try:
            print(f"Maksimum {max_duration} saniye kaydediliyor...")
            
            # Create a result container
            result = {"filename": None}
            recording_finished = threading.Event()
            
            def recording_done(filename):
                result["filename"] = filename
                recording_finished.set()
            
            # Start recording
            if not self.start_recording(callback=recording_done):
                return None
                
            # Wait for specified duration then stop
            time.sleep(max_duration)
            self.stop_recording()
            
            # Wait for recording to finish saving (timeout after 2 seconds)
            recording_finished.wait(timeout=2)
            return result["filename"]
            
        except Exception as e:
            print(f"Kayıt sırasında hata: {e}")
            traceback.print_exc()
            self.recording = False
            return None
    
    def stop_recording(self):
        """
        Stop recording and save the audio file
        
        Returns:
            None: The recording thread will handle the file saving
        """
        if not self.recording:
            return None
        
        try:
            # Signal to stop the ongoing recording
            self.recording = False
            print("Kayıt durduruldu.")
            
            # We don't join the thread here to avoid blocking
            # The thread will finish processing and save the file
            return None
        except Exception as e:
            print(f"Kaydı durdururken hata: {e}")
            traceback.print_exc()
            return None
    
    def is_recording(self):
        """
        Check if recording is in progress
        
        Returns:
            bool: True if recording, False otherwise
        """
        return self.recording
    
    def save_uploaded_audio(self, uploaded_file):
        """
        Save an uploaded audio file
        
        Args:
            uploaded_file: Streamlit UploadedFile object
            
        Returns:
            str: Path to the saved audio file
        """
        if uploaded_file is None:
            return None
        
        try:
            # Generate a filename based on timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.output_directory, f"upload_{timestamp}.wav")
            
            # Save the uploaded file
            with open(filename, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            print(f"Yüklenen ses dosyası şuraya kaydedildi: {filename}")
            return filename
        except Exception as e:
            print(f"Yüklenen ses dosyasını kaydederken hata: {e}")
            traceback.print_exc()
            return None

# Example usage
if __name__ == "__main__":
    try:
        recorder = Recorder()
        print("Kayıt başlatılıyor...")
        recorder.start_recording()
        print("5 saniye kayıt yapılıyor...")
        time.sleep(5)
        recorder.stop_recording()
        # Bekleyin ki kayıt dosyaya kaydedilebilsin
        time.sleep(1)
        print("Kayıt tamamlandı")
    except KeyboardInterrupt:
        print("Kullanıcı kaydı durdurdu")
    except Exception as e:
        print(f"Hata: {e}")
        traceback.print_exc()
