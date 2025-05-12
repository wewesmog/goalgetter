import requests
import os
from dotenv import load_dotenv

def setup_webhook():
    # Load environment variables
    #load_dotenv()
    
    # Get the bot token from environment variables or use hardcoded token for testing
    TELEGRAM_TOKEN = "8104473553:AAF-lQpLvIyZ2QQC5_ECyEFiSHm_x90C7wE"
    print(f"Token found: {'Yes' if TELEGRAM_TOKEN else 'No'}")
    
    if not TELEGRAM_TOKEN:
        print("❌ Error: TELEGRAM_BOT_TOKEN not found in environment variables")
        print("Please make sure you have created a .env file with TELEGRAM_BOT_TOKEN")
        return
    
    # Your ngrok URL + webhook endpoint
    WEBHOOK_URL = "https://965f-197-232-1-154.ngrok-free.app/telegram/telegram-webhook"
    
    # Telegram API endpoint to set webhook
    api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook"
    
    print(f"Setting webhook to: {WEBHOOK_URL}")
    print(f"Using API URL: {api_url}")
    
    # Set up the webhook
    try:
        response = requests.post(
            api_url,
            json={'url': WEBHOOK_URL}
        )
        
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.text}")
        
        if response.status_code == 200 and response.json().get('ok'):
            print("✅ Webhook set up successfully!")
            print(f"Webhook URL: {WEBHOOK_URL}")
        else:
            print("❌ Failed to set up webhook")
            print(f"Response: {response.json()}")
            
        # Let's also test the getWebhookInfo endpoint
        info_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getWebhookInfo"
        info_response = requests.get(info_url)
        print("\nCurrent Webhook Info:")
        print(info_response.json())
        
    except Exception as e:
        print(f"❌ Error occurred: {str(e)}")

if __name__ == "__main__":
    setup_webhook() 