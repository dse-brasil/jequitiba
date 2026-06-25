import os
import requests
import re
from typing import Dict, Any, Optional, List

# Chave pública vigente do Datajud (CNJ) fornecida
DEFAULT_API_KEY = "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="

class DatajudClient:
    def __init__(self):
        # Permite carregar do .env ou usar a chave padrão
        self.api_key = os.getenv("DATAJUD_API_KEY", DEFAULT_API_KEY)
        self.base_url = "https://api-publica.datajud.cnj.jus.br"

    def detect_court_alias(self, process_number: str) -> Optional[str]:
        """
        Detecta o alias do tribunal a partir do número único do processo (CNJ).
        Formato CNJ: NNNNNNN-DD.YYYY.J.TR.OOOO
        J = segmento de justiça (15º dígito, índice 13 da string limpa)
        TR = tribunal/região (16º e 17º dígitos, índices 14-15 da string limpa)
        """
        # Limpar formatação
        num = "".join(filter(str.isdigit, process_number))
        if len(num) != 20:
            return None
        
        j = int(num[13])
        tr = int(num[14:16])
        
        # Segmento de Justiça Federal (TRFs)
        if j == 4:
            return f"api_publica_trf{tr}"
        
        # Segmento de Justiça do Trabalho (TRTs)
        elif j == 5:
            return f"api_publica_trt{tr}"
        
        # Segmento de Justiça Eleitoral (TREs)
        elif j == 6:
            tre_map = {
                1: "tre-ac", 2: "tre-al", 3: "tre-am", 4: "tre-ap", 5: "tre-ba",
                6: "tre-ce", 7: "tre-dft", 8: "tre-es", 9: "tre-go", 10: "tre-ma",
                11: "tre-mg", 12: "tre-ms", 13: "tre-mt", 14: "tre-pa", 15: "tre-pb",
                16: "tre-pe", 17: "tre-pi", 18: "tre-pr", 19: "tre-rj", 20: "tre-rn",
                21: "tre-ro", 22: "tre-rr", 23: "tre-rs", 24: "tre-sc", 25: "tre-se",
                26: "tre-sp", 27: "tre-to"
            }
            alias = tre_map.get(tr)
            return f"api_publica_{alias}" if alias else None
            
        # Segmento de Justiça Estadual (TJs)
        elif j == 8:
            tj_map = {
                1: "tjac", 2: "tjal", 3: "tjam", 4: "tjap", 5: "tjba",
                6: "tjce", 7: "tjdft", 8: "tjes", 9: "tjgo", 10: "tjma",
                11: "tjmg", 12: "tjms", 13: "tjmt", 14: "tjpa", 15: "tjpb",
                16: "tjpe", 17: "tjpi", 18: "tjpr", 19: "tjrj", 20: "tjrn",
                21: "tjro", 22: "tjrr", 23: "tjrs", 24: "tjsc", 25: "tjse",
                26: "tjsp", 27: "tjto"
            }
            alias = tj_map.get(tr)
            return f"api_publica_{alias}" if alias else None
            
        # Segmento de Justiça Militar Estadual (TJMs)
        elif j == 9:
            tjm_map = {
                11: "tjmmg", 23: "tjmrs", 26: "tjmsp"
            }
            alias = tjm_map.get(tr)
            return f"api_publica_{alias}" if alias else None
            
        # Tribunais Superiores
        elif j == 3:  # STJ
            if tr == 0:
                return "api_publica_stj"
        elif j == 1:  # STF / TST
            if tr == 0:
                # No Datajud, alguns são específicos
                pass
                
        return None

    def query_process(self, process_number: str, court_alias: Optional[str] = None) -> Dict[str, Any]:
        """
        Consulta os metadados de um processo público no Datajud.
        """
        # Limpar formatação
        clean_number = "".join(filter(str.isdigit, process_number))
        
        # Tenta detectar o tribunal se não for fornecido
        alias = court_alias or self.detect_court_alias(clean_number)
        if not alias:
            return {
                "success": False,
                "error": "Não foi possível identificar o tribunal a partir do número do processo. Certifique-se de que é um número CNJ de 20 dígitos válido."
            }

        url = f"{self.base_url}/{alias}/_search"
        
        headers = {
            "Authorization": f"APIKey {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "query": {
                "match": {
                    "numeroProcesso": clean_number
                }
            }
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=12)
            if response.status_code == 200:
                data = response.json()
                hits = data.get("hits", {}).get("hits", [])
                if hits:
                    process_source = hits[0].get("_source", {})
                    return {
                        "success": True,
                        "data": process_source,
                        "court": alias.replace("api_publica_", "").upper()
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Processo não encontrado no tribunal '{alias.replace('api_publica_', '').upper()}'."
                    }
            elif response.status_code in [401, 403]:
                return {
                    "success": False,
                    "error": "Chave de API do Datajud inválida ou expirada. Verifique as configurações."
                }
            else:
                return {
                    "success": False,
                    "error": f"Erro na API do Datajud (HTTP {response.status_code}): {response.text}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro de conexão com o Datajud: {str(e)}"
            }

    @staticmethod
    def format_process_info(data: Dict[str, Any], court_name: str) -> str:
        """
        Formata os metadados do processo em um resumo textual limpo e legível.
        """
        num_formatado = DatajudClient.format_cnj_number(data.get("numeroProcesso", ""))
        classe = data.get("classe", {}).get("nome", "Não informada")
        orgao = data.get("orgaoJulgador", {}).get("nome", "Não informado")
        data_ajuizamento = data.get("dataAjuizamento", "")
        if data_ajuizamento:
            # Simplificar data ISO
            data_ajuizamento = data_ajuizamento.split("T")[0]
            
        assuntos_list = []
        assuntos_raw = data.get("assuntos", [])
        for a in assuntos_raw:
            if isinstance(a, list):
                for item in a:
                    if isinstance(item, dict) and "nome" in item:
                        assuntos_list.append(item["nome"])
            elif isinstance(a, dict) and "nome" in a:
                assuntos_list.append(a["nome"])
        assuntos = ", ".join(assuntos_list) if assuntos_list else "Não informado"
        
        # Movimentações
        movs = data.get("movimentos", [])
        # Ordenar movimentos por data descrescente para ter a mais recente primeiro
        movs_sorted = sorted(movs, key=lambda x: x.get("dataHora", ""), reverse=True)
        
        movs_formatted = []
        for m in movs_sorted[:5]:  # Mostrar as 5 mais recentes
            dt = m.get("dataHora", "").split("T")[0]
            nome_mov = m.get("nome", "Movimentação")
            movs_formatted.append(f"- {dt}: {nome_mov}")
            
        movs_text = "\n".join(movs_formatted) if movs_formatted else "Nenhuma movimentação registrada"

        text = (
            f"=== METADADOS DO PROCESSO JUDICIAL ===\n"
            f"Número do Processo: {num_formatado}\n"
            f"Tribunal: {court_name}\n"
            f"Classe Processual: {classe}\n"
            f"Órgão Julgador: {orgao}\n"
            f"Data de Ajuizamento: {data_ajuizamento}\n"
            f"Assuntos: {assuntos}\n"
            f"\nÚltimas Movimentações Processuais:\n{movs_text}\n"
            f"======================================"
        )
        return text

    @staticmethod
    def format_cnj_number(num: str) -> str:
        """Formata string numérica de 20 dígitos no formato CNJ NNNNNNN-DD.YYYY.J.TR.OOOO"""
        clean = "".join(filter(str.isdigit, num))
        if len(clean) != 20:
            return num
        return f"{clean[0:7]}-{clean[7:9]}.{clean[9:13]}.{clean[13:14]}.{clean[14:16]}.{clean[16:20]}"

    @staticmethod
    def extract_cnj_numbers(text: str) -> List[str]:
        """Extrai números de processos CNJ (20 dígitos unificados ou formatados) do texto"""
        pattern = r'\b\d{7}[-]?\d{2}[-.]?\d{4}[-.]?\d{1}[-.]?\d{2}[-.]?\d{4}\b'
        matches = re.findall(pattern, text)
        return ["".join(filter(str.isdigit, m)) for m in matches]
