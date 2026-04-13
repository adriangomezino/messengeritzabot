#!/usr/bin/env python3
"""
Script para probar el bot localmente sin necesidad de Facebook.
Útil para desarrollo y pruebas iniciales.
"""

import asyncio
import sys
import os
from openrouter_client import get_openrouter_response


async def test_bot():
    """Prueba el bot con mensajes de ejemplo."""
    
    print("🤖 Probando Bot de Itzamna Energía")
    print("=" * 50)
    
    # Mensajes de prueba
    test_messages = [
        "Hola",
        "¿Cuánto cuestan los paneles solares?",
        "Quiero una cotización",
        "¿Cómo es el proceso de instalación?",
        "¿Qué garantías ofrecen?",
        "Necesito hablar con un especialista",
        "Gracias por la información",
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n📝 Prueba {i}: '{message}'")
        print("-" * 40)
        
        try:
            # Usar OpenRouter directamente
            response = await get_openrouter_response(message)
            print(f"🤖 Respuesta: {response}")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        # Pausa entre mensajes
        if i < len(test_messages):
            input("\n⏎ Presiona Enter para continuar...")
    
    print("\n" + "=" * 50)
    print("✅ Pruebas completadas")


async def test_openclaw_integration():
    """Prueba la integración con OpenClaw."""
    print("\n🔗 Probando integración con OpenClaw...")
    
    try:
        from openclaw_client import process_with_openclaw
        
        test_message = "Hola, necesito información sobre paneles solares en Mérida"
        response = await process_with_openclaw(test_message)
        
        if response:
            print(f"✅ OpenClaw respondió: {response[:100]}...")
        else:
            print("⚠️ OpenClaw no respondió (puede ser normal si no está configurado)")
    
    except ImportError:
        print("❌ No se pudo importar openclaw_client")
    except Exception as e:
        print(f"❌ Error con OpenClaw: {str(e)}")


def check_environment():
    """Verifica que las variables de entorno estén configuradas."""
    print("\n🔍 Verificando entorno...")
    
    required_vars = ["OPENROUTER_API_KEY"]
    optional_vars = ["META_VERIFY_TOKEN", "META_PAGE_ACCESS_TOKEN", "OPENCLAW_API_URL"]
    
    print("Variables requeridas:")
    for var in required_vars:
        if os.getenv(var):
            print(f"  ✅ {var}: Configurada")
        else:
            print(f"  ❌ {var}: NO configurada")
            print(f"     Obtén una en: https://openrouter.ai/keys")
    
    print("\nVariables opcionales:")
    for var in optional_vars:
        if os.getenv(var):
            print(f"  ✅ {var}: Configurada")
        else:
            print(f"  ⚠️ {var}: No configurada (ok para pruebas)")


async def main():
    """Función principal."""
    print("🧪 Pruebas del Bot de Messenger - Itzamna Energía")
    print("=" * 50)
    
    # Verificar entorno
    check_environment()
    
    # Preguntar qué probar
    print("\n¿Qué quieres probar?")
    print("1. 🤖 Solo OpenRouter (respuestas de IA)")
    print("2. 🔗 OpenRouter + OpenClaw (si está configurado)")
    print("3. 🚪 Salir")
    
    choice = input("\nSelecciona (1-3): ").strip()
    
    if choice == "1":
        await test_bot()
    elif choice == "2":
        await test_bot()
        await test_openclaw_integration()
    elif choice == "3":
        print("👋 ¡Hasta luego!")
        return
    else:
        print("❌ Opción no válida")
    
    print("\n🎯 Próximos pasos:")
    print("1. Configurar variables de entorno en .env")
    print("2. Ejecutar servidor: uvicorn app:app --reload")
    print("3. Probar con: python test_local.py")
    print("4. Desplegar en Railway/Heroku")
    print("5. Configurar Facebook App")


if __name__ == "__main__":
    # Cargar variables de entorno si existe .env
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("📁 Variables cargadas desde .env")
    except ImportError:
        print("⚠️ python-dotenv no instalado, usando variables del sistema")
    
    # Ejecutar pruebas
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Pruebas canceladas por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {str(e)}")
        sys.exit(1)