import os
import time
import pygame
from gtts import gTTS
import streamlit as st
import speech_recognition as sr
from googletrans import LANGUAGES, Translator
from uuid import uuid4

USE_STREAMLIT_AUDIO = os.environ.get('STREAMLIT_CLOUD', 'false') == 'true'
isTranslateOn = False

translator = Translator() # Initialize the translator module.
pygame.mixer.init()  # Initialize the mixer module.

# Create a mapping between language names and language codes
language_mapping = {name: code for code, name in LANGUAGES.items()}

def get_language_code(language_name):
    return language_mapping.get(language_name, language_name)

def translator_function(spoken_text, from_language, to_language):
    return translator.translate(spoken_text, src='{}'.format(from_language), dest='{}'.format(to_language))

def text_to_voice(text_data, to_language):
    tts = gTTS(text=text_data, lang=to_language, slow=False)
    tts.save("cache_file.mp3")

    if USE_STREAMLIT_AUDIO:
        with open("cache_file.mp3", "rb") as audio_file:
            st.audio(audio_file.read(), format="audio/mp3")
    else:
        import pygame
        pygame.mixer.init()
        sound = pygame.mixer.Sound("cache_file.mp3")
        sound.play()


def main_process(output_placeholder, from_language, to_language):
    
    global isTranslateOn

    if USE_STREAMLIT_AUDIO:
        output_placeholder.warning("Voice translation via microphone is not supported on Streamlit Cloud.")
        return


    while isTranslateOn:
        rec = sr.Recognizer()
        with sr.Microphone() as source:
            output_placeholder.text("Listening...")
            rec.pause_threshold = 1
            audio = rec.listen(source, phrase_time_limit=10)
       
        try:
            output_placeholder.text("Processing...")
            spoken_text = rec.recognize_google(audio, language='{}'.format(from_language))
            
            output_placeholder.text("Translating...")
            translated_text = translator_function(spoken_text, from_language, to_language)

            text_to_voice(translated_text.text, to_language)
    
        except sr.UnknownValueError:
            output_placeholder.error("Sorry, could not understand the audio.")
        except sr.RequestError:
            output_placeholder.error("Could not request results from Google Speech Recognition service.")
        except Exception as e:
            output_placeholder.error(f"Unexpected error: {e}")

# UI layout
st.title("Language Translator")

# Optional: Add flags to some language dropdowns
flag_map = {
    'english': '🇺🇸',
    'hindi': '🇮🇳',
    'french': '🇫🇷',
    'spanish': '🇪🇸',
    'german': '🇩🇪',
    'chinese (simplified)': '🇨🇳',
    'japanese': '🇯🇵',
    'russian': '🇷🇺',
    'arabic': '🇸🇦',
}

language_names = list(LANGUAGES.values())

# Function to add flag to language name
def get_label(lang):
    emoji = flag_map.get(lang.lower(), '')
    return f"{emoji} {lang}" if emoji else lang

# Dropdowns with flags
from_language_name = st.selectbox("Select Source Language:", language_names, format_func=get_label)
to_language_name = st.selectbox("Select Target Language:", language_names, format_func=get_label)


# Convert language names to language codes
from_language = get_language_code(from_language_name)
to_language = get_language_code(to_language_name)

auto_detect = st.checkbox("Auto-detect source language (Text-to-Text only)")

# --- Text to Text Translation Section ---
st.subheader("Text-to-Text Translation")

# Text input field
input_text = st.text_input("Enter text to translate:")

# Initialize history in session state if not present
if 'translation_history' not in st.session_state:
    st.session_state.translation_history = []

# Button to trigger text translation
if st.button("Translate Text"):
    if input_text.strip():

        if auto_detect:
            detected = translator.detect(input_text)
            detected_lang_code = detected.lang
            detected_lang_name = LANGUAGES.get(detected_lang_code, detected_lang_code)
            confidence = detected.confidence 

            from_language_code = detected_lang_code
            from_language_display = detected_lang_name

            if confidence is not None:
                confidence = round(confidence * 100, 2)
                st.success(f"Detected Language: {detected_lang_name} ({confidence}% confidence)")
            else:
                st.success(f"Detected Language: {detected_lang_name} (confidence not available)")
            

        translated = translator_function(input_text, from_language_code, to_language)
        
        # ✅ Side-by-side view
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Original Text**")
            st.text_area("Input", input_text, height=150, key="original_text_area", disabled=True)

        with col2:
             st.markdown("**Translated Text**")
             st.text_area("Output", translated.text, height=150, key="translated_text_area", disabled=True)

        # Create a downloadable text file with the translation
        download_text = f"Original ({from_language}): {input_text}\n\nTranslated ({to_language}): {translated.text}"
        st.download_button(
            label="📥 Download Translation",
            data=download_text,
            file_name="translated_output.txt",
            mime="text/plain"   
)


        # Store the translation in session state
        st.session_state.translation_history.append({
            "id": str(uuid4()),  # Unique ID for widget keys
            "input": input_text,
            "output": translated.text,
            "from": from_language_display,
            "to": to_language_name
        })


    else:
        st.warning("Please enter some text to translate.")

# Show translation history
if st.session_state.translation_history:
    st.markdown("---")
    st.subheader("🕘 Translation History")
    for item in reversed(st.session_state.translation_history[-10:]):  # Show last 10
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**{item['from']}**")
            st.text_area("Original", item["input"], height=100, disabled=True, key=f"hist_input_{item['id']}")

        with c2:
            st.markdown(f"**{item['to']}**")
            st.text_area("Translated", item["output"], height=100, disabled=True, key=f"hist_output_{item['id']}")

        
        
    if st.button("Clear History"):
        st.session_state.translation_history.clear()
        st.rerun()


# Button to trigger translation
start_button = st.button("Start")
stop_button = st.button("Stop")

# Check if "Start" button is clicked
if start_button:
    if not isTranslateOn:
        isTranslateOn = True
        output_placeholder = st.empty()
        main_process(output_placeholder, from_language, to_language)

# Check if "Stop" button is clicked
if stop_button:
    isTranslateOn = False
