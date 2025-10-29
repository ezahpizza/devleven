# Quick Start Guide


### Step 3: Setup Database (30 seconds)

```bash
python setup_db.py
```

### Step 4: Start ngrok

### Step 5: Configure ElevenLabs Webhook (1 min)

1. Go to [ElevenLabs Console](https://elevenlabs.io/app/conversational-ai) → Webhooks
2. Click "Create Webhook"
3. Fill in:
   - **Name**: DevFusion Lead Capture
   - **URL**: `https://your-ngrok-url.ngrok.io/elevenlabs-webhook`
   - **Auth Method**: HMAC
4. Click "Create"
5. Copy the **Webhook Secret** and add to `.env`:
   ```env
   ELEVENLABS_WEBHOOK_SECRET=whsec_xxxxx
   ```
6. Associate webhook with your agent

### Step 6: Start Server (10 seconds)

## 🆘 Common Issues

### "Database connection failed"
- Check PostgreSQL is running: `pg_isready`
- Verify DATABASE_URL format
- Test connection: `psql "postgresql://user:pass@host:port/db"`

### "ElevenLabs connection timeout"
- Verify API key is correct
- Check agent ID exists
- Ensure agent is active in console

### "Twilio call failed"
- Verify Twilio credentials
- Check phone number format (E.164: +1234567890)
- Ensure FROM number is verified/purchased

### "Webhook not receiving events"
- Verify ngrok is running
- Check webhook URL in ElevenLabs console
- Test webhook endpoint directly:
  ```bash
  curl -X POST http://localhost:8000/elevenlabs-webhook \
    -H "Content-Type: application/json" \
    -d '{"type":"test"}'
  ```

### "First message not personalized"
- Ensure your agent supports first message override
- Check ElevenLabs plan includes this feature
- Verify client_name is passed in request

---

## 📊 Monitoring

### View Logs
```bash
# Real-time logs
python main.py

# Look for:
[Handler] Client: Prateek, Phone: +917978268815
[ElevenLabs] Connecting with personalized greeting...
[Webhook] Lead created: ID=1, Name=Prateek
```

### Check Database
```bash
# Connect to PostgreSQL
psql "postgresql://user:pass@host:port/devfusion_calls"

# View leads
SELECT * FROM leads ORDER BY created_at DESC LIMIT 10;
```

---
