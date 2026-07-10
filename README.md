# Alpha Analytical Engine v1.0

Standalone analytical service consuming ADC and Alpha Knowledge Engine.

## Railway variables

```text
ADC_BASE_URL=https://your-adc-service.up.railway.app
KNOWLEDGE_BASE_URL=https://your-knowledge-service.up.railway.app
```

## Start command

```bash
python -m uvicorn aae.api.server:app --host 0.0.0.0 --port 8080
```

## API

- `GET /`
- `GET /health`
- `POST /analysis/run`
- `GET /analysis/latest`
- `GET /analysis/history`
- `GET /version`

This v1.0 is a deterministic analytical foundation. It does not yet call an external LLM.
