"""
streamlit_app.py - Interface do Projeto Jequitibá (versão avançada)
"""

import streamlit as st
import os
import sys
import time
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv
import logging
from loguru import logger

# Configuração de logging
logger.remove()  # remove default handler
logger.add(sys.stderr, level="INFO", format="{time} | {level} | {message}")

# Carregar variáveis de ambiente
load_dotenv()

# Adicionar diretório raiz ao path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from src.rag_engine import JequitibaRAGEngine

# ============================
# CONFIGURAÇÕES DO STREAMLIT
# ============================
st.set_page_config(
    page_title="Projeto Jequitibá - Assistente Jurídico",
    page_icon="🌳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================
# INICIALIZAÇÃO DO RAG ENGINE (CACHEADO)
# ============================
VECTOR_DIR = os.path.join(BASE_DIR, "data", "vector_store")

@st.cache_resource
def load_rag_engine():
    """Carrega o engine RAG com cache para evitar recargas."""
    try:
        engine = JequitibaRAGEngine(vector_store_dir=VECTOR_DIR)
        logger.info("RAG Engine carregado com sucesso.")
        return engine
    except Exception as e:
        logger.error(f"Falha ao carregar RAG Engine: {e}")
        st.error(f"Erro crítico ao inicializar o motor de busca: {e}")
        return None

engine = load_rag_engine()

# ============================
# CONFIGURAÇÕES DA SESSÃO
# ============================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []
if "rag_params" not in st.session_state:
    st.session_state.rag_params = {
        "top_k": 5,
        "score_threshold": 0.6,
        "model": os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
        "temperature": 0.0,
    }

# ============================
# FUNÇÕES AUXILIARES
# ============================
def log_query(query: str, answer: str, sources: List[Dict], duration: float):
    """Registra a consulta e a resposta em um arquivo de log estruturado."""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "conversation_id": st.session_state.conversation_id,
        "query": query,
        "answer": answer[:200] + "..." if len(answer) > 200 else answer,
        "sources": sources,
        "duration_sec": duration,
        "params": st.session_state.rag_params,
    }
    logger.info(f"Consulta processada: {json.dumps(log_entry, ensure_ascii=False)}")
    # Opcional: salvar em arquivo
    # with open("logs/query_log.jsonl", "a", encoding="utf-8") as f:
    #     f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

def format_sources(sources: List[Dict]) -> str:
    """Formata as fontes para exibição amigável."""
    if not sources:
        return "Nenhuma fonte específica foi utilizada."
    lines = []
    for idx, doc in enumerate(sources, 1):
        source = doc.get("source", "Documento desconhecido")
        page = doc.get("page", "N/A")
        score = doc.get("score", None)
        score_str = f" (similaridade: {score:.3f})" if score is not None else ""
        lines.append(f"{idx}. **{source}** - Página {page}{score_str}")
    return "\n".join(lines)

def display_chunks(chunks: List[Dict]):
    """Exibe os trechos recuperados de forma destacada."""
    if not chunks:
        return
    with st.expander("📄 Trechos recuperados (usados para gerar a resposta)"):
        for i, chunk in enumerate(chunks):
            score = chunk.get("score", 0)
            st.markdown(f"**Chunk {i+1}** (score: {score:.3f})")
            st.markdown(f"> {chunk.get('text', '')[:500]}...")
            st.caption(f"Fonte: {chunk.get('source', '')} - Pág. {chunk.get('page', '')}")
            st.divider()

# ============================
# INTERFACE PRINCIPAL
# ============================
# Cabeçalho
col1, col2 = st.columns([1, 6])
with col1:
    st.image(os.path.join(BASE_DIR, "logo_jequitiba.png"), width=120) if os.path.exists(
        os.path.join(BASE_DIR, "logo_jequitiba.png")
    ) else st.title("🌳")
with col2:
    st.title("Projeto Jequitibá")
    st.subheader("Assistente Jurídico Inteligente com RAG e LLMs")

st.markdown("---")

