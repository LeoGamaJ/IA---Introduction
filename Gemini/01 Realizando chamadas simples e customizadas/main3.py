import os
import requests
import json
import base64
from dotenv import load_dotenv
from enum import Enum
from typing import Optional, List, Union, BinaryIO
from pathlib import Path
import mimetypes
import markdown
import pygments
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name, guess_lexer
from bs4 import BeautifulSoup
import tempfile
from PIL import Image
import io

# Importação condicional do PyMuPDF
try:
    import fitz  # PyMuPDF
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    print("Aviso: Suporte a PDF não está disponível. Para habilitar, instale PyMuPDF.")

class GeminiModel(Enum):
    GEMINI_PRO = "gemini-pro"
    GEMINI_PRO_VISION = "gemini-pro-vision"

class ContentType(Enum):
    TEXT = "text"
    IMAGE = "image"
    PDF = "pdf"
    HTML = "html"
    MARKDOWN = "markdown"
    CODE = "code"

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
        self.temperature = min(max(temperature, 0.0), 1.0)
        self.top_k = top_k
        self.top_p = top_p
        self.max_output_tokens = max_output_tokens
        self.stop_sequences = stop_sequences or []

class MediaHandler:
    @staticmethod
    def process_image(image_path: Union[str, BinaryIO]) -> dict:
        """Processa imagem para envio à API."""
        try:
            if isinstance(image_path, str):
                with Image.open(image_path) as img:
                    # Converter para RGB se necessário
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    # Redimensionar se a imagem for muito grande
                    max_size = 2048
                    if max(img.size) > max_size:
                        ratio = max_size / max(img.size)
                        new_size = tuple(int(dim * ratio) for dim in img.size)
                        img = img.resize(new_size, Image.Resampling.LANCZOS)
                    
                    # Converter para bytes
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format='JPEG', quality=85)
                    img_bytes = img_byte_arr.getvalue()
            else:
                img_bytes = image_path.read()

            return {
                "mime_type": "image/jpeg",
                "data": base64.b64encode(img_bytes).decode('utf-8')
            }
        except Exception as e:
            raise ValueError(f"Erro ao processar imagem: {str(e)}")

    @staticmethod
    def process_pdf(pdf_path: str) -> str:
        """Extrai texto de um arquivo PDF."""
        if not PDF_SUPPORT:
            raise ValueError("Suporte a PDF não está disponível. Instale PyMuPDF para habilitar.")
        
        text_content = []
        try:
            with fitz.open(pdf_path) as doc:
                for page in doc:
                    text_content.append(page.get_text())
            return "\n".join(text_content)
        except Exception as e:
            raise ValueError(f"Erro ao processar PDF: {str(e)}")

    @staticmethod
    def process_markdown(markdown_text: str) -> str:
        """Converte markdown para HTML."""
        try:
            return markdown.markdown(markdown_text)
        except Exception as e:
            raise ValueError(f"Erro ao processar Markdown: {str(e)}")

    @staticmethod
    def process_code(code: str, language: Optional[str] = None) -> str:
        """Aplica syntax highlighting ao código."""
        try:
            if language:
                lexer = get_lexer_by_name(language)
            else:
                lexer = guess_lexer(code)
            formatter = HtmlFormatter(style='monokai', linenos=True)
            return highlight(code, lexer, formatter)
        except Exception as e:
            raise ValueError(f"Erro ao processar código: {str(e)}")

    @staticmethod
    def process_html(html_content: str) -> str:
        """Processa e limpa HTML."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            return soup.prettify()
        except Exception as e:
            raise ValueError(f"Erro ao processar HTML: {str(e)}")

class GeminiAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.config = GeminiConfig()
        self.media_handler = MediaHandler()

    def update_config(self, **kwargs):
        """Atualiza as configurações do modelo."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

    def build_request_data(self, content: Union[str, dict, list], content_type: ContentType = ContentType.TEXT) -> dict:
        """Constrói o payload da requisição com base no tipo de conteúdo."""
        data = {
            "contents": [{
                "parts": []
            }],
            "generationConfig": {
                "temperature": self.config.temperature,
            }
        }

        # Adiciona configurações opcionais
        if self.config.top_k is not None:
            data["generationConfig"]["topK"] = self.config.top_k
        if self.config.top_p is not None:
            data["generationConfig"]["topP"] = self.config.top_p
        if self.config.max_output_tokens is not None:
            data["generationConfig"]["maxOutputTokens"] = self.config.max_output_tokens
        if self.config.stop_sequences:
            data["generationConfig"]["stopSequences"] = self.config.stop_sequences

        # Processa o conteúdo com base no tipo
        if content_type == ContentType.IMAGE:
            self.config.model = GeminiModel.GEMINI_PRO_VISION
            if isinstance(content, dict):
                data["contents"][0]["parts"].append({
                    "text": content.get("prompt", "Descreva esta imagem"),
                })
                data["contents"][0]["parts"].append({
                    "inline_data": content["image_data"]
                })
            else:
                raise ValueError("Conteúdo de imagem inválido")
        else:
            data["contents"][0]["parts"].append({"text": str(content)})

        return data

    async def process_file(self, file_path: str, content_type: Optional[ContentType] = None) -> Union[str, dict]:
        """Processa diferentes tipos de arquivo."""
        if not content_type:
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type:
                if mime_type.startswith('image/'):
                    content_type = ContentType.IMAGE
                elif mime_type == 'application/pdf':
                    content_type = ContentType.PDF
                elif mime_type in ['text/html', 'application/html']:
                    content_type = ContentType.HTML
                elif mime_type == 'text/markdown':
                    content_type = ContentType.MARKDOWN
                else:
                    content_type = ContentType.TEXT

        try:
            if content_type == ContentType.IMAGE:
                image_data = self.media_handler.process_image(file_path)
                return {
                    "type": "image",
                    "image_data": image_data
                }
            elif content_type == ContentType.PDF:
                return self.media_handler.process_pdf(file_path)
            elif content_type == ContentType.MARKDOWN:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return self.media_handler.process_markdown(f.read())
            elif content_type == ContentType.HTML:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return self.media_handler.process_html(f.read())
            elif content_type == ContentType.CODE:
                with open(file_path, 'r', encoding='utf-8') as f:
                    extension = Path(file_path).suffix[1:]
                    return self.media_handler.process_code(f.read(), extension)
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            raise ValueError(f"Erro ao processar arquivo: {str(e)}")

    async def chamar_gemini(self, content: Union[str, dict, list], content_type: ContentType = ContentType.TEXT) -> str:
        """Envia uma requisição para a API do Google Gemini e retorna a resposta."""
        if not self.api_key:
            return "Erro: GEMINI_API_KEY não encontrada"

        url = f"https://generativelanguage.googleapis.com/v1/models/{self.config.model.value}:generateContent?key={self.api_key}"
        
        headers = {
            "Content-Type": "application/json"
        }

        try:
            data = self.build_request_data(content, content_type)
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

