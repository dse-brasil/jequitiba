"""
streamlit_app.py - Interface do Projeto Jequitibá (versão avançada com Material Design)
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
logo_path = os.path.join(BASE_DIR, "logo_jequitiba.png")

st.set_page_config(
    page_title="Projeto Jequitibá - Assistente Jurídico",
    page_icon=logo_path if os.path.exists(logo_path) else "🌳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================
# CONFIGURAÇÕES DE DESIGN (MATERIAL DESIGN E CSS PERSONALIZADO)
# ============================
st.markdown(
    """
    <!-- Fonte e Ícones do Google -->
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" rel="stylesheet">
    
    <style>
    /* Estilização Geral com a fonte Outfit */
    html, body, [class*="css"], .stMarkdown, p, div, label {
        font-family: 'Outfit', sans-serif !important;
    }
    
    /* Classe para ícones do Material Design */
    .material-symbols-outlined {
        vertical-align: middle;
        margin-right: 6px;
        display: inline-block;
    }
    
    /* Títulos e Headers */
    .app-title {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        padding: 0;
        background: linear-gradient(45deg, #1b5e20, #4caf50);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .app-subtitle {
        font-size: 1.1rem;
        color: #757575;
        margin-top: 5px;
        margin-bottom: 20px;
    }
    
    /* Elemento da logo com animação suave de flutuação */
    .logo-container {
        animation: float 4s ease-in-out infinite;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    @keyframes float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-6px); }
        100% { transform: translateY(0px); }
    }
    
    /* Estilização dos Expanders (Fontes e Chunks) */
    div[data-testid="stExpander"] {
        border: 1px solid rgba(46, 125, 50, 0.15);
        background-color: rgba(46, 125, 50, 0.02);
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
        transition: all 0.3s ease;
    }
    div[data-testid="stExpander"]:hover {
        border-color: rgba(46, 125, 50, 0.4);
        background-color: rgba(46, 125, 50, 0.04);
        box-shadow: 0 6px 18px rgba(46, 125, 50, 0.08);
    }
    
    /* Botões personalizados com micro-animações */
    button[kind="secondary"] {
        border-radius: 8px !important;
        border: 1px solid rgba(46, 125, 50, 0.3) !important;
        background-color: transparent !important;
        font-weight: 600 !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    button[kind="secondary"]:hover {
        transform: translateY(-2px);
        border-color: #2e7d32 !important;
        color: #2e7d32 !important;
        box-shadow: 0 4px 10px rgba(46, 125, 50, 0.12) !important;
    }
    button[kind="secondary"]:active {
        transform: translateY(0);
    }
    
    /* Alinhamento de status de sucesso e erro */
    .status-active {
        color: #2e7d32;
        font-weight: 500;
        display: flex;
        align-items: center;
        margin-top: 10px;
    }
    .status-inactive {
        color: #c62828;
        font-weight: 500;
        display: flex;
        align-items: center;
        margin-top: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
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

def format_sources(sources: List[Dict]) -> str:
    """Formata as fontes para exibição amigável usando ícone Material."""
    if not sources:
        return "<span class='material-symbols-outlined' style='font-size: 16px; color:#c62828;'>info</span> Nenhuma fonte específica foi utilizada."
    lines = []
    for idx, doc in enumerate(sources, 1):
        source = doc.get("source", "Documento desconhecido")
        page = doc.get("page", "N/A")
        score = doc.get("score", None)
        score_str = f" (similaridade: {score:.3f})" if score is not None else ""
        lines.append(f"{idx}. <span class='material-symbols-outlined' style='font-size:16px; color:#2e7d32;'>description</span> **{source}** - Página {page}{score_str}")
    return "\n".join(lines)

def display_chunks(chunks: List[Dict]):
    """Exibe os trechos recuperados de forma destacada com ícone Material."""
    if not chunks:
        return
    with st.expander("📄 Trechos recuperados (usados para gerar a resposta)"):
        for i, chunk in enumerate(chunks):
            score = chunk.get("score", 0)
            st.markdown(f"<span class='material-symbols-outlined' style='color:#2e7d32;'>article</span> **Trecho {i+1}** (similaridade: {score:.3f})", unsafe_allow_html=True)
            st.markdown(f"> {chunk.get('text', '')[:500]}...")
            st.caption(f"Fonte: {chunk.get('source', '')} - Pág. {chunk.get('page', '')}")
            st.divider()

# ============================
# INTERFACE PRINCIPAL - HEADER
# ============================
col1, col2 = st.columns([1, 6])
with col1:
    if os.path.exists(logo_path):
        st.markdown(
            f'<div class="logo-container"><img src="data:image/png;base64,{st.image(logo_path, width=120)}" style="display:none;"/>'
            f'<img src="app/static/logo_jequitiba.png" class="logo-img" style="width:100px; height:auto;" onerror="this.onerror=null; this.src=\'https://fonts.gstatic.com/s/i/short-term/release/materialsymbolsoutlined/forest/default/48px.svg\';"/></div>',
            # Se o path relativo falhar no Streamlit, renderizamos a imagem local normalmente:
            unsafe_allow_html=True
        )
        st.image(logo_path, width=100) # Exibição padrão segura do Streamlit
    else:
        st.markdown("<h1><span class='material-symbols-outlined' style='font-size: 48px; color: #2e7d32;'>forest</span></h1>", unsafe_allow_html=True)
with col2:
    st.markdown("<h1 class='app-title'>Projeto Jequitibá</h1>", unsafe_allow_html=True)
    st.markdown("<p class='app-subtitle'>Assistente Jurídico Inteligente com RAG e LLMs</p>", unsafe_allow_html=True)

st.markdown("---")

# ============================
# SIDEBAR - CONFIGURAÇÕES
# ============================
with st.sidebar:
    st.image("https://img.shields.io/badge/USP%20ICMC-F7DF1E?style=for-the-badge&logo=school", width=180)
    
    st.markdown("<h3><span class='material-symbols-outlined'>settings</span> Parâmetros do RAG</h3>", unsafe_allow_html=True)
    
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
    
    # Seletor de modelo
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
    
    # Mostrar status do engine com Material Icons
    if engine:
        st.markdown("<div class='status-active'><span class='material-symbols-outlined'>check_circle</span> Motor RAG ativo</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='status-inactive'><span class='material-symbols-outlined'>cancel</span> Motor RAG indisponível</div>", unsafe_allow_html=True)
    
    st.divider()
    
    st.markdown("<h3><span class='material-symbols-outlined'>upload_file</span> Upload de Documentos</h3>", unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        "Adicione novos PDFs para indexar (experimental)",
        type=["pdf"],
        accept_multiple_files=True,
        key="file_uploader",
    )
    if uploaded_files:
        st.info("Funcionalidade em desenvolvimento: os arquivos serão indexados em breve.")
    
    st.divider()
    
    st.markdown("<h3><span class='material-symbols-outlined'>analytics</span> Estatísticas</h3>", unsafe_allow_html=True)
    st.metric("Perguntas feitas", len(st.session_state.messages) // 2)
    st.caption(f"ID da conversa: {st.session_state.conversation_id}")
    
    if st.button("Nova Conversa"):
        st.session_state.messages = []
        st.session_state.conversation_id = hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]
        st.rerun()
    
    st.divider()
    st.markdown("""
    **Sobre o Jequitibá**  
    Recupera trechos de documentos jurídicos via embeddings vetoriais e gera respostas fundamentadas, com rastreabilidade total.
    
    [Repositório no GitHub](https://github.com/dse-brasil/jequitiba)
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
                    with st.spinner("Jequitibá está analisando os documentos..."):
                        # Ícone customizado de processamento
                        st.markdown("<p style='color:#2e7d32;'><span class='material-symbols-outlined'>forest</span> Buscando e interpretando evidências...</p>", unsafe_allow_html=True)
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
                    answer = f"<span class='material-symbols-outlined' style='color:#c62828;'>warning</span> Ocorreu um erro ao processar sua pergunta: {str(e)}"
                    sources = []
                    chunks = []
            else:
                answer = "<span class='material-symbols-outlined' style='color:#c62828;'>error</span> Sistema indisponível. Verifique a configuração do RAG Engine e as chaves de API."
                sources = []

            # Exibir resposta
            full_response = answer
            message_placeholder.markdown(full_response, unsafe_allow_html=True)

            # Exibir trechos recuperados (se houver)
            if chunks:
                display_chunks(chunks)

            # Exibir fontes
            if sources:
                with st.expander("📚 Ver fontes consultadas (detalhadas)"):
                    st.markdown(format_sources(sources), unsafe_allow_html=True)
                    st.markdown(f"<p style='font-size: 12px; color: #757575;'><span class='material-symbols-outlined' style='font-size:14px;'>schedule</span> Tempo de resposta: {duration:.2f}s</p>", unsafe_allow_html=True)
            else:
                st.markdown("<p style='font-size: 12px; color: #757575;'><span class='material-symbols-outlined' style='font-size:14px;'>info</span> Nenhuma fonte específica foi citada.</p>", unsafe_allow_html=True)

            # Salvar no histórico
            st.session_state.messages.append({
                "role": "assistant",
                "content": full_response,
                "sources": sources,
                "chunks": chunks,
            })
            st.rerun()

with tab_datajud:
    st.markdown("## <span class='material-symbols-outlined' style='font-size:28px;'>find_in_page</span> Consulta Direta ao Datajud (CNJ)", unsafe_allow_html=True)
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
            
            st.markdown(f"<p class='status-active'><span class='material-symbols-outlined'>check_circle</span> Processo localizado no index <strong>{court}</strong>!</p>", unsafe_allow_html=True)
            
            col_info1, col_info2 = st.columns(2)
            with col_info1:
                st.markdown(f"<span class='material-symbols-outlined' style='font-size:18px;'>fingerprint</span> **Número CNJ:** `{dj_client.format_cnj_number(proc_data.get('numeroProcesso', ''))}`", unsafe_allow_html=True)
                st.markdown(f"<span class='material-symbols-outlined' style='font-size:18px;'>account_balance</span> **Tribunal/Index:** `{court}`", unsafe_allow_html=True)
                st.markdown(f"<span class='material-symbols-outlined' style='font-size:18px;'>gavel</span> **Classe Processual:** {proc_data.get('classe', {}).get('nome', 'N/A')} (Código: {proc_data.get('classe', {}).get('codigo', 'N/A')})", unsafe_allow_html=True)
                st.markdown(f"<span class='material-symbols-outlined' style='font-size:18px;'>layers</span> **Grau de Jurisdição:** `{proc_data.get('grau', 'N/A')}`", unsafe_allow_html=True)
            with col_info2:
                st.markdown(f"<span class='material-symbols-outlined' style='font-size:18px;'>groups</span> **Órgão Julgador:** {proc_data.get('orgaoJulgador', {}).get('nome', 'N/A')} (Código: {proc_data.get('orgaoJulgador', {}).get('codigo', 'N/A')})", unsafe_allow_html=True)
                st.markdown(f"<span class='material-symbols-outlined' style='font-size:18px;'>calendar_month</span> **Data de Ajuizamento:** {proc_data.get('dataAjuizamento', '').split('T')[0] if proc_data.get('dataAjuizamento') else 'N/A'}", unsafe_allow_html=True)
                st.markdown(f"<span class='material-symbols-outlined' style='font-size:18px;'>computer</span> **Sistema Eletrônico:** {proc_data.get('sistema', {}).get('nome', 'N/A')}", unsafe_allow_html=True)
                st.markdown(f"<span class='material-symbols-outlined' style='font-size:18px;'>article</span> **Formato:** {proc_data.get('formato', {}).get('nome', 'N/A')}", unsafe_allow_html=True)
                
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
            st.markdown(f"<span class='material-symbols-outlined' style='font-size:18px;'>label</span> **Assuntos:** {', '.join(assuntos_list) if assuntos_list else 'N/A'}", unsafe_allow_html=True)
            
            # Movimentações
            st.markdown("### <span class='material-symbols-outlined'>history</span> Linha do Tempo de Movimentações", unsafe_allow_html=True)
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