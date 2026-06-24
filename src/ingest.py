import os
import glob
from dotenv import load_dotenv
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

# Carregar variáveis de ambiente
load_dotenv()

class DocumentIngester:
    def __init__(self, raw_data_dir: str, vector_store_dir: str):
        self.raw_data_dir = raw_data_dir
        self.vector_store_dir = vector_store_dir
        
        print("Carregando o modelo de embeddings BERTimbau (neuralmind/bert-base-portuguese-cased)...")
        # Usamos HuggingFaceEmbeddings do LangChain com o modelo BERTimbau base em português
        self.embeddings = HuggingFaceEmbeddings(
            model_name="neuralmind/bert-base-portuguese-cased",
            model_kwargs={'device': 'cpu'}  # 'cuda' se houver GPU disponível
        )
        print("Modelo de embeddings carregado com sucesso!")

    def extract_text_from_pdf(self, pdf_path: str) -> list:
        """
        Extrai o texto de um PDF mantendo controle sobre o número das páginas.
        Retorna uma lista de dicionários contendo o texto da página e metadados.
        """
        documents = []
        doc_name = os.path.basename(pdf_path)
        try:
            reader = PdfReader(pdf_path)
            for page_num, page in enumerate(reader.pages, start=1):
                text = page.extract_text()
                if text and text.strip():
                    documents.append({
                        "text": text,
                        "metadata": {
                            "source": doc_name,
                            "page": page_num
                        }
                    })
        except Exception as e:
            print(f"Erro ao ler PDF {pdf_path}: {e}")
        return documents

    def split_text_into_chunks(self, documents: list, chunk_size: int = 1000, chunk_overlap: int = 150) -> list:
        """
        Divide o texto em pedaços (chunks) menores e semanticamente coerentes,
        preservando os metadados de origem e página.
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False
        )
        
        chunks = []
        for doc in documents:
            text = doc["text"]
            metadata = doc["metadata"]
            
            # Split do texto da página
            page_chunks = text_splitter.split_text(text)
            
            for chunk in page_chunks:
                chunks.append({
                    "text": chunk,
                    "metadata": metadata
                })
        return chunks

    def create_and_persist_embeddings(self, chunks: list):
        """
        Gera os embeddings dos chunks e armazena/persiste no ChromaDB.
        """
        if not chunks:
            print("Nenhum fragmento para indexar.")
            return

        texts = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]

        print(f"Indexando {len(chunks)} fragmentos no ChromaDB...")
        
        # Inicializa o ChromaDB com persistência no diretório configurado
        db = Chroma.from_texts(
            texts=texts,
            embedding=self.embeddings,
            metadatas=metadatas,
            persist_directory=self.vector_store_dir
        )
        print(f"Banco de dados vetorial salvo com sucesso em: {self.vector_store_dir}")

    def run_ingestion(self):
        """
        Executa o pipeline completo de ingestão.
        """
        print("Iniciando processo de ingestão do Jequitibá...")
        
        # Encontrar todos os PDFs no diretório raw_data_dir
        pdf_pattern = os.path.join(self.raw_data_dir, "*.pdf")
        pdf_files = glob.glob(pdf_pattern)
        
        if not pdf_files:
            print(f"Nenhum arquivo PDF encontrado em: {self.raw_data_dir}")
            print("Adicione alguns contratos em PDF nessa pasta para prosseguir.")
            return

        all_pages = []
        for pdf_file in pdf_files:
            print(f"Processando: {os.path.basename(pdf_file)}")
            pages = self.extract_text_from_pdf(pdf_file)
            all_pages.extend(pages)
            
        print(f"Total de {len(all_pages)} páginas extraídas.")
        
        chunks = self.split_text_into_chunks(all_pages)
        print(f"Gerados {len(chunks)} fragmentos de texto.")
        
        self.create_and_persist_embeddings(chunks)
        print("Ingestão concluída com sucesso!")

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    RAW_DIR = os.path.join(BASE_DIR, "data", "raw_contracts")
    VECTOR_DIR = os.path.join(BASE_DIR, "data", "vector_store")
    
    ingester = DocumentIngester(raw_data_dir=RAW_DIR, vector_store_dir=VECTOR_DIR)
    ingester.run_ingestion()
