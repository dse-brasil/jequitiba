import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from src.prompts import SYSTEM_PROMPT, QA_PROMPT_TEMPLATE

# Carregar variáveis de ambiente
load_dotenv()

class JequitibaRAGEngine:
    def __init__(self, vector_store_dir: str):
        self.vector_store_dir = vector_store_dir
        
        # 1. Carregar o modelo de embeddings (deve ser o mesmo da ingestão - BERTimbau)
        print("Carregando o modelo de embeddings BERTimbau (neuralmind/bert-base-portuguese-cased) no RAG Engine...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="neuralmind/bert-base-portuguese-cased",
            model_kwargs={'device': 'cpu'}
        )
        
        # 2. Conectar ao ChromaDB
        if os.path.exists(self.vector_store_dir) and os.listdir(self.vector_store_dir):
            print(f"Conectando ao ChromaDB persistido em {self.vector_store_dir}...")
            self.db = Chroma(
                persist_directory=self.vector_store_dir,
                embedding_function=self.embeddings
            )
        else:
            print(f"Alerta: Banco de dados vetorial vazio ou inexistente em {self.vector_store_dir}")
            self.db = None
            
        # 3. Inicializar o cliente oficial da API Gemini do Google
        api_key = os.getenv("AI_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Chave de API do Gemini não encontrada. Configure AI_API_KEY ou GEMINI_API_KEY no seu arquivo .env")
        self.client = genai.Client(api_key=api_key)
        self.model_name = os.getenv("AI_MODEL") or os.getenv("GEMINI_MODEL") or "gemini-2.5-flash"
        print(f"Cliente Gemini carregado com o modelo: {self.model_name}")

    def retrieve_relevant_contexts(self, query: str, top_k: int = 4) -> list:
        """
        Consulta o ChromaDB para recuperar os trechos mais semelhantes à pergunta.
        """
        if not self.db:
            print("ChromaDB não inicializado ou sem dados.")
            return []

        # Faz a pesquisa de similaridade
        results = self.db.similarity_search(query, k=top_k)
        
        retrieved_docs = []
        for doc in results:
            retrieved_docs.append({
                "text": doc.page_content,
                "source": doc.metadata.get("source", "Desconhecido"),
                "page": doc.metadata.get("page", "N/A")
            })
        return retrieved_docs

    def format_context(self, retrieved_docs: list) -> str:
        """
        Formata os documentos recuperados em uma string estruturada para o prompt.
        """
        formatted = ""
        for i, doc in enumerate(retrieved_docs):
            formatted += f"Trecho {i+1} [Documento: {doc.get('source')} | Página: {doc.get('page')}]:\n"
            formatted += f"{doc.get('text')}\n\n"
        return formatted

    def generate_answer(self, query: str) -> dict:
        """
        Executa a busca RAG e gera a resposta fundamentada com o Gemini.
        """
        # Se o banco foi atualizado após a inicialização, recarregar a conexão
        if not self.db and os.path.exists(self.vector_store_dir) and os.listdir(self.vector_store_dir):
            self.db = Chroma(
                persist_directory=self.vector_store_dir,
                embedding_function=self.embeddings
            )

        # 1. Recuperar contextos relevantes
        retrieved_docs = self.retrieve_relevant_contexts(query)
        
        if not retrieved_docs:
            return {
                "answer": "Nenhum documento relevante foi encontrado na base de dados para responder a esta pergunta.",
                "sources": []
            }

        # 2. Formatar o contexto
        context_str = self.format_context(retrieved_docs)
        
        # 3. Montar prompt final
        prompt = QA_PROMPT_TEMPLATE.format(context=context_str, question=query)

        # 4. Chamar a API do Gemini
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.0,  # Determinístico para evitar alucinações
                )
            )
            return {
                "answer": response.text,
                "sources": retrieved_docs
            }
        except Exception as e:
            return {
                "answer": f"Erro ao gerar resposta com o modelo Gemini: {str(e)}",
                "sources": []
            }

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    VECTOR_DIR = os.path.join(BASE_DIR, "data", "vector_store")
    
    engine = JequitibaRAGEngine(vector_store_dir=VECTOR_DIR)
    # response = engine.generate_answer("Qual o prazo de aviso prévio do contrato?")
    # print(response)
