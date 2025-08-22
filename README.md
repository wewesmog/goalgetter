# MwalimuBot

An intelligent tutoring system designed to help Kenyan students learn through Telegram. The bot provides interactive lessons, practice problems, and personalized feedback in subjects like Mathematics and other core subjects.

## Features

- Interactive tutoring through Telegram
- Support for Form 1-4 curriculum
- Personalized learning experience
- Practice problems and instant feedback
- Subject coverage including Mathematics (Algebra, etc.)
- Multi-agent LangGraph architecture
- Cultural localization with Swahili integration

## Project Structure

- `backend/` - Backend server and API implementation
- `requirements.txt` - Python dependencies
- `mwalimu_env/` - Virtual environment configuration

## Railway Deployment

### Prerequisites

1. Railway account
2. Neon PostgreSQL database
3. Telegram Bot Token
4. LLM API keys (OpenAI, Groq, or OpenRouter)

### Environment Variables

Set these environment variables in Railway:

```bash
# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
WEBHOOK_URL=https://your-railway-app.railway.app/telegram/telegram-webhook

# Neon Database Configuration (Preferred - Connection String)
DATABASE_URL=postgresql://username:password@host:port/database_name

# Alternative: Individual Database Parameters
# PGHOST=your_neon_host
# PGDATABASE=your_database_name
# PGUSER=your_database_user
# PGPASSWORD=your_database_password
# PGPORT=5432
```

# LLM API Keys (at least one required)
OPENAI_API_KEY=your_openai_api_key
GROQ_API_KEY=your_groq_api_key
OPENROUTER_API_KEY=your_openrouter_api_key

# Optional: Tavily Search API
TAVILY_API_KEY=your_tavily_api_key
```

### Deployment Steps

1. **Connect to Railway:**
   ```bash
   railway login
   railway init
   ```

2. **Set Environment Variables:**
   ```bash
   railway variables set TELEGRAM_BOT_TOKEN=your_token
   railway variables set WEBHOOK_URL=https://your-app.railway.app/telegram/telegram-webhook
   # ... set all other required variables
   ```

3. **Deploy:**
   ```bash
   railway up
   ```

4. **Set Webhook:**
   After deployment, run the webhook setup:
   ```bash
   railway run python backend/setup_webhook.py
   ```

### Local Development

1. Clone the repository
2. Install dependencies: `pip install -r backend/requirements.txt`
3. Create `.env` file with environment variables
4. Run: `cd backend && uvicorn main:app --reload`

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 