"""
Servidor FastAPI para el bot de Messenger de Itzamna Energía.
Desplegable en Heroku, Railway, Render, etc.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

import httpx
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

from messenger_handler import process_webhook_event

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="Itzamna Energía Messenger Bot",
    description="Bot de Messenger para atención automática de clientes usando IA",
    version="1.0.0",
    docs_url="/docs" if os.getenv("DEBUG", "False").lower() == "true" else None,
    redoc_url=None
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, restringir a dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variables de entorno
META_VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN")
META_PAGE_ACCESS_TOKEN = os.getenv("META_PAGE_ACCESS_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENCLAW_API_URL = os.getenv("OPENCLAW_API_URL", "https://server.itzamnaenergia.com")
PORT = int(os.getenv("PORT", 8000))


@app.get("/")
async def root():
    """Endpoint raíz - información del servicio."""
    return {
        "service": "Itzamna Energía Messenger Bot",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "GET /": "Esta información",
            "GET /health": "Health check",
            "GET /webhook": "Verificación webhook Meta",
            "POST /webhook": "Webhook para mensajes de Messenger",
            "POST /message": "Endpoint para probar mensajes",
        },
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/health")
async def health_check():
    """Health check endpoint para monitoreo."""
    # Verificar configuraciones básicas
    checks = {
        "meta_verify_token_configured": bool(META_VERIFY_TOKEN),
        "meta_page_token_configured": bool(META_PAGE_ACCESS_TOKEN),
        "openrouter_api_key_configured": bool(OPENROUTER_API_KEY),
        "openclaw_url_configured": bool(OPENCLAW_API_URL),
    }
    
    all_healthy = all(checks.values())
    
    return {
        "ok": all_healthy,
        "status": "healthy" if all_healthy else "degraded",
        "checks": checks,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/webhook")
async def verify_webhook(
    request: Request,
    hub_mode: Optional[str] = None,
    hub_verify_token: Optional[str] = None,
    hub_challenge: Optional[str] = None
):
    """
    Endpoint para verificación del webhook de Meta.
    
    Meta envía una solicitud GET para verificar el webhook durante la configuración.
    """
    logger.info(f"Verificacion webhook: hub_mode={hub_mode}, hub_verify_token={hub_verify_token}, expected={META_VERIFY_TOKEN}")
    
    if not META_VERIFY_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="META_VERIFY_TOKEN no configurado"
        )
    
    if hub_mode == "subscribe" and hub_verify_token == META_VERIFY_TOKEN:
        logger.info("Webhook verificado exitosamente")
        return PlainTextResponse(hub_challenge)
    else:
        logger.warning(f"Fallo verificacion webhook: hub_mode={hub_mode}, hub_verify_token={hub_verify_token}, expected={META_VERIFY_TOKEN}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Verificacion fallida"
        )


@app.post("/webhook")
async def handle_webhook(request: Request):
    """
    Endpoint principal para recibir webhooks de Meta Messenger.
    
    Meta envía eventos de mensajes, postbacks, entregas, lecturas, etc.
    """
    try:
        # Leer el cuerpo de la solicitud
        body = await request.json()
        logger.info(f"Webhook recibido: {json.dumps(body, indent=2)[:500]}...")
        
        # Verificar que sea un evento de página (opcional pero recomendado)
        if "object" in body and body["object"] != "page":
            logger.warning(f"Objeto no reconocido: {body.get('object')}")
            return JSONResponse(content={"status": "ignored"})
        
        # Procesar el evento
        responses = await process_webhook_event(body)
        
        # Enviar respuestas a Messenger
        sent_messages = []
        for response in responses:
            sender_id = response["metadata"]["sender_id"]
            message_text = response["text"]
            
            # Enviar mensaje a través de Meta API
            success = await send_messenger_message(sender_id, message_text, response)
            
            sent_messages.append({
                "sender_id": sender_id,
                "success": success,
                "text_preview": message_text[:100] + "..." if len(message_text) > 100 else message_text
            })
        
        logger.info(f"Procesado webhook: {len(responses)} respuestas enviadas")
        
        return JSONResponse(content={
            "status": "processed",
            "responses_sent": len(responses),
            "details": sent_messages,
            "timestamp": datetime.now().isoformat()
        })
        
    except json.JSONDecodeError:
        logger.error("Error decodificando JSON del webhook")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON"
        )
    except Exception as e:
        logger.error(f"Error procesando webhook: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


async def send_messenger_message(recipient_id: str, message_text: str, 
                               response_metadata: Dict[str, Any]) -> bool:
    """
    Envía un mensaje a través de la API de Messenger.
    
    Args:
        recipient_id: ID del destinatario en Messenger
        message_text: Texto del mensaje a enviar
        response_metadata: Metadatos de la respuesta generada
        
    Returns:
        True si se envió exitosamente, False si falló
    """
    if not META_PAGE_ACCESS_TOKEN:
        logger.error("META_PAGE_ACCESS_TOKEN no configurado")
        return False
    
    # Construir payload del mensaje
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text},
        "messaging_type": "RESPONSE"
    }
    
    # Agregar quick replies si están disponibles
    if "quick_replies" in response_metadata:
        payload["message"]["quick_replies"] = response_metadata["quick_replies"]
    
    # Headers para la API de Meta
    headers = {
        "Content-Type": "application/json",
    }
    
    # Parámetros de la solicitud
    params = {
        "access_token": META_PAGE_ACCESS_TOKEN
    }
    
    url = "https://graph.facebook.com/v19.0/me/messages"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                headers=headers,
                params=params,
                json=payload
            )
            
            if response.status_code == 200:
                logger.info(f"Mensaje enviado a {recipient_id}: {message_text[:50]}...")
                return True
            else:
                logger.error(f"Error enviando mensaje a {recipient_id}: {response.status_code} - {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"Excepción enviando mensaje a {recipient_id}: {str(e)}")
        return False


@app.post("/message")
async def test_message(request: Request):
    """
    Endpoint para probar el bot sin necesidad de Messenger.
    Útil para desarrollo y pruebas.
    """
    try:
        data = await request.json()
        message_text = data.get("message", "")
        sender_id = data.get("sender_id", "test_user_123")
        
        if not message_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El campo 'message' es requerido"
            )
        
        logger.info(f"Mensaje de prueba: {sender_id} - {message_text}")
        
        # Simular evento webhook
        simulated_event = {
            "object": "page",
            "entry": [{
                "messaging": [{
                    "sender": {"id": sender_id},
                    "message": {"text": message_text, "mid": "test_mid"},
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }]
            }]
        }
        
        # Procesar como webhook normal
        responses = await process_webhook_event(simulated_event)
        
        if responses:
            response_data = responses[0]
            return {
                "success": True,
                "response": response_data["text"],
                "metadata": response_data["metadata"],
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "error": "No se generó respuesta",
                "timestamp": datetime.now().isoformat()
            }
            
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON"
        )
    except Exception as e:
        logger.error(f"Error en endpoint de prueba: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/config")
async def get_config():
    """
    Endpoint para ver la configuración actual (sin valores sensibles).
    """
    return {
        "meta_verify_token_configured": bool(META_VERIFY_TOKEN),
        "meta_page_token_configured": bool(META_PAGE_ACCESS_TOKEN),
        "openrouter_api_key_configured": bool(OPENROUTER_API_KEY),
        "openclaw_url": OPENCLAW_API_URL,
        "openclaw_url_configured": bool(OPENCLAW_API_URL),
        "port": PORT,
        "debug": os.getenv("DEBUG", "False").lower() == "true",
        "timestamp": datetime.now().isoformat(),
    }


# Middleware para logging de solicitudes
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware para logging de todas las solicitudes."""
    start_time = datetime.now()
    
    # Omitir logging de health checks frecuentes
    if request.url.path != "/health":
        logger.info(f"Inicio: {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        process_time = (datetime.now() - start_time).total_seconds() * 1000
        
        if request.url.path != "/health":
            logger.info(
                f"Fin: {request.method} {request.url.path} "
                f"- {response.status_code} - {process_time:.2f}ms"
            )
        
        return response
    except Exception as e:
        process_time = (datetime.now() - start_time).total_seconds() * 1000
        logger.error(
            f"Error: {request.method} {request.url.path} "
            f"- Exception: {str(e)} - {process_time:.2f}ms"
        )
        raise


# Manejo de excepciones global
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Manejador global de excepciones."""
    logger.error(f"Excepción no manejada: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    # Verificar configuraciones críticas
    if not META_VERIFY_TOKEN:
        logger.warning("META_VERIFY_TOKEN no configurado - verificación webhook fallará")
    if not META_PAGE_ACCESS_TOKEN:
        logger.warning("META_PAGE_ACCESS_TOKEN no configurado - no se podrán enviar mensajes")
    if not OPENROUTER_API_KEY:
        logger.warning("OPENROUTER_API_KEY no configurado - bot no funcionará")
    
    logger.info(f"Iniciando servidor en puerto {PORT}")
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=PORT,
        reload=os.getenv("DEBUG", "False").lower() == "true"
    )