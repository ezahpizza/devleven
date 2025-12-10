# Post-Call Notifications - Current State

## Overview

This document describes the post-call notification system that sends call summaries and follow-up information to users via Email and WhatsApp after a voice agent call completes.

## Architecture

### Flow Diagram

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│  Call Completes │────▶│  ElevenLabs      │────▶│  /webhook/         │
│                 │     │  Webhook         │     │  call_complete      │
└─────────────────┘     └──────────────────┘     └──────────┬──────────┘
                                                            │
                                                            ▼
                                               ┌─────────────────────┐
                                               │  GeminiService.     │
                                               │  analyze_transcript()│
                                               └──────────┬──────────┘
                                                          │
                                    ┌─────────────────────┼─────────────────────┐
                                    │                     │                     │
                                    ▼                     ▼                     ▼
                         ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
                         │  Extract:        │  │  Extract:        │  │  Extract:        │
                         │  - Summary       │  │  - Email pref    │  │  - WhatsApp pref │
                         │  - Follow-up     │  │  - Email addr    │  │  - WA number     │
                         └──────────────────┘  └────────┬─────────┘  └────────┬─────────┘
                                                        │                     │
                                                        ▼                     ▼
                                               ┌──────────────────┐  ┌──────────────────┐
                                               │  EmailService    │  │  WhatsAppService │
                                               │  (Gmail SMTP)    │  │  (Twilio)        │
                                               └──────────────────┘  └──────────────────┘
```

## Backend Components

### 1. GeminiService (`app/services/gemini_service.py`)

**Main Method:** `analyze_transcript(transcript, default_phone_number)`

Analyzes call transcripts using Google Gemini AI to extract:
- **Summary**: 2-3 sentence summary of call key points
- **Follow-up Date**: Extracted or calculated from relative dates
- **Email Notification**: Whether user requested email notification
- **WhatsApp Notification**: Whether user requested WhatsApp notification
- **Email Address**: Extracted email address from transcript
- **WhatsApp Number**: Extracted phone number or defaults to call number

**Returns:** `TranscriptAnalysisResult` dataclass

```python
@dataclass
class TranscriptAnalysisResult:
    summary: str
    follow_up_date: Optional[str]
    notify_email: bool
    notify_whatsapp: bool
    email_address: Optional[str]
    whatsapp_number: Optional[str]
```

---

### 2. EmailService (`app/services/email_service.py`)

**Main Method:** `send_call_summary_email(to_email, client_name, summary, follow_up_date)`

Sends HTML-formatted emails via Gmail SMTP with:
- Professional email template with gradient header
- Call summary section
- Follow-up date section (if scheduled)
- Plain text fallback

**Returns:**
```python
{
    "success": bool,
    "email_id": None,  # SMTP doesn't return an ID
    "to": str
}
```

---

### 3. WhatsAppService (`app/services/whatsapp_service.py`)

**Main Method:** `send_call_summary_whatsapp(to_number, client_name, summary, follow_up_date, call_id)`

Sends WhatsApp messages via Twilio Programmable Messaging:
- Call summary with formatted markdown
- Follow-up date information
- Interactive prompts for CONFIRM/RESCHEDULE

**Additional Methods:**
- `send_simple_message(to_number, message_body)` - For generic messages
- `_send_interactive_buttons()` - Sends follow-up action prompts

**Returns:**
```python
{
    "success": bool,
    "message_sid": str,  # Twilio message SID
    "to": str,
    "status": str
}
```

---

### 4. Webhook Handler (`app/routes/webhooks.py`)

**Endpoints:**

#### POST `/webhook/call_complete`
Main webhook endpoint that:
1. Verifies HMAC signature from ElevenLabs
2. Parses webhook payload
3. Calls `GeminiService.analyze_transcript()`
4. Saves call record to MongoDB
5. Triggers `_send_post_call_notifications()`
6. Broadcasts update to dashboard via WebSocket

#### POST `/webhook/whatsapp_response`
Handles incoming WhatsApp replies:
- **CONFIRM**: Confirms appointment
- **RESCHEDULE**: Initiates reschedule flow
- Returns appropriate response messages

---

### 5. Models (`app/models/call_record_models.py`)

**New Model:** `NotificationPreferences`

```python
class NotificationPreferences(BaseModel):
    notify_email: bool = False
    notify_whatsapp: bool = False
    email_address: Optional[str] = None
    whatsapp_number: Optional[str] = None
    email_sent: bool = False
    whatsapp_sent: bool = False
```

**Updated Model:** `CallCompletePayload`

Added fields:
- `notification_preferences: Optional[NotificationPreferences]`
- `phone_number: Optional[str]`

---

### 6. Configuration (`app/config.py`)

**New Environment Variables:**

| Variable | Description | Default |
|----------|-------------|---------|
| `GMAIL_USER` | Gmail account username | Required |
| `GMAIL_APP_PASSWORD` | Gmail App Password (not regular password) | Required |
| `GMAIL_FROM_EMAIL` | Sender email address | Falls back to `GMAIL_USER` |
| `TWILIO_WHATSAPP_NUMBER` | Twilio WhatsApp sender number | Falls back to `TWILIO_PHONE_NUMBER` |

**New Validation Methods:**
- `validate_email_config()` - Validates Gmail SMTP configuration
- `validate_whatsapp_config()` - Validates WhatsApp configuration

---

## Environment Variables

Add to your `.env` file:

```env
# Gmail SMTP Email Configuration
GMAIL_USER=your-gmail@gmail.com
GMAIL_APP_PASSWORD=your-16-character-app-password
GMAIL_FROM_EMAIL=your-gmail@gmail.com

# Twilio WhatsApp Configuration
TWILIO_WHATSAPP_NUMBER=+14155238886
```

**Note:** For Gmail, you need to use an App Password instead of your regular password. To create one:
1. Go to your Google Account > Security
2. Enable 2-Step Verification if not already enabled
3. Go to App Passwords and generate a new one for "Mail"

---

## Dependencies

**Python Packages:**
No additional packages required - uses Python's built-in `smtplib` and `email` modules.

The `twilio` package (already installed) provides WhatsApp messaging support.

---

## Trigger Phrases

The Gemini AI looks for these patterns in transcripts:

**Email Notifications:**
- "send me an email"
- "email me the details"
- "forward to my email"

**WhatsApp Notifications:**
- "send me a WhatsApp"
- "message me on WhatsApp"
- "text me"
- "send to my WhatsApp"

---

## File Changes Summary

| File | Change Type | Description |
|------|-------------|-------------|
| `app/services/gemini_service.py` | Modified | Added `TranscriptAnalysisResult`, `analyze_transcript()` |
| `app/services/email_service.py` | New | Email service using Gmail SMTP |
| `app/services/whatsapp_service.py` | New | WhatsApp service using Twilio |
| `app/services/__init__.py` | Modified | Export new services |
| `app/models/call_record_models.py` | Modified | Added `NotificationPreferences` model |
| `app/models/__init__.py` | Modified | Export `NotificationPreferences` |
| `app/routes/webhooks.py` | Modified | Integrated notifications, added WhatsApp webhook |
| `app/config.py` | Modified | Added Gmail SMTP and WhatsApp config |
| `client/src/types/call.types.ts` | Modified | Added `NotificationPreferences` interface |
| `client/src/components/dashboard/CallDetailModal.tsx` | Modified | Display notification status |
| `client/src/components/dashboard/CallTable.tsx` | Modified | Show notification indicators |
