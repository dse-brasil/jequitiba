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
    logo_file = os.path.join(BASE_DIR, "logo_jequitiba.png")
    if os.path.exists(logo_file):
        st.image(logo_file, width=120)
    else:
        st.title("🌳")
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
# ÁREA PRINCIPAL - ABAS
# ============================
tab_chat, tab_datajud = st.tabs(["💬 Chat Jurídico (RAG)", "🔍 Consulta Processual (Datajud)"])

with tab_chat:
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
                    chunks = response.get("chunks", [])
                    
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
                    st.caption(f"⏱️ Tempo de resposta: {duration:.2f}s")
            else:
                st.caption("ℹ️ Nenhuma fonte específica foi citada.")

            # Salvar no histórico
            st.session_state.messages.append({
                "role": "assistant",
                "content": full_response,
                "sources": sources,
                "chunks": chunks,
            })
            st.rerun()

with tab_datajud:
    st.header("🔍 Consulta Direta ao Datajud (CNJ)")
    st.markdown("Pesquise metadados e andamento de processos públicos em qualquer tribunal do Brasil em tempo real.")
    
    col_input, col_btn = st.columns([4, 1])
    with col_input:
        proc_query = st.text_input(
            "Número do Processo (CNJ)",
            placeholder="Ex: 0000832-35.2018.4.01.3202",
            help="Número unificado de 20 dígitos."
        )
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        search_btn = st.button("Buscar Processo", use_container_width=True)
        
    if search_btn and proc_query:
        from src.datajud_client import DatajudClient
        dj_client = DatajudClient()
        
        with st.spinner("Consultando base nacional do Datajud..."):
            res = dj_client.query_process(proc_query)
            
        if res.get("success"):
            proc_data = res["data"]
            court = res["court"]
            
            st.success(f"✅ Processo localizado no index `{court}`!")
            
            col_info1, col_info2 = st.columns(2)
            with col_info1:
                st.markdown(f"**Número CNJ:** `{dj_client.format_cnj_number(proc_data.get('numeroProcesso', ''))}`")
                st.markdown(f"**Tribunal/Index:** `{court}`")
                st.markdown(f"**Classe Processual:** {proc_data.get('classe', {}).get('nome', 'N/A')} (Código: {proc_data.get('classe', {}).get('codigo', 'N/A')})")
                st.markdown(f"**Grau de Jurisdição:** `{proc_data.get('grau', 'N/A')}`")
            with col_info2:
                st.markdown(f"**Órgão Julgador:** {proc_data.get('orgaoJulgador', {}).get('nome', 'N/A')} (Código: {proc_data.get('orgaoJulgador', {}).get('codigo', 'N/A')})")
                st.markdown(f"**Data de Ajuizamento:** {proc_data.get('dataAjuizamento', '').split('T')[0] if proc_data.get('dataAjuizamento') else 'N/A'}")
                st.markdown(f"**Sistema Eletrônico:** {proc_data.get('sistema', {}).get('nome', 'N/A')}")
                st.markdown(f"**Formato:** {proc_data.get('formato', {}).get('nome', 'N/A')}")
                
            st.divider()
            
            # Assuntos
            assuntos_list = []
            for a in proc_data.get("assuntos", []):
                if isinstance(a, list):
                    for item in a:
                        if isinstance(item, dict):
                            assuntos_list.append(item.get("nome"))
                elif isinstance(a, dict):
                    assuntos_list.append(a.get("nome"))
            st.markdown(f"**Assuntos:** {', '.join(assuntos_list) if assuntos_list else 'N/A'}")
            
            # Movimentações
            st.markdown("### ⏳ Linha do Tempo de Movimentações")
            movs = proc_data.get("movimentos", [])
            if movs:
                movs_table = []
                for m in movs:
                    dt = m.get("dataHora", "").replace("T", " ").replace("Z", "")
                    if dt:
                        dt = dt[:19]
                    name = m.get("nome", "N/A")
                    
                    comps = []
                    for c in m.get("complementosTabelados", []):
                        comps.append(f"{c.get('nome')}: {c.get('valor')}")
                    comps_str = ", ".join(comps) if comps else ""
                    
                    movs_table.append({
                        "Data/Hora": dt,
                        "Movimentação": name,
                        "Complementos/Descrição": comps_str
                    })
                
                movs_table = sorted(movs_table, key=lambda x: x["Data/Hora"], reverse=True)
                st.dataframe(movs_table, use_container_width=True)
            else:
                st.info("Nenhuma movimentação registrada para este processo.")
        else:
            st.error(res.get("error"))