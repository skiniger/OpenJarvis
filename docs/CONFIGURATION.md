# OpenJarvis Configuration Reference

This document lists **all environment variables** used across the codebase,
grouped by subsystem. Variables marked **Required** must be set for the
corresponding feature to produce real results instead of demo/fallback data.

---

## Core / Server

| Variable | Required | Purpose |
|----------|----------|---------|
| `OPENJARVIS_HOME` | no | Override default home dir (`~/.openjarvis`) |
| `OPENJARVIS_CONFIG` | no | Path to custom config file |
| `SECRET_KEY` | **yes** | JWT / session signing key |
| `WEBHOOK_SECRET` | no | Webhook signature verification |

---

## Landhaus Bavaria (Domain Agent)

| Variable | Required | Purpose |
|----------|----------|---------|
| `LANDHAUS_WEBSITE` | no | Website URL (default: `https://www.landhausbavaria.de`) |
| `DESKLINE_PROXY_URL` | **yes** | Deskline proxy endpoint for room availability |
| `DESKLINE_BASE_URL` | no | Deskline base (default: `https://webclient4.deskline.net`) |
| `BOOKINGCOM_ICAL_URL` | **yes** | Booking.com iCal feed URL |
| `VERCEL_API_TOKEN` | **yes** | Vercel API token for deployment status |
| `VERCEL_PROJECT_ID` | **yes** | Vercel project ID |

---

## Search & Retrieval

| Variable | Required | Purpose |
|----------|----------|---------|
| `TAVILY_API_KEY` | **yes** | Tavily web-search API key |

Fallback: if Tavily is unavailable, DuckDuckGo (`ddgs`) is used automatically.

---

## LLM Engines

| Variable | Required | Purpose |
|----------|----------|---------|
| `OLLAMA_HOST` | no | Ollama host (default: `localhost:11434`) |
| `OPENAI_API_KEY` | no | OpenAI cloud API key |
| `ANTHROPIC_API_KEY` | no | Anthropic API key |
| `GOOGLE_API_KEY` | no | Gemini API key |
| `MINIMAX_API_KEY` | no | MiniMax API key |
| `OPENROUTER_API_KEY` | no | OpenRouter API key |
| `LLM_API_KEY` | no | Generic LLM API key |

---

## OSINT / Security

| Variable | Required | Purpose |
|----------|----------|---------|
| `FBI_WATCHDOG_ENABLED` | no | Enable FBI Watchdog monitoring |

---

## Channels / Messaging

