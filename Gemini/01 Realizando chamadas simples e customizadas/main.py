import os
import requests
import json
from dotenv import load_dotenv
import sys

# Carrega as variáveis de ambiente do arquivo .env
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

def chamar_gemini(prompt):
    """Envia uma requisição para a API do Google Gemini e retorna a resposta."""
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Erro: GEMINI_API_KEY não encontrada no arquivo .env"

    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={api_key}"
    
    headers = {
        "Content-Type": "application/json"
    }

    data = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        
        try:
            resposta_json = response.json()
            
            if "candidates" in resposta_json:
                return resposta_json["candidates"][0]["content"]["parts"][0]["text"]
            else:
                return "Erro: Resposta inesperada do Gemini"
                
        except json.JSONDecodeError:
            return "Erro: Resposta inválida do servidor"

    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response'):
            if e.response.status_code == 401:
                return "Erro 401: Não autorizado. Verifique sua chave de API."
            elif e.response.status_code == 404:
                return "Erro 404: API não encontrada."
        return f"Erro na requisição à API Gemini: {str(e)}"

def main():
    print("Bem-vindo ao chat com Gemini! Digite 'sair' para encerrar.")
    
    while True:
        prompt = input("\nVocê: ")
        if prompt.lower() == 'sair':
            print("Encerrando chat...")
            break

        resposta = chamar_gemini(prompt)
        print(f"\nGemini: {resposta}")

if __name__ == "__main__":
    main()