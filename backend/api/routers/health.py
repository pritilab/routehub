from django.db import connection
from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    def check_db() -> bool:
        try:
            with connection.cursor() as cur:
                cur.execute("SELECT 1")
            return True
        except Exception:
            return False

    db_ok = await run_in_threadpool(check_db)
    return {"status": "ok" if db_ok else "degraded", "db": db_ok}
