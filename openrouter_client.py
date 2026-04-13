"""
Cliente para OpenRouter API usando modelos gratuitos automáticamente.
Usa el endpoint especial 'openrouter/free' que selecciona el mejor modelo gratis disponible.
"""

import os
import json
import httpx
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class OpenRouterClient:
    """Cliente para interactuar con OpenRouter API usando modelos gratuitos."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa el cliente de OpenRouter.
        
        Args:
            api_key: API key de OpenRouter. Si es None, busca en variable de entorno.
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY no configurada")
        
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = os.getenv("OPENROUTER_MODEL", "openrouter/free")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://itzamnaenergia.com",  # Opcional pero recomendado
            "X-Title": "Itzamna Energía Messenger Bot",
        }
        
        self.client = httpx.AsyncClient(timeout=30.0)
        logger.info(f"OpenRouterClient inicializado con modelo: {self.model}")
    
    async def generate_response(self, message: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Genera una respuesta usando OpenRouter con modelo gratuito.
        
        Args:
            message: Mensaje del usuario
            context: Contexto adicional (historial de conversación, información de empresa, etc.)
            
        Returns:
            Dict con la respuesta generada y metadatos
        """
        # Construir prompt con contexto de Itzamna Energía
        system_prompt = self._build_system_prompt(context)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 500,
            "temperature": 0.7,
            "top_p": 0.9,
        }
        
        try:
            logger.info(f"Enviando solicitud a OpenRouter: {message[:100]}...")
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            generated_text = result["choices"][0]["message"]["content"]
            usage = result.get("usage", {})
            model_used = result.get("model", "unknown")
            
            logger.info(f"Respuesta recibida de modelo: {model_used}, tokens: {usage}")
            
            return {
                "success": True,
                "response": generated_text.strip(),
                "model": model_used,
                "usage": usage,
                "raw_response": result
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Error HTTP de OpenRouter: {e.response.status_code} - {e.response.text}")
            return {
                "success": False,
                "error": f"Error HTTP {e.response.status_code}",
                "response": "Lo siento, estoy teniendo problemas técnicos. Por favor, intenta de nuevo más tarde."
            }
        except Exception as e:
            logger.error(f"Error inesperado en OpenRouter: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": "Lo siento, ocurrió un error inesperado. Por favor, contacta con soporte."
            }
    
    def _build_system_prompt(self, additional_context: Optional[str] = None) -> str:
        """
        Construye el prompt del sistema con información de Itzamna Energía.
        
        Returns:
            String con el prompt del sistema
        """
        base_prompt = """Eres el asistente virtual de Itzamna Energía, una empresa especializada en energía solar en Mérida, Yucatán.

INFORMACIÓN DE LA EMPRESA:
- Nombre: Itzamna Energía
- Ubicación: Mérida, Yucatán, México
- Servicios: Instalación de paneles solares, mantenimiento, consultoría energética
- Ventajas: Ahorro en recibo de luz, energía limpia, financiamiento disponible
- Contacto: WhatsApp: +5219992730702

INSTRUCCIONES:
1. Sé amable, profesional y servicial
2. Responde en español mexicano natural
3. Si no sabes algo, ofrece contactar con un especialista
4. Mantén las respuestas concisas pero informativas
5. Promueve los beneficios de la energía solar
6. Pregunta por el consumo eléctrico si alguien pide cotización

RESPUESTAS TÍPICAS:
- Para saludos: "¡Hola! Soy el asistente de Itzamna Energía. ¿En qué puedo ayudarte hoy?"
- Para precios: "Los precios varían según tu consumo. ¿Podrías decirme cuánto pagas mensualmente de luz?"
- Para instalación: "El proceso toma 1-2 días. Primero hacemos un estudio gratuito de tu consumo."
- Para garantías: "Ofrecemos 25 años de garantía en paneles y 10 años en inversores."
- Para contacto: "Puedes contactarnos al WhatsApp: +5219992730702"

NO INVENTES:
- No inventes precios específicos
- No prometas plazos exactos sin consultar
- No des información técnica incorrecta
- Si no estás seguro, di "Te recomiendo hablar con nuestro especialista"

OBJETIVO: Convertir consultas en leads calificados para el equipo de ventas."""
        
        if additional_context:
            base_prompt += f"\n\nCONTEXTO ADICIONAL:\n{additional_context}"
        
        return base_prompt
    
    async def close(self):
        """Cierra la sesión HTTP."""
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


# Función de conveniencia para uso rápido
async def get_openrouter_response(message: str, api_key: Optional[str] = None) -> str:
    """
    Función de conveniencia para obtener respuesta de OpenRouter.
    
    Args:
        message: Mensaje del usuario
        api_key: API key opcional
        
    Returns:
        Respuesta generada o mensaje de error
    """
    async with OpenRouterClient(api_key) as client:
        result = await client.generate_response(message)
        return result["response"] if result["success"] else result["response"]  # Siempre devuelve texto


if __name__ == "__main__":
    # Ejemplo de uso
    import asyncio
    
    async def test():
        # Necesitas configurar OPENROUTER_API_KEY en entorno
        client = OpenRouterClient()
        response = await client.generate_response("¿Cuánto cuestan los paneles solares?")
        print(f"Modelo usado: {response.get('model')}")
        print(f"Respuesta: {response.get('response')}")
        await client.close()
    
    asyncio.run(test())