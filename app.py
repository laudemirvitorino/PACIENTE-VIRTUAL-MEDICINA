import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import os
from streamlit_mic_recorder import mic_recorder
import tempfile

# Configuração da página
st.set_page_config(page_title="Paciente Virtual Multimodal", page_icon="🏥")

# --- ESTILIZAÇÃO PARA MELHORAR A EXPERIÊNCIA ---
st.markdown("""
    <style>
    .stChatFloatingInputContainer {padding-bottom: 20px;}
    .reportview-container .main .footer {color: #777;}
    </style>
    """, unsafe_allow_html=True)

# --- PAINEL DO PROFESSOR (LATERAL) ---
with st.sidebar:
    st.title("👨‍🏫 Configuração do Caso")
    api_key = st.text_input("Insira sua Gemini API Key:", type="password")
    senha_prof = st.text_input("Senha de Acesso:", type="password")
    
    if senha_prof == "L@uvitorino1977":
        st.divider()
        caso_clinico = st.text_area(
            "Defina o Paciente (Prompt):", 
            placeholder="Ex: Você é Dona Maria, 70 anos. Está confusa e com dor abdominal forte...",
            height=300
        )
        if st.button("🔄 Atualizar/Reiniciar Caso"):
            st.session_state.contexto = caso_clinico
            st.session_state.messages = []
            st.success("Caso carregado com sucesso!")
    else:
        st.info("Insira a senha para editar o caso.")

# --- LÓGICA DO CHAT E IA ---
if api_key and "contexto" in st.session_state:
    genai.configure(api_key=api_key)
    # Usamos o modelo Flash por ser mais rápido para conversão de voz
    model = genai.GenerativeModel('gemini-1.5-flash')

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Exibir histórico de mensagens
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # --- ENTRADAS DO ALUNO (ÁUDIO E TEXTO) ---
    st.write("---")
    col1, col2 = st.columns([1, 4])
    
    with col1:
        # Gravador de áudio
        audio_data = mic_recorder(
            start_prompt="🎤 Falar",
            stop_prompt="🛑 Enviar",
            key='recorder'
        )

    with col2:
        prompt_texto = st.chat_input("Ou digite sua pergunta aqui...")

    # Processamento da Resposta
    input_usuario = None
    conteudo_para_gemini = []

    # Se o aluno falou (Áudio)
    if audio_data:
        input_usuario = "🎤 [Áudio enviado pelo aluno]"
        # Salva o áudio temporariamente para enviar ao Gemini
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_audio:
            tmp_audio.write(audio_data['bytes'])
            tmp_audio_path = tmp_audio.name
        
        # Prepara o payload multimodal (Texto do sistema + Áudio)
        audio_file_gemini = genai.upload_file(path=tmp_audio_path, mime_type="audio/wav")
        conteudo_para_gemini = [
            f"Instrução: Aja como este paciente: {st.session_state.contexto}. O áudio a seguir é a pergunta do médico.",
            audio_file_gemini
        ]

    # Se o aluno digitou (Texto)
    elif prompt_texto:
        input_usuario = prompt_texto
        conteudo_para_gemini = [
            f"Instrução: Aja como este paciente: {st.session_state.contexto}. Responda à pergunta do médico: {prompt_texto}"
        ]

    # Executar a IA se houver entrada
    if input_usuario:
        st.session_state.messages.append({"role": "user", "content": input_usuario})
        with st.chat_message("user"):
            st.markdown(input_usuario)

        with st.spinner("O paciente está pensando..."):
            try:
                # Gera resposta
                response = model.generate_content(conteudo_para_gemini)
                texto_resposta = response.text
                
                # Exibe resposta em texto
                with st.chat_message("assistant"):
                    st.markdown(texto_resposta)
                    
                    # Gera áudio da resposta (TTS)
                    tts = gTTS(text=texto_resposta, lang='pt', slow=False)
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_mg:
                        tts.save(tmp_mg.name)
                        st.audio(tmp_mg.name, format="audio/mp3", autoplay=True)
                
                st.session_state.messages.append({"role": "assistant", "content": texto_resposta})
                
            except Exception as e:
                st.error(f"Erro ao processar: {e}")

else:
    if not api_key:
        st.warning("⚠️ Professor: Insira a Gemini API Key na barra lateral para começar.")
    elif "contexto" not in st.session_state:
        st.info("👋 Professor: Configure o caso clínico e clique em 'Salvar' para liberar o chat para o aluno.")
