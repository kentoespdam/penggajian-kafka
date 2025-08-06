import asyncio
import io
import os
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Response
from fastapi.responses import StreamingResponse

from core import cron_tanggungan
from core.proses_gaji.consumer import consume_proses_gaji

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_event_loop()
    loop.create_task(consume_proses_gaji())
    scheduler.add_job(cron_tanggungan.execute, 'interval', seconds=600)
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(
    title="Proses Gaji",
    description="Proses gaji",
    version="1.0.0",
    lifespan=lifespan,
    not_found_response={"message": "Not Found"},
)


@app.get("/export/table_gaji/{export_id}", status_code=200)
async def export_table_gaji(export_id: str) -> StreamingResponse | Response:
    """Export Excel file for table gaji by export ID"""
    file_path = f"result_excel/tabel_gaji_{export_id}.xlsx"

    if not os.path.exists(file_path):
        return Response("File Not Found!", status_code=404)

    with open(file_path, "rb") as file:
        file_data = file.read()

    return StreamingResponse(
        io.BytesIO(file_data),
        headers={"Content-Disposition": f"attachment; filename=tabel_gaji_{export_id}.xlsx"},
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@app.get("/export/potongan/{export_id}")
async def export_potongan(export_id: str) -> StreamingResponse | Response:
    """Export Excel file for potongan gaji by export ID"""
    file_path = f"result_excel/potongan_gaji_{export_id}.xlsx"

    if not os.path.exists(file_path):
        return Response("File Not Found!", status_code=404)

    with open(file_path, "rb") as file:
        file_data = file.read()

    return StreamingResponse(
        io.BytesIO(file_data),
        headers={"Content-Disposition": f"attachment; filename=potongan_gaji_{export_id}.xlsx"},
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
