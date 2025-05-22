import os
import time
from gtts import gTTS
import streamlit as st
import speech_recognition as sr
from deep_translator import GoogleTranslator
from uuid import uuid4

USE_STREAMLIT_AUDIO = True
isTranslateOn = False

# Supported languages from deep-translator
supported_languages = GoogleTranslator(source='auto', target='en').get_supported_languages(as_dict=True)
language_names = list(supported_languages.keys())

# Create reverse mapping
language_mapping = {name: code for code, name in supported_languages.items()}

def get_language_code(language_name):
    return language_mapping.get(language_name.lower(), language_name)

def translator_function(spoken_text, from_language, to_language):
    return GoogleTranslator(source=from_language, target=to_language).translate(spoken_text)

def text_to_voice(text_data, to_language):
    tts = gTTS(text=text_data, lang=to_language, slow=False)
    tts.save("cache_file.mp3")

    with open("cache_file.mp3", "rb") as audio_file:
        st.audio(audio_file.read(), format="audio/mp3")

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
            spoken_text = rec.recognize_google(audio, language=from_language)
            output_placeholder.text("Translating...")
            translated_text = translator_function(spoken_text, from_language, to_language)
            text_to_voice(translated_text, to_language)
        except sr.UnknownValueError:
            output_placeholder.error("Sorry, could not understand the audio.")
        except sr.RequestError:
            output_placeholder.error("Could not request results from Google Speech Recognition service.")
        except Exception as e:
            output_placeholder.error(f"Unexpected error: {e}")

# UI layout
st.title("Language Translator")

# Flag support
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

def get_label(lang):
    emoji = flag_map.get(lang.lower(), '')
    return f"{emoji} {lang}" if emoji else lang

from_language_name = st.selectbox("Select Source Language:", language_names, format_func=get_label)
to_language_name = st.selectbox("Select Target Language:", language_names, format_func=get_label)

from_language = get_language_code(from_language_name)
to_language = get_language_code(to_language_name)

st.subheader("Text-to-Text Translation")
input_text = st.text_input("Enter text to translate:")

if 'translation_history' not in st.session_state:
    st.session_state.translation_history = []

if st.button("Translate Text"):
    if input_text.strip():
        try:
            translated = translator_function(input_text, from_language, to_language)
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Original Text**")
                st.text_area("Input", input_text, height=150, key="original_text_area", disabled=True)

            with col2:
                st.markdown("**Translated Text**")
                st.text_area("Output", translated, height=150, key="translated_text_area", disabled=True)

            download_text = f"Original ({from_language}): {input_text}\n\nTranslated ({to_language}): {translated}"
            st.download_button("📥 Download Translation", data=download_text, file_name="translated_output.txt", mime="text/plain")

            st.session_state.translation_history.append({
                "id": str(uuid4()),
                "input": input_text,
                "output": translated,
                "from": from_language_name,
                "to": to_language_name
            })

        except Exception as e:
            st.error(f"Translation failed: {e}")
    else:
        st.warning("Please enter some text to translate.")

if st.session_state.translation_history:
    st.markdown("---")
    st.subheader("🕘 Translation History")
    for item in reversed(st.session_state.translation_history[-10:]):
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

start_button = st.button("Start")
stop_button = st.button("Stop")

if start_button:
    if not isTranslateOn:
        isTranslateOn = True
        output_placeholder = st.empty()
        main_process(output_placeholder, from_language, to_language)

if stop_button:
    isTranslateOn = False
