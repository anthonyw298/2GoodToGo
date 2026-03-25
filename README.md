# 2GoodToGo

Auto-purchase Too Good To Go surprise bags the second they drop.

## Setup

1. **Clone the repo:**
   ```
   git clone https://github.com/anthonyw298/2GoodToGo.git
   cd 2GoodToGo
   ```

2. **Install Python 3.8+** if you don't have it

3. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```

4. **Create your `.env` file:**
   ```
   copy .env.example .env
   notepad .env
   ```
   Put your TGTG email in.

5. **Log in to TGTG:**
   ```
   python auth.py
   ```
   Check your email, click the login link, come back. It'll say "Login successful!"

6. **Add a store:**
   ```
   python manage.py add
   ```
   Search by location or browse your favorites, pick the store, set the drop time.

## Running the Bot

**Test mode (polls but does NOT purchase):**
```
python bot.py --test
```
Use this first to make sure everything works. If bags are available it'll say "found! [TEST MODE — not purchasing]" instead of buying.

**Live mode (polls and auto-purchases):**
```
python bot.py
```
Leave it running. It'll sleep until your set time, poll with a bell curve distribution (fastest at the exact time, slower at the edges), buy the instant a bag appears, and send you a desktop notification.

**Auto-start on Windows login (optional):**
```
python scheduler.py install
```

## Managing Jobs

```
python manage.py add       # Add a store to watch
python manage.py list      # List all jobs
python manage.py edit      # Edit a job (time, quantity, on/off)
python manage.py delete    # Delete a job
```

## How It Works

- You add a store and the exact time bags usually drop
- The bot opens a 1-minute polling window centered on that time
- Polling follows a bell curve: ~5 calls/sec at the exact time, tapering to ~1 every 3s at the edges
- Hard capped at 180 API calls per window — never exceeds this
- The instant a bag appears, it auto-reserves on your TGTG account using the payment method you have saved in the app
- You get a desktop notification — open your TGTG app and go pick it up
- The reservation shows up in your TGTG app just like a normal purchase

## Security

- Credentials stored in `.env` (never committed to git)
- Auth tokens stored in `tokens.json` (never committed to git)
- All API calls over HTTPS
- No data sent anywhere except directly to TGTG servers
