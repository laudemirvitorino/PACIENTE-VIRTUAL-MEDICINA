import streamlit as st
import google.generativeai as genai

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Simulador de Paciente Virtual", page_icon="🩺", layout="centered")

# Estilização para uma aparência limpa e profissional
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; }
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. BARRA LATERAL: PAINEL DO PROFESSOR
with st.sidebar:
    st.title("👨‍🏫 Área do Professor")
    api_key = st.text_input("1. Gemini API Key:", type="password", help="Insira a chave gerada no Google AI Studio")
    senha_prof = st.text_input("2. Senha de Acesso:", type="password")
    
    # Senha padrão: medicina123
    if senha_prof == "L@uvitorino1977":
        st.success("Acesso Autorizado")
        st.divider()
        caso_clinico = st.text_area(
            "3. Defina o Caso Clínico (Prompt):", 
            placeholder="Ex: Paciente é o Sr. Alberto, 70 anos, com dispneia progressiva. Ele é ex-fumante e nega febre...",
            height=300
        )
        if st.button("🚀 Salvar e Iniciar Simulação"):
            st.session_state.contexto = caso_clinico
            st.session_state.messages = []
            st.session_state.finalizado = False
            st.success("Caso carregado com sucesso!")
    else:
        st.info("Insira a senha para configurar o paciente.")

    # Botão de Finalização (Só aparece se houver uma conversa em curso)
    if "messages" in st.session_state and len(st.session_state.messages) > 0 and not st.session_state.get("finalizado", False):
        st.divider()
        st.warning("Clique abaixo para encerrar o atendimento:")
        if st.button("🏁 ENCERRAR E RECEBER AVALIAÇÃO", type="primary"):
            st.session_state.finalizado = True
            st.rerun()

# 3. INTERFACE PRINCIPAL
st.header("🏥 Consulta Médica Virtual")

# Verifica se o professor já configurou o básico
if api_key and "contexto" in st.session_state:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # --- CENÁRIO A: EXIBIR AVALIAÇÃO FINAL ---
    if st.session_state.get("finalizado", False):
        st.subheader("📋 Relatório de Desempenho do Aluno")
        
        with st.spinner("O Preceptor Médico está analisando sua anamnese..."):
            # Concatena a conversa para análise
            historico_conversa = ""
            for m in st.session_state.messages:
                autor = "Aluno" if m["role"] == "user" else "Paciente"
                historico_conversa += f"{autor}: {m['content']}\n"

            prompt_avaliacao = f"""
            Você é um preceptor médico sênior, extremamente rigoroso e criterioso.
            Analise a anamnese realizada pelo aluno com base no caso clínico original: {st.session_state.contexto}.
            
            HISTÓRICO DA CONSULTA:
            {historico_conversa}
            
            FORNEÇA SUA AVALIAÇÃO SEGUINDO ESTA ESTRUTURA:
            1. PONTOS POSITIVOS: O que o aluno perguntou corretamente?
            2. PONTOS NEGATIVOS E OMISSÕES: O que o aluno esqueceu de investigar? Onde ele falhou na técnica semiológica ou na exploração da queixa? Seja exigente.
            3. POSTURA E TÉCNICA: Avalie se a linguagem foi adequada e se houve empatia.
            4. NOTA FINAL: Atribua uma nota de 0 a 10 (Seja rigoroso. Notas 10 são raríssimas e apenas para anamneses completas e perfeitas).
            """
            
            try:
                feedback = model.generate_content(prompt_avaliacao)
                st.markdown(feedback.text)
            except Exception as e:
                st.error(f"Erro ao gerar avaliação: {e}")
        
        if st.button("Reiniciar Novo Atendimento"):
            st.session_state.finalizado = False
            st.session_state.messages = []
            st.rerun()

    # --- CENÁRIO B: CONSULTA EM ANDAMENTO ---
    else:
        st.info("O paciente está aguardando. Comece a anamnese abaixo.")

        # Exibir balões de chat
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Campo de entrada de texto para o aluno
        if prompt_aluno := st.chat_input("Pergunte algo ao paciente..."):
            # Adiciona mensagem do aluno ao histórico
            st.session_state.messages.append({"role": "user", "content": prompt_aluno})
            with st.chat_message("user"):
                st.markdown(prompt_aluno)

            # Gera resposta do paciente
            with st.spinner("O paciente está respondendo..."):
                try:
                    # Instrução de sistema combinada com a pergunta
                    prompt_sistema = f"Aja estritamente como o seguinte paciente: {st.session_state.contexto}. Responda apenas como o paciente, de forma natural e humana. Não dê diagnósticos médicos. Pergunta do aluno: {prompt_aluno}"
                    
                    response = model.generate_content(prompt_sistema)
                    texto_resposta = response.text
                    
                    with st.chat_message("assistant"):
                        st.markdown(texto_resposta)
                    
                    st.session_state.messages.append({"role": "assistant", "content": texto_resposta})
                except Exception as e:
                    st.error(f"Erro na resposta do paciente: {e}")

else:
    # Caso o app abra e não tenha configuração
    if not api_key:
        st.warning("⚠️ Professor: Insira sua Gemini API Key no menu lateral.")
    elif "contexto" not in st.session_state:
        st.info("👋 Professor: Configure o Caso Clínico no menu lateral e clique em 'Iniciar'.")
    
    st.image("https://cdn-icons-png.flaticon.com/512/387/387561.png", width=100)
