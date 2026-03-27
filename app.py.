import streamlit as st
import google.generativeai as genai

# Configuração da página
st.set_page_config(page_title="Simulador de Paciente Virtual", layout="centered")

# --- BARRA LATERAL: CONFIGURAÇÃO DO PROFESSOR ---
with st.sidebar:
    st.title("⚙️ Configuração")
    api_key = st.text_input("Insira sua Gemini API Key:", type="password")
    senha_prof = st.text_input("Senha do Professor (para editar o caso):", type="password")
    
    if senha_prof == "medicina123": # Você pode mudar essa senha
        st.subheader("Configuração do Caso Clínico")
        caso = st.text_area("Instruções de comportamento e prontuário:", 
                            height=300,
                            help="Defina aqui quem é o paciente, o que ele sente e como deve agir.")
        if st.button("Salvar e Iniciar Caso"):
            st.session_state.contexto = caso
            st.session_state.messages = []
            st.success("Caso carregado!")

# --- INTERFACE DO ALUNO ---
st.header("🏥 Consulta Médica Virtual")
st.info("Realize a anamnese com o paciente abaixo.")

if api_key and "contexto" in st.session_state:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash') # Versão rápida e eficiente

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Exibir histórico
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Input do aluno
    if prompt := st.chat_input("Pergunte algo ao paciente..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Preparar o contexto para a IA
        instrucao_sistema = f"Aja estritamente como este paciente: {st.session_state.contexto}. Não saia do personagem. Responda de forma natural humana."
        
        try:
            # Envia o contexto + a pergunta do aluno
            response = model.generate_content(instrucao_sistema + "\nAluno: " + prompt)
            with st.chat_message("assistant"):
                st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"Erro: {e}")
else:
    if not api_key:
        st.warning("Por favor, insira a API Key na barra lateral.")
    if "contexto" not in st.session_state:
        st.warning("Aguarde o professor configurar o caso clínico.")