| Variable | Required | Purpose |
|----------|----------|---------|
| `TELEGRAM_BOT_TOKEN` | **yes** | Telegram bot token |
| `DISCORD_BOT_TOKEN` | **yes** | Discord bot token |
| `SLACK_BOT_TOKEN` | **yes** | Slack bot token |
| `SLACK_APP_TOKEN` | **yes** | Slack app token |
| `TWITTER_API_KEY` | **yes** | Twitter API key |
| `TWITTER_API_SECRET` | **yes** | Twitter API secret |
| `TWITTER_ACCESS_TOKEN` | **yes** | Twitter access token |
| `TWITTER_BEARER_TOKEN` | **yes** | Twitter bearer token |
| `TWITTER_BOT_USER_ID` | **yes** | Twitter bot user ID |
| `WHATSAPP_ACCESS_TOKEN` | **yes** | WhatsApp access token |
| `WHATSAPP_APP_SECRET` | **yes** | WhatsApp app secret |
| `WHATSAPP_VERIFY_TOKEN` | **yes** | WhatsApp verify token |
| `TWILIO_ACCOUNT_SID` | **yes** | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | **yes** | Twilio auth token |
| `TWILIO_PHONE_NUMBER` | **yes** | Twilio phone number |
| `EMAIL_USERNAME` | **yes** | SMTP username |
| `EMAIL_PASSWORD` | **yes** | SMTP password |
| `SENDBLUE_API_KEY_ID` | **yes** | SendBlue API key |
| `SENDBLUE_API_SECRET_KEY` | **yes** | SendBlue secret |
| `SENDBLUE_FROM_NUMBER` | **yes** | SendBlue from number |
| `BLUEBUBBLES_URL` | **yes** | BlueBubbles server URL |
| `BLUEBUBBLES_PASSWORD` | **yes** | BlueBubbles password |
| `SIGNAL_API_URL` | **yes** | Signal API endpoint |
| `MASTODON_ACCESS_TOKEN` | **yes** | Mastodon access token |
| `MASTODON_API_BASE_URL` | **yes** | Mastodon instance URL |
| `MATRIX_ACCESS_TOKEN` | **yes** | Matrix access token |
| `MATRIX_HOMESERVER` | **yes** | Matrix homeserver URL |
| `MATTERMOST_TOKEN` | **yes** | Mattermost token |
| `MATTERMOST_URL` | **yes** | Mattermost URL |
| `ROCKETCHAT_URL` | **yes** | Rocket.Chat URL |
| `ROCKETCHAT_USER` | **yes** | Rocket.Chat username |
| `ROCKETCHAT_PASSWORD` | **yes** | Rocket.Chat password |
| `ROCKETCHAT_AUTH_TOKEN` | **yes** | Rocket.Chat auth token |
| `ROCKETCHAT_USER_ID` | **yes** | Rocket.Chat user ID |
| `IRC_SERVER` | **yes** | IRC server |
| `IRC_PORT` | **yes** | IRC port |
| `IRC_NICK` | **yes** | IRC nick |
| `IRC_PASSWORD` | **yes** | IRC password |
| `XMPP_SERVER` | **yes** | XMPP server |
| `XMPP_PORT` | **yes** | XMPP port |
| `XMPP_JID` | **yes** | XMPP JID |
| `XMPP_PASSWORD` | **yes** | XMPP password |
| `ZULIP_SITE` | **yes** | Zulip site URL |
| `ZULIP_EMAIL` | **yes** | Zulip bot email |
| `ZULIP_API_KEY` | **yes** | Zulip API key |
| `ZULIP_RC` | **yes** | Zulip RC file path |
| `NOSTR_PRIVATE_KEY` | **yes** | Nostr private key |
| `NOSTR_RELAYS` | **yes** | Nostr relays |
| `FEISHU_APP_ID` | **yes** | Feishu app ID |
| `FEISHU_APP_SECRET` | **yes** | Feishu app secret |
| `TEAMS_APP_ID` | **yes** | Teams app ID |
| `TEAMS_APP_PASSWORD` | **yes** | Teams app password |
| `VIBER_AUTH_TOKEN` | **yes** | Viber auth token |
| `VIBER_BOT_NAME` | **yes** | Viber bot name |
| `VIBER_BOT_AVATAR` | **yes** | Viber bot avatar URL |
| `TWITCH_CLIENT_ID` | **yes** | Twitch client ID |
| `TWITCH_ACCESS_TOKEN` | **yes** | Twitch access token |
| `TWITCH_NICK` | **yes** | Twitch nickname |

---

## Audio / Speech

| Variable | Required | Purpose |
|----------|----------|---------|
| `DEEPGRAM_API_KEY` | **yes** | Deepgram speech-to-text API |
| `CARTESIA_API_KEY` | **yes** | Cartesia text-to-speech API |

---

## Other Integrations

| Variable | Required | Purpose |
|----------|----------|---------|
| `HUGGINGFACE_HUB_TOKEN` | no | HuggingFace model access |
| `REDDIT_CLIENT_ID` | **yes** | Reddit API client ID |
| `REDDIT_USERNAME` | **yes** | Reddit username |
| `REDDIT_PASSWORD` | **yes** | Reddit password |
| `GITLAB` | no | GitLab URL |
| `HERMES_AGENT_PATH` | no | Hermes agent binary path |

---

## How to Configure

1. Copy `.env.example` to `.env`
2. Fill in the variables for the features you want active
3. Restart the server: `python -m openjarvis.cli serve`

Features without required env vars will show **demo data** in the dashboard.

---

## Quick-Start (Minimum Viable)

For a basic working system with Landhaus + Search + Chat:

```bash
# Required
export SECRET_KEY="your-secret-key-here"
export TAVILY_API_KEY="your-tavily-key"

# Optional but recommended for real Landhaus data
export DESKLINE_PROXY_URL="https://your-proxy.example.com"
export BOOKINGCOM_ICAL_URL="https://ical.booking.com/..."
export VERCEL_API_TOKEN="your-vercel-token"
export VERCEL_PROJECT_ID="prj_..."
```