async def main():
    # Carrega as variáveis de ambiente
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    load_dotenv(env_path)
    
    # Inicializa a API
    api = GeminiAPI(os.getenv("GEMINI_API_KEY"))
    
    print("""
Bem-vindo ao chat avançado com Gemini!
Comandos disponíveis:
- 'config': Alterar configurações
- 'arquivo': Enviar um arquivo (imagem, PDF, código, etc.)
- 'sair': Encerrar o chat
    """)
    
    while True:
        comando = input("\nVocê (texto/comando): ").lower()
        
        if comando == 'sair':
            print("Encerrando chat...")
            break
            
        elif comando == 'config':
            print("\nConfigurações atuais:")
            print(f"Modelo: {api.config.model.value}")
            print(f"Temperatura: {api.config.temperature}")
            print(f"Top K: {api.config.top_k}")
            print(f"Top P: {api.config.top_p}")
            print(f"Max Output Tokens: {api.config.max_output_tokens}")
            print(f"Stop Sequences: {api.config.stop_sequences}")
            
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
            
        elif comando == 'arquivo':
            file_path = input("Digite o caminho do arquivo: ")
            if not os.path.exists(file_path):
                print("Arquivo não encontrado!")
                continue
                
            print("\nTipos de conteúdo disponíveis:")
            for content_type in ContentType:
                print(f"- {content_type.value}")
            
            content_type_str = input("Digite o tipo de conteúdo (ou enter para autodetectar): ").lower()
            content_type = ContentType(content_type_str) if content_type_str else None
            
            try:
                processed_content = await api.process_file(file_path, content_type)
                
                if isinstance(processed_content, dict) and processed_content.get("type") == "image":
                    prompt = input("Digite uma descrição ou pergunta sobre a imagem: ")
                    processed_content["prompt"] = prompt
                    response = await api.chamar_gemini(processed_content, ContentType.IMAGE)
                else:
                    response = await api.chamar_gemini(processed_content, content_type or ContentType.TEXT)
                
                print(f"\nGemini: {response}")
                
            except Exception as e:
                print(f"Erro ao processar arquivo: {str(e)}")
            
        else:
            response = await api.chamar_gemini(comando)
            print(f"\nGemini: {response}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())