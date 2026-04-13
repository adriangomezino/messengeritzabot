"""
Cliente para OpenClaw API para integraciones avanzadas.
Conecta con https://server.itzamnaenergia.com
"""

import os
import json
import httpx
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class OpenClawClient:
    """Cliente para interactuar con OpenClaw API."""
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        """
        Inicializa el cliente de OpenClaw.
        
        Args:
            base_url: URL base de OpenClaw API. Por defecto usa variable de entorno.
            api_key: API key para autenticación (opcional).
        """
        self.base_url = base_url or os.getenv("OPENCLAW_API_URL", "https://server.itzamnaenergia.com")
        self.api_key = api_key or os.getenv("OPENCLAW_API_KEY")
        
        self.headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"
        
        self.client = httpx.AsyncClient(timeout=30.0)
        logger.info(f"OpenClawClient inicializado con URL: {self.base_url}")
    
    async def health_check(self) -> bool:
        """
        Verifica si la API de OpenClaw está funcionando.
        
        Returns:
            True si está saludable, False si no.
        """
        try:
            response = await self.client.get(f"{self.base_url}/health", headers=self.headers)
            return response.status_code == 200 and response.json().get("ok") is True
        except Exception as e:
            logger.error(f"Error en health check: {str(e)}")
            return False
    
    async def send_message(self, message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Envía un mensaje a OpenClaw para procesamiento avanzado.
        
        Args:
            message: Mensaje a procesar
            session_id: ID de sesión para mantener contexto (opcional)
            
        Returns:
            Dict con la respuesta de OpenClaw
        """
        payload = {
            "message": message,
            "session_id": session_id or f"messenger_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "metadata": {
                "source": "messenger_bot",
                "user_agent": "Itzamna-Energía-Messenger-Bot/1.0",
            }
        }
        
        try:
            logger.info(f"Enviando mensaje a OpenClaw: {message[:100]}...")
            response = await self.client.post(
                f"{self.base_url}/api/v1/message",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Respuesta recibida de OpenClaw")
            
            return {
                "success": True,
                "response": result.get("response", ""),
                "session_id": result.get("session_id"),
                "metadata": result.get("metadata", {}),
                "raw_response": result
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Error HTTP de OpenClaw: {e.response.status_code} - {e.response.text}")
            return {
                "success": False,
                "error": f"Error HTTP {e.response.status_code}",
                "response": ""
            }
        except Exception as e:
            logger.error(f"Error inesperado en OpenClaw: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": ""
            }
    
    async def create_lead(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea un nuevo lead en el sistema de OpenClaw.
        
        Args:
            lead_data: Datos del lead (nombre, teléfono, email, mensaje, etc.)
            
        Returns:
            Dict con el resultado de la creación
        """
        payload = {
            "lead": lead_data,
            "source": "messenger_bot",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            logger.info(f"Creando lead en OpenClaw: {lead_data.get('name', 'Sin nombre')}")
            response = await self.client.post(
                f"{self.base_url}/api/v1/leads",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Lead creado exitosamente: {result.get('id', 'unknown')}")
            
            return {
                "success": True,
                "lead_id": result.get("id"),
                "message": result.get("message", "Lead creado exitosamente"),
                "raw_response": result
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Error HTTP al crear lead: {e.response.status_code} - {e.response.text}")
            return {
                "success": False,
                "error": f"Error HTTP {e.response.status_code}",
                "message": "No se pudo guardar el lead. Se notificará al equipo manualmente."
            }
        except Exception as e:
            logger.error(f"Error inesperado al crear lead: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Error al procesar el lead."
            }
    
    async def schedule_appointment(self, appointment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Agenda una cita a través de OpenClaw.
        
        Args:
            appointment_data: Datos de la cita (fecha, hora, tipo, contacto, etc.)
            
        Returns:
            Dict con el resultado de la agenda
        """
        payload = {
            "appointment": appointment_data,
            "source": "messenger_bot",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            logger.info(f"Agendando cita en OpenClaw: {appointment_data.get('type', 'consulta')}")
            response = await self.client.post(
                f"{self.base_url}/api/v1/appointments",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Cita agendada exitosamente: {result.get('id', 'unknown')}")
            
            return {
                "success": True,
                "appointment_id": result.get("id"),
                "message": result.get("message", "Cita agendada exitosamente"),
                "confirmation_code": result.get("confirmation_code"),
                "raw_response": result
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Error HTTP al agendar cita: {e.response.status_code} - {e.response.text}")
            return {
                "success": False,
                "error": f"Error HTTP {e.response.status_code}",
                "message": "No se pudo agendar la cita automáticamente. Te contactaremos para coordinarla."
            }
        except Exception as e:
            logger.error(f"Error inesperado al agendar cita: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Error al procesar la cita."
            }
    
    async def get_quick_replies(self, intent: str) -> List[Dict[str, str]]:
        """
        Obtiene quick replies sugeridos basados en la intención detectada.
        
        Args:
            intent: Intención detectada (cotización, cita, info, etc.)
            
        Returns:
            Lista de quick replies para Messenger
        """
        # Respuestas predefinidas para diferentes intenciones
        quick_replies_map = {
            "cotizacion": [
                {"title": "📊 Enviar mi recibo CFE", "payload": "COTIZAR_CON_RECIBO"},
                {"title": "💬 Hablar con especialista", "payload": "HABLAR_CON_ESPECIALISTA"},
                {"title": "📅 Agendar consulta", "payload": "AGENDAR_CONSULTA"},
            ],
            "cita": [
                {"title": "✅ Confirmar cita", "payload": "CONFIRMAR_CITA"},
                {"title": "🔄 Reagendar", "payload": "REAGENDAR_CITA"},
                {"title": "❌ Cancelar", "payload": "CANCELAR_CITA"},
            ],
            "info": [
                {"title": "💰 Precios", "payload": "INFO_PRECIOS"},
                {"title": "⚡ Instalación", "payload": "INFO_INSTALACION"},
                {"title": "🛡️ Garantías", "payload": "INFO_GARANTIAS"},
                {"title": "📞 Contacto", "payload": "INFO_CONTACTO"},
            ],
            "default": [
                {"title": "💬 ¿Preguntas?", "payload": "AYUDA"},
                {"title": "📞 Contactar", "payload": "CONTACTAR"},
                {"title": "🏠 Inicio", "payload": "INICIO"},
            ]
        }
        
        return quick_replies_map.get(intent, quick_replies_map["default"])
    
    async def close(self):
        """Cierra la sesión HTTP."""
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


# Funciones de conveniencia
async def process_with_openclaw(message: str) -> str:
    """
    Procesa un mensaje con OpenClaw (si está disponible).
    
    Args:
        message: Mensaje a procesar
        
    Returns:
        Respuesta de OpenClaw o string vacío si falla
    """
    try:
        async with OpenClawClient() as client:
            # Primero verificar que OpenClaw esté disponible
            if not await client.health_check():
                logger.warning("OpenClaw no está disponible, usando solo OpenRouter")
                return ""
            
            result = await client.send_message(message)
            if result["success"] and result["response"]:
                return result["response"]
            else:
                logger.warning(f"OpenClaw no devolvió respuesta válida: {result.get('error')}")
                return ""
    except Exception as e:
        logger.error(f"Error al usar OpenClaw: {str(e)}")
        return ""


if __name__ == "__main__":
    # Ejemplo de uso
    import asyncio
    
    async def test():
        client = OpenClawClient()
        
        # Health check
        healthy = await client.health_check()
        print(f"OpenClaw saludable: {healthy}")
        
        if healthy:
            # Enviar mensaje
            response = await client.send_message("Hola, necesito información sobre paneles solares")
            print(f"Respuesta de OpenClaw: {response.get('response', 'No response')}")
        
        await client.close()
    
    asyncio.run(test())