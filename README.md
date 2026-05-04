# PDD ChatBot

Помощник по ПДД с ответами из официальных источников.

## Запуск

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- API: http://localhost:8000

## Локально

**Backend:**
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```