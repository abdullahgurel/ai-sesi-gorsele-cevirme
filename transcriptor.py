import os
import traceback
import speech_recognition as sr
from datetime import datetime

class Transcriptor:
    def __init__(self):
        """
        SpeechRecognition kütüphanesini kullanarak yerel ses tanıma gerçekleştiren sınıf
        """
        try:
            self.recognizer = sr.Recognizer()
            print("Transcriptor başarıyla başlatıldı / Transcriptor initialized successfully")
        except Exception as e:
            print(f"Speech Recognition başlatılırken hata: {e}")
            traceback.print_exc()
            raise
    
    def transcribe(self, audio_file_path, language="tr-TR"):
        """
        Ses dosyasını metne dönüştürür / Transcribes the audio file to text
        
        Args:
            audio_file_path (str): Ses dosyasının yolu / Path to the audio file
            language (str): Dil kodu (örn. "tr-TR" Türkçe, "en-US" İngilizce için) / Language code (e.g., "tr-TR" for Turkish, "en-US" for English)
            
        Returns:
            str: Dönüştürülen metin / Transcribed text
        """
        print(f"Ses dosyası transkript edilmeye çalışılıyor: {audio_file_path} / Transcribing audio file: {audio_file_path}")
        
        if not os.path.exists(audio_file_path):
            error_msg = f"Ses dosyası bulunamadı: {audio_file_path} / Audio file not found: {audio_file_path}"
            print(error_msg)
            raise FileNotFoundError(error_msg)
        
        try:
            with sr.AudioFile(audio_file_path) as source:
                print("Ses dosyası okunuyor... / Reading audio file...")
                audio_data = self.recognizer.record(source)
                
                print("Google Speech Recognition API ile tanıma yapılıyor... / Recognizing with Google Speech Recognition API...")
                text = self.recognizer.recognize_google(audio_data, language=language)
                
                print(f"Transkript başarılı: {text[:50]}... / Transcription successful")
                return text
                
        except sr.UnknownValueError:
            print("Google Speech Recognition sesi anlayamadı / Could not understand audio")
            return None
        except sr.RequestError as e:
            print(f"Google Speech Recognition servisinden sonuç alınamadı; {e} / Could not request results from service")
            return None
        except Exception as e:
            print(f"Ses dosyasını transkript ederken hata: {e} / Error while transcribing audio")
            traceback.print_exc()
            return None
    
    def save_transcript(self, text, output_file=None):
        """
        Dönüştürülen metni dosyaya kaydeder / Saves the transcribed text to a file
        
        Args:
            text (str): Dönüştürülen metin / Transcribed text
            output_file (str): Kaydedilecek dosya yolu / Output file path
            
        Returns:
            str: Kaydedilen dosya yolu / Saved file path
        """
        if not text:
            print("Kaydedilecek transkript yok / No transcript to save")
            return None
        
        if not output_file:
            # Timestamp kullanarak dosya adı oluştur / Generate file name with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"transcript_{timestamp}.txt"
        
        try:
            print(f"Transkript kaydediliyor: {output_file} / Saving transcript: {output_file}")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(text)
            
            print("Transkript başarıyla kaydedildi / Transcript saved successfully")
            return output_file
        
        except Exception as e:
            print(f"Transkripti kaydederken hata: {e} / Error saving transcript")
            traceback.print_exc()
            return None

# Example usage
if __name__ == "__main__":
    try:
        transcriptor = Transcriptor()
        
        # Example audio file path
        audio_file = "recordings/audio_sample.wav"
        
        if os.path.exists(audio_file):
            # Transcribe audio in Turkish
            text_tr = transcriptor.transcribe(audio_file, language="tr-TR")
            if text_tr:
                print(f"[TR] Transkript: {text_tr}")
                transcriptor.save_transcript(text_tr, "transcripts/sample_transcript_tr.txt")

            # Transcribe audio in English
            text_en = transcriptor.transcribe(audio_file, language="en-US")
            if text_en:
                print(f"[EN] Transcript: {text_en}")
                transcriptor.save_transcript(text_en, "transcripts/sample_transcript_en.txt")
        else:
            print(f"Ses dosyası bulunamadı: {audio_file} / Audio file not found: {audio_file}")
    except Exception as e:
        print(f"Hata: {e} / Error: {e}")
        traceback.print_exc()
