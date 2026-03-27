import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import os
from streamlit_mic_recorder import mic_recorder
import tempfile

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Simulador de Paciente Virtual - Medicina", page_icon="🏥", layout="centered")

# Estilização visual básica
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 20px; }
    .stChatFloatingInputContainer { padding-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# 2. BARRA LATERAL: ÁREA DO PROFESSOR (OCULTA POR SENHA)
with st.sidebar:
    st.title("👨‍🏫 Painel do Professor")
    api_key = st.text_input("1. Cole sua Gemini API Key:", type="password")
    senha_prof = st.text_input("2. Senha de Acesso:", type="password")
    
    # A senha padrão é medicina123 (você pode alterar na linha abaixo)
    if senha_prof == "L@uvitorino1977":
        st.success("Acesso Liberado")
        st.divider()
        caso_clinico = st.text_area(
            "3. Defina o Caso Clínico (Prompt):", 
            placeholder="Ex: Você é o Sr. João, 65 anos, fumante, com dor no peito...",
            height=300
        )
        if st.button("🚀 Iniciar/Resetar Caso"):
            st.session_state.contexto = caso_clinico
            st.session_state.messages = []
            st.session_state.finalizado = False
            st.success("Caso carregado! O aluno já pode começar.")
    else:
        st.info("Insira a senha para configurar o paciente.")

    if "messages" in st.session_state and len(st.session_state.messages) > 0:
        st.divider()
        if st.button("🏁 ENCERRAR E AVALIAR ALUNO", type="primary"):
            st.session_state.finalizado = True

# 3. LÓGICA PRINCIPAL DO APLICATIVO
st.header("🏥 Consulta Médica Virtual")

if api_key and "contexto" in st.session_state:
    genai.configure(api_key=api_key)
    # Utilizamos o modelo Flash para respostas rápidas
    model = genai.GenerativeModel('gemini-1.5-flash')

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # --- TELA DE AVALIAÇÃO FINAL ---
    if st.session_state.get("finalizado", False):
        st.subheader("📋 Relatório de Desempenho do Aluno")
        
        with st.spinner("O Preceptor está analisando a consulta..."):
            # Construindo o histórico para a avaliação
            historico_conversa = ""
            for m in st.session_state.messages:
                autor = "Aluno" if m["role"] == "user" else "Paciente"
                historico_conversa += f"{autor}: {m['content']}\n"

            prompt_feedback = f"""
            Você é um preceptor médico extremamente rigoroso e experiente. 
            Analise a anamnese feita pelo aluno com base no caso clínico: {st.session_state.contexto}.
            
            Sua tarefa é avaliar o desempenho do aluno no seguinte histórico:
            {historico_conversa}
            
            Forneça um relatório detalhado com:
            1. PONTOS POSITIVOS: O que foi perguntado corretamente.
            2. PONTOS NEGATIVOS/FALTANTES: O que o aluno esqueceu ou errou na técnica (Seja muito criterioso).
            3. POSTURA E EMPATIA: Avalie a forma como o aluno falou com o paciente.
            4. NOTA FINAL: De 0 a 10 (Seja exigente. Notas 10 são apenas para perfeição técnica e humana).
            
            Responda de forma profissional e direta.
            """
            
            try:
                feedback = model.generate_content(prompt_feedback)
                st.markdown(feedback.text)
            except Exception as e:
                st.error(f"Erro ao gerar avaliação: {e}")
        
        if st.button("Voltar para a Consulta"):
            st.session_state.finalizado = False
            st.rerun()

    # --- TELA DE CHAT (CONSULTA EM ANDAMENTO) ---
    else:
        st.info("Paciente na sala. Comece a anamnese por voz ou texto.")

        # Exibir histórico de mensagens
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Interface de Entrada (Voz e Texto)
        st.divider()
        col_voz, col_texto = st.columns([1, 4])
        
        with col_voz:
            audio_data = mic_recorder(start_prompt="🎤 Falar", stop_prompt="🛑 Enviar", key='recorder')

        with col_texto:
            prompt_texto = st.chat_input("Digite sua pergunta...")

        # Processar entrada do aluno
        input_usuario = None
        conteudo_gemini = []

        if audio_data:
            input_usuario = "🎤 [Mensagem de Voz enviada]"
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_audio:
                tmp_audio.write(audio_data['bytes'])
                tmp_audio_path = tmp_audio.name
            
            # Envia áudio para o Gemini ouvir
            audio_file = genai.upload_file(path=tmp_audio_path, mime_type="audio/wav")
            conteudo_gemini = [
                f"Aja estritamente como o paciente descrito: {st.session_state.contexto}. Ouça o áudio do aluno e responda.",
                audio_file
            ]
        elif prompt_texto:
            input_usuario = prompt_texto
            conteudo_gemini = [
                f"Aja como o paciente: {st.session_state.contexto}. Responda à pergunta do médico: {prompt_texto}"
            ]

        # Se houver uma nova pergunta, gera a resposta do paciente
        if input_usuario:
            st.session_state.messages.append({"role": "user", "content": input_usuario})
            with st.chat_message("user"):
                st.markdown(input_usuario)

            with st.spinner("O paciente está respondendo..."):
                try:
                    response = model.generate_content(conteudo_gemini)
                    texto_resposta = response.text
                    
                    with st.chat_message("assistant"):
                        st.markdown(texto_resposta)
                        
                        # Converte resposta em voz (TTS)
                        tts = gTTS(text=texto_resposta, lang='pt', slow=False)
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_mp3:
                            tts.save(tmp_mp3.name)
                            st.audio(tmp_mp3.name, format="audio/mp3", autoplay=True)
                    
                    st.session_state.messages.append({"role": "assistant", "content": texto_resposta})
                except Exception as e:
                    st.error(f"Erro: {e}")

else:
    # Mensagem inicial caso o professor ainda não tenha configurado nada
    st.warning("⚠️ Professor: Acesse a barra lateral, insira sua API Key e configure o Caso Clínico para começar.")
    st.image("https://cdn-icons-png.flaticon.com/512/387/387561.png", width=100)
