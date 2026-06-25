import os
import sys
from dotenv import load_dotenv

# Carregar variáveis de ambiente e adicionar o diretório raiz ao path
load_dotenv()
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rag_engine import JequitibaRAGEngine

def main():
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    VECTOR_DIR = os.path.join(BASE_DIR, "data", "vector_store")
    
    print("Inicializando o JequitibaRAGEngine para teste com Datajud...")
    engine = JequitibaRAGEngine(vector_store_dir=VECTOR_DIR)
    
    # Pergunta com o número do processo fornecido no exemplo
    query = "Quais são as últimas movimentações e o órgão julgador do processo 0000832-35.2018.4.01.3202?"
    print(f"\nRealizando pergunta: '{query}'")
    
    response = engine.generate_answer(query)
    
    print("\n--- RESPOSTA DO JEQUITIBÁ ---")
    print(response["answer"])
    print("\n--- FONTES RETORNADAS ---")
    for doc in response["sources"]:
        print(f"- Documento: {doc.get('source')} | Página: {doc.get('page')}")

if __name__ == "__main__":
    main()
