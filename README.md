# 2GoodToGo

Auto-purchase Too Good To Go surprise bags the second they drop.

## Setup

1. **Install Python 3.8+** if you don't have it

2. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```

3. **Copy the env template and add your TGTG email:**
   ```
   copy .env.example .env
   ```
   Edit `.env` and set your email.

4. **Log in to TGTG:**
   ```
   python auth.py
   ```
   Check your email and click the login link. Tokens are saved locally.

## Usage

**Add a store:**
```
python manage.py add
```

**List your jobs:**
```
python manage.py list
```

**Edit a job:**
```
python manage.py edit
```

**Delete a job:**
```
python manage.py delete
```

**Start the bot:**
```
python bot.py
```

**Auto-start on Windows login (optional):**
```
python scheduler.py install
```

## How It Works

- You add a store and the exact time bags usually drop
- The bot starts polling 1 minute before that time, every 1-2 seconds
- The instant a bag appears, it auto-reserves on your TGTG account
- You get a desktop notification — open your TGTG app and go pick it up

## Security

- Credentials stored in `.env` (never committed to git)
- Auth tokens stored in `tokens.json` (never committed to git)
- All API calls over HTTPS
- No data sent anywhere except directly to TGTG servers
