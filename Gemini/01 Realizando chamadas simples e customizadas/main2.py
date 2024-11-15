import os
import requests
import json
from dotenv import load_dotenv
from enum import Enum
from typing import Optional, List
import sys

class GeminiModel(Enum):
    GEMINI_PRO = "gemini-pro"
    GEMINI_PRO_VISION = "gemini-pro-vision"

class GeminiConfig:
    def __init__(
        self,
        model: GeminiModel = GeminiModel.GEMINI_PRO,
        temperature: float = 0.7,
        top_k: Optional[int] = None,
        top_p: Optional[float] = None,
        max_output_tokens: Optional[int] = None,
        stop_sequences: Optional[List[str]] = None
    ):
        self.model = model
        self.temperature = min(max(temperature, 0.0), 1.0)  # Limita entre 0 e 1
        self.top_k = top_k
        self.top_p = top_p
        self.max_output_tokens = max_output_tokens
        self.stop_sequences = stop_sequences or []

class GeminiAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.config = GeminiConfig()
    
    def update_config(self, **kwargs):
        """Atualiza as configurações do modelo."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

    def build_request_data(self, prompt: str) -> dict:
        """Constrói o payload da requisição com as configurações atuais."""
        data = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": self.config.temperature,
            }
        }

        # Adiciona configurações opcionais apenas se estiverem definidas
        if self.config.top_k is not None:
            data["generationConfig"]["topK"] = self.config.top_k
        
        if self.config.top_p is not None:
            data["generationConfig"]["topP"] = self.config.top_p
            
        if self.config.max_output_tokens is not None:
            data["generationConfig"]["maxOutputTokens"] = self.config.max_output_tokens
            
        if self.config.stop_sequences:
            data["generationConfig"]["stopSequences"] = self.config.stop_sequences

        return data

    def chamar_gemini(self, prompt: str) -> str:
        """Envia uma requisição para a API do Google Gemini e retorna a resposta."""
        if not self.api_key:
            return "Erro: GEMINI_API_KEY não encontrada"

        url = f"https://generativelanguage.googleapis.com/v1/models/{self.config.model.value}:generateContent?key={self.api_key}"
        
        headers = {
            "Content-Type": "application/json"
        }

        data = self.build_request_data(prompt)

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            resposta_json = response.json()
            
            if "candidates" in resposta_json:
                return resposta_json["candidates"][0]["content"]["parts"][0]["text"]
            else:
                return "Erro: Resposta inesperada do Gemini"
                
        except requests.exceptions.RequestException as e:
            if hasattr(e, 'response'):
                if e.response.status_code == 401:
                    return "Erro 401: Não autorizado. Verifique sua chave de API."
                elif e.response.status_code == 404:
                    return "Erro 404: API não encontrada."
            return f"Erro na requisição à API Gemini: {str(e)}"
        except json.JSONDecodeError:
            return "Erro: Resposta inválida do servidor"

def main():
    # Carrega as variáveis de ambiente do arquivo .env
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    load_dotenv(env_path)
    
    # Inicializa a API com a chave
    api = GeminiAPI(os.getenv("GEMINI_API_KEY"))
    
    print("Bem-vindo ao chat com Gemini! Digite 'config' para alterar configurações ou 'sair' para encerrar.")
    
    while True:
        prompt = input("\nVocê: ")
        
        if prompt.lower() == 'sair':
            print("Encerrando chat...")
            break
            
        elif prompt.lower() == 'config':
            print("\nConfigurações atuais:")
            print(f"Modelo: {api.config.model.value}")
            print(f"Temperatura: {api.config.temperature}")
            print(f"Top K: {api.config.top_k}")
            print(f"Top P: {api.config.top_p}")
            print(f"Max Output Tokens: {api.config.max_output_tokens}")
            print(f"Stop Sequences: {api.config.stop_sequences}")
            
            # Menu de configuração
            print("\nO que você deseja configurar?")
            print("1. Modelo (gemini-pro, gemini-pro-vision)")
            print("2. Temperatura (0.0 a 1.0)")
            print("3. Top K")
            print("4. Top P")
            print("5. Max Output Tokens")
            print("6. Stop Sequences")
            print("7. Voltar ao chat")
            
            opcao = input("\nEscolha uma opção (1-7): ")
            
            if opcao == "1":
                print("\nModelos disponíveis:")
                for model in GeminiModel:
                    print(f"- {model.value}")
                modelo = input("Digite o nome do modelo: ")
                try:
                    api.update_config(model=GeminiModel(modelo))
                except ValueError:
                    print("Modelo inválido!")
                    
            elif opcao == "2":
                temp = float(input("Digite a temperatura (0.0 a 1.0): "))
                api.update_config(temperature=temp)
                
            elif opcao == "3":
                top_k = int(input("Digite o valor de Top K (ou 0 para desativar): "))
                api.update_config(top_k=top_k if top_k > 0 else None)
                
            elif opcao == "4":
                top_p = float(input("Digite o valor de Top P (ou 0 para desativar): "))
                api.update_config(top_p=top_p if top_p > 0 else None)
                
            elif opcao == "5":
                max_tokens = int(input("Digite o número máximo de tokens (ou 0 para desativar): "))
                api.update_config(max_output_tokens=max_tokens if max_tokens > 0 else None)
                
            elif opcao == "6":
                sequences = input("Digite as sequências de parada separadas por vírgula (ou enter para limpar): ")
                api.update_config(stop_sequences=sequences.split(",") if sequences.strip() else [])
            
            continue

        resposta = api.chamar_gemini(prompt)
        print(f"\nGemini: {resposta}")

if __name__ == "__main__":
    main()