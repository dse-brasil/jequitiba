<div align="center">
  <img src="https://img.shields.io/badge/Research-USP%20ICMC-F7DF1E?style=for-the-badge&logo=school" alt="USP Research">
  <h1>🌳 Projeto Jequitibá</h1>
  <p>
    <b>Assistente Jurídico Inteligente Baseado em RAG e LLMs.</b>
  </p>

  <p>
    <a href="#-sobre-o-projeto">Sobre o Projeto</a> •
    <a href="#-o-simbolismo-do-jequitibá">O Simbolismo</a> •
    <a href="#-arquitetura-do-sistema">Arquitetura</a> •
    <a href="#-estrutura-do-repositório">Estrutura</a> •
    <a href="#-tech-stack">Tech Stack</a>
  </p>

  <img src="https://img.shields.io/badge/LangChain-%F0%9F%A6%9C%F0%9F%94%97-black?style=for-the-badge" alt="LangChain">
  <img src="https://img.shields.io/badge/LLM-Gemini%20%2B%20LoRA-blue?style=for-the-badge" alt="LLM">
  <img src="https://img.shields.io/badge/Vector_DB-Chroma-orange?style=for-the-badge" alt="ChromaDB">
  <img src="https://img.shields.io/badge/Focus-NLP%20%26%20Law-green?style=for-the-badge" alt="LegalTech">
</div>

---

## ⚖️ Sobre o Projeto

O **Projeto Jequitibá** é uma iniciativa de pesquisa desenvolvida no âmbito do Mestrado do Instituto de Ciências Matemáticas e de Computação (ICMC-USP), dedicada à aplicação de Inteligência Artificial para análise e interpretação de documentos jurídicos complexos. Seu principal produto é o **Legal RAG Assistant (LRA)**, um assistente jurídico contextual baseado em técnicas de Retrieval-Augmented Generation (RAG) e Grandes Modelos de Linguagem (LLMs).

A solução foi concebida para enfrentar dois dos principais desafios atuais da aplicação de LLMs ao domínio domínio jurídico: a ocorrência de alucinações e as limitações de contexto ao analisar grandes volumes documentais. Para isso, utiliza uma arquitetura baseada em RAG, na qual contratos, pareceres e outros documentos jurídicos são processados, segmentados em trechos semanticamente coerentes e armazenados em um banco vetorial. Quando uma consulta é realizada, os fragmentos mais relevantes são recuperados e utilizados como contexto para a geração da resposta, garantindo que o modelo produza informações estritamente fundamentadas nos documentos fornecidos.

Além de responder perguntas, o sistema é projetado para indicar as fontes exatas que sustentam cada afirmação, incluindo referências a cláusulas e páginas específicas. Essa característica promove transparência, auditabilidade e confiança, requisitos essenciais para aplicações no contexto jurídico.

---

## 🌳 O Simbolismo do Jequitibá

O nome **Jequitibá** foi escolhido por representar valores fundamentais para o domínio jurídico e para a própria proposta tecnológica do projeto. Considerado uma das maiores e mais longevas árvores nativas do Brasil, o jequitibá simboliza solidez, confiabilidade, permanência e acúmulo de conhecimento ao longo do tempo. 

Assim como suas raízes profundas sustentam uma estrutura robusta por séculos, o Projeto Jequitibá busca fundamentar suas respostas em evidências documentais concretas, preservando a rastreabilidade das informações e reduzindo os riscos associados à geração de conteúdo não fundamentado.

Tal como a árvore que lhe dá nome, o sistema pretende servir como uma estrutura confiável, duradoura e fundamentada para apoiar a tomada de decisão e a análise documental no contexto jurídico.

---

## 🏗️ Arquitetura do Sistema

A arquitetura do sistema segue um fluxo estruturado de ingestão, indexação, recuperação e geração de conhecimento:

1. **Ingestão:** Documentos jurídicos em formato PDF são processados e divididos em fragmentos semanticamente coerentes (chunks) usando divisores recursivos para preservar o contexto de cláusulas.
2. **Embedding:** Esses fragmentos são convertidos em representações vetoriais por meio de modelos de embeddings (BERTimbau base em português).
3. **Indexação/Vector Store:** Armazenamento dos embeddings em um banco vetorial local (ChromaDB) para recuperação rápida e eficiente.
4. **Recuperação:** Quando uma consulta é realizada, o sistema realiza uma busca de similaridade e identifica os trechos (chunks) mais relevantes.
5. **Geração:** O modelo de linguagem recebe os trechos recuperados como contexto e gera respostas estritamente baseadas nas evidências, indicando precisamente as fontes e páginas consultadas.

```mermaid
graph TD
    A[Usuário: Pergunta Jurídica] --> B(Modelo de Embedding BERTimbau)
    B --> C{Busca por Similaridade}
    D[Documentos PDF] --> E[Chunking Semântico] --> F[Geração de Embeddings] --> C
    C -->|Trechos Relevantes + Páginas| G[Prompt com Contexto Rígido]
    A --> G
    G --> H[Gemini + Adaptador LoRA]
    H --> I[Resposta Fundamentada com Citações]
```

---

## 📂 Estrutura do Repositório

```
/legal-rag-assistant
│
├── /data
│   ├── /raw_contracts       # PDFs de exemplo (Anonimizados)
│   └── /vector_store        # Banco de dados vetorial persistido (ChromaDB)
│
├── /src
│   ├── ingest.py            # Script de Chunking e Embedding (BERTimbau)
│   ├── rag_engine.py        # Lógica de Retrieval e Integração RAG (Gemini)
│   └── prompts.py           # Templates de Prompt (Engenharia de Prompt)
│
├── /app
│   └── streamlit_app.py     # Interface de Chat (Streamlit)
│
├── .env.example             # Exemplo de configuração (Chaves de API)
├── requirements.txt
└── README.md
```

---

## 🛡️ Salvaguardas contra Alucinação (Prompt Engineering)
Para garantir a confiabilidade exigida por profissionais do direito:
- **Token "Não Sei":** O modelo é explicitamente instruído a recusar respostas se o contexto recuperado não for suficiente, em vez de criar informações.
- **Rastreabilidade de Fontes:** Retorno obrigatório de metadados como número da página e nome do documento para auditoria humana.
- **Temperatura Zero:** Configuração para geração estritamente determinística das respostas.

---

## 🛠️ Tech Stack

- **Orquestração:** LangChain
- **LLM Base:** Google Gemini (via SDK `google-genai`)
- **Ajuste Fino:** PEFT / LoRA para especialização em linguagem jurídica brasileira, extração de entidades e geração de relatórios de auditoria documental.
- **Vector Database:** ChromaDB (persistência local)
- **Interface:** Streamlit
- **Embeddings:** BERTimbau (`neuralmind/bert-base-portuguese-cased`) via HuggingFace

---

## 👤 Autor

**Fernando Torres**  
Mestrando em Ciência da Computação (ICMC - USP) | Cientista de Dados Sênior  
[LinkedIn](https://www.linkedin.com/in/fertorresfs/)
