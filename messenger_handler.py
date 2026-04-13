"""
Manejador de webhooks de Meta Messenger.
Procesa eventos de Messenger y genera respuestas.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from openrouter_client import OpenRouterClient
from openclaw_client import OpenClawClient, process_with_openclaw

logger = logging.getLogger(__name__)


class MessengerHandler:
    """Manejador principal para eventos de Messenger."""
    
    def __init__(self):
        """Inicializa el manejador de Messenger."""
        self.verify_token = os.getenv("META_VERIFY_TOKEN")
        self.page_access_token = os.getenv("META_PAGE_ACCESS_TOKEN")
        
        if not self.verify_token or not self.page_access_token:
            logger.warning("Tokens de Meta no configurados completamente")
        
        self.openrouter_client = None
        self.openclaw_client = None
        self.user_sessions = {}  # Simple almacenamiento en memoria de sesiones
        
        logger.info("MessengerHandler inicializado")
    
    async def initialize(self):
        """Inicializa los clientes asíncronos."""
        self.openrouter_client = OpenRouterClient()
        self.openclaw_client = OpenClawClient()
    
    async def handle_webhook_verification(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """
        Maneja la verificación del webhook de Meta.
        
        Args:
            mode: Modo de verificación ('subscribe')
            token: Token de verificación
            challenge: Challenge de verificación
            
        Returns:
            Challenge si la verificación es exitosa, None si falla
        """
        if mode == "subscribe" and token == self.verify_token:
            logger.info("Webhook verificado exitosamente")
            return challenge
        else:
            logger.warning(f"Fallo verificación webhook: mode={mode}, token={token}")
            return None
    
    async def handle_message(self, sender_id: str, message_text: str, 
                           message_id: str, timestamp: int) -> Dict[str, Any]:
        """
        Maneja un mensaje entrante de usuario.
        
        Args:
            sender_id: ID del remitente en Messenger
            message_text: Texto del mensaje
            message_id: ID único del mensaje
            timestamp: Timestamp del mensaje
            
        Returns:
            Dict con la respuesta a enviar
        """
        logger.info(f"Mensaje recibido de {sender_id}: {message_text[:100]}...")
        
        # Inicializar sesión de usuario si no existe
        if sender_id not in self.user_sessions:
            self.user_sessions[sender_id] = {
                "created_at": datetime.now().isoformat(),
                "message_count": 0,
                "last_message": None,
                "context": "",
                "intent": None
            }
        
        session = self.user_sessions[sender_id]
        session["message_count"] += 1
        session["last_message"] = message_text
        session["last_active"] = datetime.now().isoformat()
        
        # Determinar intención básica
        intent = self._detect_intent(message_text)
        session["intent"] = intent
        
        # Generar respuesta
        response = await self._generate_response(message_text, sender_id, intent, session)
        
        # Actualizar contexto de sesión
        session["context"] += f"Usuario: {message_text}\nAsistente: {response['text']}\n"
        
        # Limitar tamaño del contexto
        if len(session["context"]) > 2000:
            session["context"] = session["context"][-2000:]
        
        logger.info(f"Respuesta generada para {sender_id}: {response['text'][:100]}...")
        
        return response
    
    def _detect_intent(self, message: str) -> str:
        """
        Detecta la intención del mensaje del usuario.
        
        Args:
            message: Mensaje del usuario
            
        Returns:
            String con la intención detectada
        """
        message_lower = message.lower()
        
        # Palabras clave para diferentes intenciones
        if any(word in message_lower for word in ["precio", "cuesta", "cuánto", "valor", "inversión"]):
            return "cotizacion"
        elif any(word in message_lower for word in ["cita", "agendar", "reunión", "consulta", "visita"]):
            return "cita"
        elif any(word in message_lower for word in ["hola", "buenas", "saludos", "hi", "hello"]):
            return "saludo"
        elif any(word in message_lower for word in ["instalar", "instalación", "montar", "colocar"]):
            return "instalacion"
        elif any(word in message_lower for word in ["garantía", "garantias", "seguro", "protección"]):
            return "garantia"
        elif any(word in message_lower for word in ["contacto", "teléfono", "whatsapp", "email", "correo"]):
            return "contacto"
        elif any(word in message_lower for word in ["gracias", "thank you", "merci"]):
            return "agradecimiento"
        else:
            return "consulta_general"
    
    async def _generate_response(self, message: str, sender_id: str, 
                               intent: str, session: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera una respuesta para el mensaje del usuario.
        
        Args:
            message: Mensaje del usuario
            sender_id: ID del remitente
            intent: Intención detectada
            session: Datos de la sesión
            
        Returns:
            Dict con la respuesta y metadatos
        """
        try:
            # Primero intentar con OpenClaw para respuestas avanzadas
            openclaw_response = await process_with_openclaw(message)
            
            if openclaw_response:
                logger.info(f"Usando respuesta de OpenClaw para {sender_id}")
                response_text = openclaw_response
                source = "openclaw"
            else:
                # Usar OpenRouter para respuestas generativas
                if not self.openrouter_client:
                    await self.initialize()
                
                context = session.get("context", "")
                result = await self.openrouter_client.generate_response(message, context)
                
                if result["success"]:
                    response_text = result["response"]
                    source = f"openrouter:{result.get('model', 'unknown')}"
                else:
                    # Respuesta de fallback
                    response_text = self._get_fallback_response(intent)
                    source = "fallback"
                    logger.error(f"Error de OpenRouter: {result.get('error')}")
            
            # Construir respuesta completa
            response = {
                "text": response_text,
                "metadata": {
                    "sender_id": sender_id,
                    "intent": intent,
                    "source": source,
                    "timestamp": datetime.now().isoformat(),
                    "message_count": session["message_count"]
                }
            }
            
            # Agregar quick replies según la intención
            if self.openclaw_client:
                quick_replies = await self.openclaw_client.get_quick_replies(intent)
                if quick_replies:
                    response["quick_replies"] = quick_replies
            
            return response
            
        except Exception as e:
            logger.error(f"Error generando respuesta: {str(e)}")
            return {
                "text": self._get_fallback_response(intent),
                "metadata": {
                    "sender_id": sender_id,
                    "intent": intent,
                    "source": "error_fallback",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            }
    
    def _get_fallback_response(self, intent: str) -> str:
        """
        Obtiene una respuesta de fallback basada en la intención.
        
        Args:
            intent: Intención detectada
            
        Returns:
            Respuesta de fallback
        """
        fallback_responses = {
            "cotizacion": "¡Hola! Para darte una cotización precisa necesito saber tu consumo de luz. ¿Podrías compartir cuánto pagas mensualmente en tu recibo CFE? O si prefieres, puedes enviarme una foto de tu recibo.",
            "cita": "¡Claro! Puedo ayudarte a agendar una consulta. ¿Prefieres una llamada telefónica o una visita en persona? También necesito saber tu disponibilidad de horario.",
            "saludo": "¡Hola! 👋 Soy el asistente virtual de Itzamna Energía. Estoy aquí para ayudarte con información sobre energía solar, cotizaciones o agendar consultas. ¿En qué puedo asistirte hoy?",
            "instalacion": "El proceso de instalación de paneles solares normalmente toma 1-2 días. Incluye: evaluación de tu techo, instalación de paneles e inversor, y conexión a CFE. Ofrecemos garantía de 25 años en paneles.",
            "garantia": "En Itzamna Energía ofrecemos: 25 años de garantía en paneles, 10 años en inversores, y 5 años en mano de obra. Todo respaldado por certificaciones internacionales.",
            "contacto": "Puedes contactarnos por:\n📱 WhatsApp: +5219992730702\n📧 Email: info@itzamnaenergia.com\n📍 Oficina: Mérida, Yucatán\nHorario: Lunes a Viernes 9am-6pm",
            "agradecimiento": "¡Gracias a ti! 😊 Estoy aquí para ayudarte cuando lo necesites. No dudes en contactarme si tienes más preguntas sobre energía solar.",
            "consulta_general": "Entiendo que tienes una pregunta sobre energía solar. ¿Podrías darme más detalles para poder ayudarte mejor? Por ejemplo: ¿quieres saber sobre precios, instalación, financiamiento o algo específico?"
        }
        
        return fallback_responses.get(intent, fallback_responses["consulta_general"])
    
    async def handle_postback(self, sender_id: str, payload: str, timestamp: int) -> Dict[str, Any]:
        """
        Maneja un postback (botón, quick reply) de Messenger.
        
        Args:
            sender_id: ID del remitente
            payload: Payload del postback
            timestamp: Timestamp del evento
            
        Returns:
            Dict con la respuesta a enviar
        """
        logger.info(f"Postback recibido de {sender_id}: {payload}")
        
        # Mapeo de payloads a respuestas
        postback_responses = {
            "COTIZAR_CON_RECIBO": "¡Perfecto! Para cotizar con tu recibo CFE, puedes enviarme una foto del recibo o decirme:\n1. Tu consumo mensual en kWh\n2. El monto que pagas aproximadamente\n3. Tu municipio en Yucatán",
            "HABLAR_CON_ESPECIALISTA": "Te conectaré con un especialista. Por favor, comparte tu número de WhatsApp para que te contacten:",
            "AGENDAR_CONSULTA": "Vamos a agendar tu consulta. ¿Prefieres:\n• Llamada telefónica\n• Videollamada\n• Visita en persona\n\nY ¿cuál es tu disponibilidad?",
            "INFO_PRECIOS": "Los precios varían según tu consumo. En promedio:\n• Sistema básico (2-3kW): $40,000 - $60,000 MXN\n• Sistema medio (4-5kW): $70,000 - $90,000 MXN\n• Sistema grande (6kW+): $100,000+ MXN\n\n¡Tenemos financiamiento disponible!",
            "INFO_INSTALACION": "Proceso de instalación:\n1. Estudio gratuito de tu consumo\n2. Diseño del sistema\n3. Instalación (1-2 días)\n4. Trámites con CFE\n5. Puesta en marcha\n\nGarantía de 25 años en paneles.",
            "INFO_GARANTIAS": "🔒 Nuestras garantías:\n• Paneles: 25 años\n• Inversores: 10 años\n• Mano de obra: 5 años\n• Certificaciones internacionales\n• Seguro contra granizo y viento",
            "INFO_CONTACTO": "📞 Contacto Itzamna Energía:\nWhatsApp: +5219992730702\nEmail: info@itzamnaenergia.com\nUbicación: Mérida, Yucatán\nHorario: L-V 9am-6pm",
            "AYUDA": "¿En qué más puedo ayudarte? Puedo:\n• Dar cotizaciones\n• Agendar consultas\n• Informar sobre instalación\n• Explicar garantías\n• Proporcionar contacto\n\nSolo dime qué necesitas 😊",
            "CONTACTAR": "Puedes contactarnos directamente:\n📱 WhatsApp: +5219992730702\n📧 Email: info@itzamnaenergia.com\n\nEstamos aquí para ayudarte.",
            "INICIO": "¡Hola de nuevo! 👋 Soy el asistente de Itzamna Energía. ¿En qué puedo ayudarte hoy?\n\nPuedo asistirte con: cotizaciones, citas, información técnica o contacto directo."
        }
        
        response_text = postback_responses.get(payload, "Lo siento, no reconozco esa opción. ¿En qué más puedo ayudarte?")
        
        return {
            "text": response_text,
            "metadata": {
                "sender_id": sender_id,
                "postback": payload,
                "timestamp": datetime.now().isoformat(),
                "source": "postback_handler"
            }
        }
    
    async def cleanup_old_sessions(self, max_age_hours: int = 24):
        """
        Limpia sesiones antiguas para liberar memoria.
        
        Args:
            max_age_hours: Máxima antigüedad en horas para mantener sesiones
        """
        now = datetime.now()
        expired_sessions = []
        
        for sender_id, session in self.user_sessions.items():
            last_active_str = session.get("last_active")
            if last_active_str:
                last_active = datetime.fromisoformat(last_active_str)
                age_hours = (now - last_active).total_seconds() / 3600
                
                if age_hours > max_age_hours:
                    expired_sessions.append(sender_id)
        
        for sender_id in expired_sessions:
            del self.user_sessions[sender_id]
        
        if expired_sessions:
            logger.info(f"Limpiadas {len(expired_sessions)} sesiones expiradas")
    
    async def close(self):
        """Cierra los clientes y libera recursos."""
        if self.openrouter_client:
            await self.openrouter_client.close()
        if self.openclaw_client:
            await self.openclaw_client.close()
        logger.info("MessengerHandler cerrado")


# Función de conveniencia para procesar eventos webhook
async def process_webhook_event(event: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Procesa un evento webhook de Meta y genera respuestas.
    
    Args:
        event: Evento webhook de Meta
        
    Returns:
        Lista de respuestas a enviar (puede estar vacía)
    """
    handler = MessengerHandler()
    await handler.initialize()
    
    responses = []
    
    try:
        # Meta envía eventos en un array 'entry'
        if "entry" not in event:
            logger.warning("Evento sin campo 'entry'")
            return responses
        
        for entry in event["entry"]:
            if "messaging" not in entry:
                continue
                
            for messaging_event in entry["messaging"]:
                sender_id = messaging_event.get("sender", {}).get("id")
                if not sender_id:
                    continue
                
                # Manejar mensaje de texto
                if "message" in messaging_event and "text" in messaging_event["message"]:
                    message_text = messaging_event["message"]["text"]
                    message_id = messaging_event["message"].get("mid", "")
                    timestamp = messaging_event.get("timestamp", 0)
                    
                    response = await handler.handle_message(
                        sender_id, message_text, message_id, timestamp
                    )
                    responses.append(response)
                
                # Manejar postback (quick replies, botones)
                elif "postback" in messaging_event:
                    payload = messaging_event["postback"].get("payload", "")
                    timestamp = messaging_event.get("timestamp", 0)
                    
                    response = await handler.handle_postback(sender_id, payload, timestamp)
                    responses.append(response)
                
                # Manejar otros tipos de eventos (opcional)
                elif "read" in messaging_event:
                    logger.info(f"Mensaje leído por {sender_id}")
                elif "delivery" in messaging_event:
                    logger.info(f"Mensaje entregado a {sender_id}")
    
    except Exception as e:
        logger.error(f"Error procesando webhook: {str(e)}")
    
    finally:
        await handler.close()
    
    return responses