# 🤖 Messenger Bot - Itzamna Energía

Bot de Messenger para atención automática de clientes usando IA.

## 🚀 Arquitectura

```
Usuario → Messenger → Meta Webhook → Heroku App → 
→ OpenRouter FREE API (openrouter/free) → 
→ OpenClaw API (https://server.itzamnaenergia.com) → 
→ Enviar respuesta → Messenger → Usuario
```

## 📁 Estructura

```
messenger-bot-itzamna/
├── app.py                    # Servidor FastAPI principal
├── openrouter_client.py      # Cliente OpenRouter (modelos gratis)
├── openclaw_client.py        # Cliente OpenClaw API
├── messenger_handler.py      # Manejo de webhooks Meta
├── requirements.txt          # Dependencias Python
├── Procfile                 # Configuración Heroku
├── runtime.txt              # Versión Python
├── .env.example             # Variables de entorno ejemplo
└── README.md                # Esta documentación
```

## 🔧 Configuración

### Variables de entorno (Heroku Config Vars)

```bash
META_VERIFY_TOKEN=tu_token_secreto_para_webhook
META_PAGE_ACCESS_TOKEN=EAAG...  # Token de página de Facebook
OPENROUTER_API_KEY=sk-or-v1-...  # API Key de OpenRouter
OPENROUTER_MODEL=openrouter/free  # Usar modelos gratis automáticamente
OPENCLAW_API_URL=https://server.itzamnaenergia.com
# OPENCLAW_API_KEY=openc-...  # Si OpenClaw requiere autenticación
PORT=8000  # Puerto para Heroku
```

### Modelo OpenRouter

Usamos `openrouter/free` que:
- Selecciona automáticamente el mejor modelo gratuito disponible
- Balancea carga entre diferentes proveedores
- Siempre gratis - usa créditos de diferentes proveedores

## 🚀 Despliegue

### Opción 1: Railway (Recomendado - Más fácil)
1. **Crear cuenta** en https://railway.app/
2. **Conectar GitHub** y seleccionar este repositorio
3. **Configurar variables** en Railway Dashboard
4. **Obtener URL** automáticamente

### Opción 2: Heroku
1. `heroku create itzamna-messenger-bot`
2. Configurar variables con `heroku config:set`
3. `git push heroku main`

### Opción 3: Render
1. Crear Web Service en https://render.com/
2. Conectar repositorio GitHub
3. Configurar variables de entorno

**Ver archivo [DEPLOY.md](DEPLOY.md) para instrucciones detalladas paso a paso.**

## 🔗 Configuración Meta Developer

1. **Crear app** en developers.facebook.com
2. **Agregar producto** "Messenger"
3. **Generar Page Access Token** para tu página
4. **Configurar webhook:**
   - URL: `https://itzamna-messenger-bot.herokuapp.com/webhook`
   - Verify Token: `META_VERIFY_TOKEN`
   - Suscribir eventos: `messages`, `messaging_postbacks`

5. **Vincular página** a la app

## 💬 Funcionalidades

### Respuestas automáticas:
- Saludo de bienvenida
- Preguntas frecuentes (precios, instalación, garantías)
- Solicitud de cotización básica
- Agenda de consultas
- Información de contacto

### Integraciones futuras:
- Sistema de cotizaciones automáticas
- Calendario de disponibilidad
- Base de datos de clientes
- Notificaciones de seguimiento

## 🛠️ Desarrollo local

```bash
# 1. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables
cp .env.example .env
# Editar .env con tus valores

# 4. Ejecutar servidor
uvicorn app:app --reload --port 8000

# 5. Probar webhook (usar ngrok para tunnel público)
ngrok http 8000
```

## 📞 Soporte

- **Meta Developer Docs:** https://developers.facebook.com/docs/messenger-platform
- **OpenRouter Docs:** https://openrouter.ai/docs
- **OpenClaw API:** https://server.itzamnaenergia.com

---

**Desarrollado por:** Adán (IA Asistente)  
**Para:** Itzamna Energía  
**Fecha:** Abril 2026