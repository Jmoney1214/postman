# Liquor Store AI Assistant - Backend

## Quickstart

1. Python 3.11+
2. Create and fill `.env`:

```
cp .env.example .env
# edit values
```

3. Install dependencies:

```
pip install -r requirements.txt
```

4. Run server:

```
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

5. Test health:

```
curl http://localhost:8000/health
```

## Environment Variables
- `LIGHTSPEED_API_KEY`
- `LIGHTSPEED_ACCOUNT_ID`
- `ENVIRONMENT` (default: `development`)
