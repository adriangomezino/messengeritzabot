# 🚀 Despliegue del Bot de Messenger

## Opción A: Railway (Recomendada - Más fácil y gratis)

### Paso 1: Crear cuenta en Railway
1. Ve a **https://railway.app/**
2. Haz clic en **"Start a New Project"**
3. Inicia sesión con GitHub o Google
4. Usa el correo: **jago0701@gmail.com**

### Paso 2: Desplegar desde GitHub
1. En Railway, selecciona **"Deploy from GitHub repo"**
2. Conecta tu cuenta de GitHub
3. Busca el repositorio `messenger-bot-itzamna`
4. Haz clic en **"Deploy"**

### Paso 3: Configurar variables de entorno
En Railway Dashboard → Project → Variables:

```bash
META_VERIFY_TOKEN=itzamna_bot_secreto_2026
META_PAGE_ACCESS_TOKEN=EAAG... (de Facebook)
OPENROUTER_API_KEY=sk-or-v1-... (de OpenRouter)
OPENROUTER_MODEL=openrouter/free
OPENCLAW_API_URL=https://server.itzamnaenergia.com
PORT=8000
```

### Paso 4: Obtener URL del bot
1. En Railway, ve a **"Settings"** → **"Domains"**
2. Copia la URL (ej: `https://itzamna-messenger-bot.up.railway.app`)
3. Esta será tu **Callback URL** para Facebook

---

## Opción B: Heroku

### Paso 1: Instalar Heroku CLI
```bash
# Linux
curl https://cli-assets.heroku.com/install.sh | sh

# Verificar instalación
heroku --version
```

### Paso 2: Iniciar sesión
```bash
heroku login
# Usa: jago0701@gmail.com
```

### Paso 3: Crear app
```bash
cd messenger-bot-itzamna
heroku create itzamna-messenger-bot
```

### Paso 4: Configurar variables
```bash
heroku config:set META_VERIFY_TOKEN=itzamna_bot_secreto_2026
heroku config:set META_PAGE_ACCESS_TOKEN=EAAG...
heroku config:set OPENROUTER_API_KEY=sk-or-v1-...
heroku config:set OPENROUTER_MODEL=openrouter/free
heroku config:set OPENCLAW_API_URL=https://server.itzamnaenergia.com
```

### Paso 5: Desplegar
```bash
git push heroku main
```

### Paso 6: Ver URL
```bash
heroku open
# URL: https://itzamna-messenger-bot.herokuapp.com
```

---

## Opción C: Render (Alternativa gratis)

### Paso 1: Crear cuenta
1. Ve a **https://render.com/**
2. Inicia sesión con GitHub

### Paso 2: Crear Web Service
1. **New** → **Web Service**
2. Conecta repositorio GitHub
3. Configuración:
   - **Name:** itzamna-messenger-bot
   - **Environment:** Python 3
   - **Build Command:** pip install -r requirements.txt
   - **Start Command:** uvicorn app:app --host=0.0.0.0 --port=$PORT

### Paso 3: Variables de entorno
En **Environment** tab, agrega las mismas variables que Railway.

---

## 🔧 Configuración después del despliegue

### 1. Obtener Callback URL
- Railway: `https://[nombre-proyecto].up.railway.app/webhook`
- Heroku: `https://itzamna-messenger-bot.herokuapp.com/webhook`
- Render: `https://[nombre].onrender.com/webhook`

### 2. Configurar Facebook App
1. developers.facebook.com → Tu app
2. Messenger → Webhooks
3. **Callback URL:** [tu_url_del_paso_1]
4. **Verify Token:** `itzamna_bot_secreto_2026`
5. Suscribir eventos: `messages`, `messaging_postbacks`

### 3. Probar el bot
```bash
# Usando curl
curl -X POST https://tu-url.com/message \
  -H "Content-Type: application/json" \
  -d '{"message": "Hola", "sender_id": "test"}'

# Deberías recibir respuesta
```

---

## 🐛 Solución de problemas

### Error: "Module not found"
```bash
# En local, instalar dependencias
pip install -r requirements.txt
```

### Error: "Invalid Verify Token"
- Verifica que `META_VERIFY_TOKEN` en tu hosting sea igual al que pusiste en Facebook

### Error: "Page Access Token invalid"
- Regenera el token en Facebook Developer
- Actualiza la variable en tu hosting

### Bot no responde
1. Verifica logs: `railway logs` o `heroku logs --tail`
2. Revisa que OpenRouter API Key sea válida
3. Verifica que el webhook esté suscrito a eventos

---

## 📞 Soporte

- **Railway Docs:** https://docs.railway.app/
- **Heroku Docs:** https://devcenter.heroku.com/
- **Meta Messenger Docs:** https://developers.facebook.com/docs/messenger-platform
- **OpenRouter Docs:** https://openrouter.ai/docs

**¡Listo para conectar con Facebook!** 🚀