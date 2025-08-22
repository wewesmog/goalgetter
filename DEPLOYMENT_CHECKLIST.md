# Railway Deployment Checklist for MwalimuBot

## ✅ Pre-Deployment Checklist

### 1. Environment Variables Setup
- [ ] `TELEGRAM_BOT_TOKEN` - Your Telegram bot token from @BotFather
- [ ] `WEBHOOK_URL` - Will be set to `https://your-app.railway.app/telegram/telegram-webhook`
- [ ] **Neon Database Configuration (Choose one option):**
  - [ ] **Option A (Recommended):** `DATABASE_URL` - Neon connection string
  - [ ] **Option B:** Individual parameters:
    - [ ] `PGHOST` - Neon database host
    - [ ] `PGDATABASE` - Database name
    - [ ] `PGUSER` - Database username
    - [ ] `PGPASSWORD` - Database password
    - [ ] `PGPORT` - Database port (usually 5432)
- [ ] At least one LLM API key:
  - [ ] `OPENAI_API_KEY` (OpenAI API)
  - [ ] `GROQ_API_KEY` (Groq API)
  - [ ] `OPENROUTER_API_KEY` (OpenRouter API)
- [ ] `TAVILY_API_KEY` (Optional - for search functionality)

### 2. Database Setup
- [ ] Neon PostgreSQL database created
- [ ] Database connection string or individual parameters available
- [ ] Database tables will be created automatically on first run

### 3. Telegram Bot Setup
- [ ] Bot created with @BotFather
- [ ] Bot token obtained
- [ ] Bot permissions configured

## 🚀 Deployment Steps

### Step 1: Railway Setup
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize project
railway init
```

### Step 2: Set Environment Variables
```bash
# Set all required environment variables
railway variables set TELEGRAM_BOT_TOKEN=your_bot_token

# Option A: Set Neon connection string (Recommended)
railway variables set DATABASE_URL=postgresql://username:password@host:port/database_name

# Option B: Set individual database parameters
# railway variables set PGHOST=your_neon_host
# railway variables set PGDATABASE=your_db_name
# railway variables set PGUSER=your_db_user
# railway variables set PGPASSWORD=your_db_password
# railway variables set PGPORT=5432

railway variables set OPENAI_API_KEY=your_openai_key
# ... set other variables
```

### Step 3: Deploy
```bash
# Deploy to Railway
railway up
```

### Step 4: Configure Webhook
```bash
# After deployment, set the webhook URL
railway variables set WEBHOOK_URL=https://your-app.railway.app/telegram/telegram-webhook

# Run webhook setup script
railway run python backend/setup_webhook.py
```

## 🔍 Post-Deployment Verification

### 1. Health Check
- [ ] Visit `https://your-app.railway.app/` - should show "MwalimuBot is running!"
- [ ] Check Railway logs for any errors

### 2. Telegram Bot Test
- [ ] Send `/start` to your bot
- [ ] Verify bot responds with welcome message
- [ ] Test basic conversation flow

### 3. Database Connection
- [ ] Check logs for successful database connection
- [ ] Verify conversation state is being saved

### 4. LLM Integration
- [ ] Test that bot can generate responses
- [ ] Check logs for LLM API calls

## 🐛 Troubleshooting

### Common Issues

1. **Bot not responding**
   - Check webhook URL is correct
   - Verify bot token is valid
   - Check Railway logs for errors

2. **Database connection failed**
   - Verify DATABASE_URL or individual database environment variables
   - Check Neon database is accessible from Railway
   - Ensure database exists and is running
   - Verify connection string format: `postgresql://username:password@host:port/database_name`

3. **LLM API errors**
   - Verify API keys are correct
   - Check API quota/limits
   - Ensure at least one LLM provider is configured

4. **Webhook setup failed**
   - Run webhook setup script manually
   - Check webhook URL format
   - Verify bot has webhook permissions

### Useful Commands

```bash
# Check Railway logs
railway logs

# Run commands in Railway environment
railway run python backend/setup_webhook.py

# Check environment variables
railway variables

# Restart deployment
railway up
```

## 📊 Monitoring

- Monitor Railway dashboard for:
  - CPU/Memory usage
  - Request logs
  - Error rates
  - Response times

- Set up alerts for:
  - High error rates
  - Bot downtime
  - Database connection issues

## 🔄 Updates

To update the deployment:
```bash
# Push changes
git push

# Deploy updates
railway up
```

## 📞 Support

If you encounter issues:
1. Check Railway logs first
2. Verify all environment variables
3. Test locally with same configuration
4. Check Telegram Bot API documentation