# ============================
# SIDEBAR - CONFIGURAÇÕES
# ============================
with st.sidebar:
    st.image("https://img.shields.io/badge/USP%20ICMC-F7DF1E?style=for-the-badge&logo=school", width=180)
    st.header("⚙️ Parâmetros do RAG")
    
    # Controles deslizantes para ajuste fino
    top_k = st.slider(
        "Número de trechos (top_k)",
        min_value=1,
        max_value=20,
        value=st.session_state.rag_params["top_k"],
        help="Quantos trechos mais relevantes serão recuperados.",
    )
    threshold = st.slider(
        "Limiar de similaridade",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state.rag_params["score_threshold"],
        step=0.05,
        help="Trechos com score abaixo deste valor serão descartados.",
    )
    
    # Seletor de modelo (caso o RAG Engine suporte múltiplos)
    model_options = ["gemini-1.5-flash", "gemini-1.5-pro"]
    selected_model = st.selectbox(
        "Modelo LLM",
        options=model_options,
        index=model_options.index(st.session_state.rag_params["model"])
        if st.session_state.rag_params["model"] in model_options
        else 0,
    )
    
    # Atualizar parâmetros na sessão
    st.session_state.rag_params.update({
        "top_k": top_k,
        "score_threshold": threshold,
        "model": selected_model,
    })
    
    # Mostrar status do engine
    if engine:
        st.success("✅ Motor RAG ativo")
    else:
        st.error("❌ Motor RAG indisponível")
    
    st.divider()
    st.header("📁 Upload de Documentos")
    uploaded_files = st.file_uploader(
        "Adicione novos PDFs para indexar (experimental)",
        type=["pdf"],
        accept_multiple_files=True,
        key="file_uploader",
    )
    if uploaded_files:
        # Aqui você implementaria a lógica de ingestão dinâmica
        # Por enquanto, apenas avisamos
        st.info("Funcionalidade em desenvolvimento: os arquivos serão indexados em breve.")
        # st.session_state.uploaded_files.extend(uploaded_files)
    
    st.divider()
    st.header("📊 Estatísticas da Sessão")
    st.metric("Perguntas feitas", len(st.session_state.messages) // 2)
    st.caption(f"ID da conversa: {st.session_state.conversation_id}")
    
    if st.button("🔄 Nova Conversa"):
        st.session_state.messages = []
        st.session_state.conversation_id = hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]
        st.rerun()
    
    st.divider()
    st.markdown("""
    **Sobre o Jequitibá**  
    Recupera trechos de documentos jurídicos via embeddings vetoriais e gera respostas fundamentadas, com rastreabilidade total.
    
    [Repositório no GitHub](https://github.com/fertorresfs/legal-rag-assistant)
    """)

# ============================
# ÁREA PRINCIPAL - CHAT
# ============================
# Exibir mensagens do histórico
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message and message["sources"]:
            with st.expander("📚 Ver fontes consultadas"):
                st.markdown(format_sources(message["sources"]))

# Input do usuário
if query := st.chat_input("Faça uma pergunta sobre os contratos ou processos indexados:"):
    # Adicionar pergunta ao histórico
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    # Preparar resposta
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        sources = []
        chunks = []
        duration = 0.0

        if engine:
            try:
                # Atualizar parâmetros no engine (se suportar)
                # engine.update_params(top_k=top_k, threshold=threshold, model=selected_model)
                start_time = time.time()
                
                # Chamada ao RAG
                with st.spinner("🌳 Jequitibá está analisando os documentos..."):
                    response = engine.generate_answer(
                        query,
                        top_k=top_k,
                        score_threshold=threshold,
                    )
                duration = time.time() - start_time
                
                answer = response.get("answer", "Desculpe, não foi possível gerar uma resposta.")
                sources = response.get("sources", [])
                chunks = response.get("chunks", [])  # idealmente o engine retorna os chunks usados
                
                # Se não houver chunks, tentamos extrair do response
                if not chunks and "retrieved_chunks" in response:
                    chunks = response["retrieved_chunks"]
                
                # Log da consulta
                log_query(query, answer, sources, duration)
                
            except Exception as e:
                logger.error(f"Erro durante a geração: {e}")
                answer = f"⚠️ Ocorreu um erro ao processar sua pergunta: {str(e)}"
                sources = []
                chunks = []
        else:
            answer = "❌ Sistema indisponível. Verifique a configuração do RAG Engine e as chaves de API."
            sources = []

        # Exibir resposta
        full_response = answer
        message_placeholder.markdown(full_response)

        # Exibir trechos recuperados (se houver)
        if chunks:
            display_chunks(chunks)

        # Exibir fontes
        if sources:
            with st.expander("📚 Ver fontes consultadas (detalhadas)"):
                st.markdown(format_sources(sources))
                # Mostrar também o tempo de resposta
                st.caption(f"⏱️ Tempo de resposta: {duration:.2f}s")
        else:
            st.caption("ℹ️ Nenhuma fonte específica foi citada.")

        # Salvar no histórico
        st.session_state.messages.append({
            "role": "assistant",
            "content": full_response,
            "sources": sources,
            "chunks": chunks,  # opcional, para exibir depois
        })