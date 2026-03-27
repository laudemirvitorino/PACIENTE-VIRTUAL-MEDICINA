import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import os
from streamlit_mic_recorder import mic_recorder

st.set_page_config(page_title="Paciente Virtual com Voz", layout="centered")

# --- CONFIGURAÇÃO DO PROFESSOR (Igual ao anterior) ---
with st.sidebar:
    st.title("⚙️ Painel do Professor")
    api_key = st.text_input("Gemini API Key:", type="password")
    senha_prof = st.text_input("Senha:", type="password")
    
    if senha_prof == "L@uvitorino1977":
        caso = st.text_area("Prontuário/Instruções do Paciente:", height=200)
        if st.button("Salvar Caso"):
            st.session_state.contexto = caso
            st.session_state.messages = []
            st.success("Paciente pronto!")

# --- FUNÇÃO DE VOZ DO PACIENTE ---
def falar(texto):
    tts = gTTS(text=texto, lang='pt', slow=False)
    tts.save("resposta.mp3")
    return "resposta.mp3"

# --- INTERFACE DO ALUNO ---
st.header("🏥 Consulta por Voz")

if api_key and "contexto" in st.session_state:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Chat histórico
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # ENTRADA POR VOZ
    st.write("Clique no microfone para falar com o paciente:")
    audio_gravado = mic_recorder(start_prompt="🎤 Iniciar Anamnese (Voz)", stop_prompt="🛑 Parar e Enviar", key='recorder')

    # Processar se houver áudio ou texto
    texto_entrada = ""
    if audio_gravado:
        # Nota: Para traduzir áudio em texto perfeitamente no navegador, 
        # o ideal seria usar a própria API do Gemini que aceita arquivos de áudio.
        # Por simplicidade aqui, vamos focar no fluxo de resposta por voz.
        st.warning("O processamento de voz para texto exige configuração de áudio do servidor. Use o chat abaixo para testar a resposta sonora do paciente.")

    # ENTRADA POR TEXTO (Alternativa)
    if prompt := st.chat_input("Ou digite sua pergunta aqui..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Resposta do Paciente
        instrucao = f"Aja como este paciente: {st.session_state.contexto}. Responda de forma curta e humana."
        response = model.generate_content(instrucao + "\nPergunta do médico: " + prompt)
        
        texto_resposta = response.text
        
        with st.chat_message("assistant"):
            st.markdown(texto_resposta)
            # Gera o áudio da resposta
            audio_path = falar(texto_resposta)
            st.audio(audio_path, format="audio/mp3", autoplay=True) # Autoplay faz ele falar na hora
            
        st.session_state.messages.append({"role": "assistant", "content": texto_resposta})

else:
    st.info("Aguarde a configuração do professor.")
