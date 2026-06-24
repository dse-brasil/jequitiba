import streamlit as st
import os
import sys
from dotenv import load_dotenv

# Carregar variáveis de ambiente e adicionar o diretório raiz ao path
load_dotenv()
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rag_engine import JequitibaRAGEngine

# Configurações de página do Streamlit
st.set_page_config(
    page_title="Projeto Jequitibá - Assistente Jurídico Inteligente",
    page_icon="🌳",
    layout="wide"
)

# Inicializar o RAG Engine
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VECTOR_DIR = os.path.join(BASE_DIR, "data", "vector_store")

@st.cache_resource
def get_rag_engine():
    return JequitibaRAGEngine(vector_store_dir=VECTOR_DIR)

try:
    engine = get_rag_engine()
except Exception as e:
    st.error(f"Erro ao inicializar o motor de RAG: {e}")
    engine = None

# Interface
logo_path = os.path.join(BASE_DIR, "logo_jequitiba.png")

col1, col2 = st.columns([1, 6])
with col1:
    if os.path.exists(logo_path):
        st.image(logo_path, width=100)
    else:
        st.title("🌳")
with col2:
    st.title("Projeto Jequitibá")
    st.subheader("Assistente Jurídico Inteligente Baseado em RAG e LLMs")

st.markdown("---")

# Barra lateral para informações adicionais e configurações
with st.sidebar:
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    st.image("https://img.shields.io/badge/USP%20ICMC-F7DF1E?style=for-the-badge&logo=school", width=150)
    st.header("Configurações")
    
    # Exibir modelo ativo
    model_active = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    st.info(f"**Modelo Ativo:** {model_active}")
    
    st.markdown("""
    ### Sobre o Sistema
    O Jequitibá recupera trechos de documentos e contratos jurídicos de forma precisa, 
    usando embeddings vetoriais, e gera respostas fundamentadas sem alucinações.
    
    **Desenvolvido no ICMC-USP.**
    """)

# Inicializar histórico de mensagens
if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibir mensagens do histórico
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message and message["sources"]:
            with st.expander("Ver fontes consultadas"):
                for doc in message["sources"]:
                    st.write(f"- **{doc.get('source')}** (Página {doc.get('page')})")

# Input do usuário
if query := st.chat_input("Faça uma pergunta sobre os contratos ou processos indexados:"):
    # Exibir pergunta do usuário
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    # Gerar e exibir resposta
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        if engine:
            with st.spinner("Jequitibá buscando informações nos documentos..."):
                response = engine.generate_answer(query)
                answer = response["answer"]
                sources = response["sources"]
        else:
            answer = "Sistema indisponível. Verifique a configuração do RAG Engine e as chaves de API."
            sources = []
            
        message_placeholder.markdown(answer)
        
        if sources:
            with st.expander("Ver fontes consultadas"):
                for doc in sources:
                    st.write(f"- **{doc.get('source')}** (Página {doc.get('page')})")
                    
        # Salvar resposta no histórico
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "sources": sources
        })
