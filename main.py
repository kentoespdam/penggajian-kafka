import asyncio
import io
import os
from contextlib import asynccontextmanager

from aiokafka import AIOKafkaConsumer
from fastapi import HTTPException, UploadFile, FastAPI
from fastapi.responses import StreamingResponse, Response

from core.config import KAFKA_TOPIC, KAFKA_SERVER, KAFKA_GROUP_ID, LOGGER
from core.models.gaji_batch_root import exists_gaji_batch_root_by_id
from core.process_gaji.additional_potongan import process_excel
from core.process_gaji.consumer import consume_proses_gaji
from core.process_gaji.phase3 import build_himpunan_gaji

# Extracted constants for clarity and reuse
API_TITLE = "Proses Penggajian"
API_DESCRIPTION = "API proses penggajian Kepegawaian"
API_VERSION = "1.0.0"

MSG_UNKNOWN_BATCH = "Unknown Gaji Batch ID"
MSG_SUCCESS = "Success"


@asynccontextmanager
async def lifespan(app: FastAPI):
    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_SERVER,
        group_id=KAFKA_GROUP_ID,
        enable_auto_commit=False,
        value_deserializer=lambda x: x.decode("utf-8"),
        max_poll_records=10,
        session_timeout_ms=60000,
        heartbeat_interval_ms=20000
    )
    await consumer.start()
    task = asyncio.create_task(consume_proses_gaji(consumer))
    LOGGER.info("Kafka consumer started, waiting for messages...")
    yield
    task.cancel()
    await consumer.stop()
    LOGGER.info("Kafka consumer stopped")


app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    lifespan=lifespan,
)


@app.get("/export/regenerate/{export_id}", status_code=200)
async def regenerate_export(export_id: str) -> Response:
    """
    Regenerate export artifacts for the given batch export_id.
    Raises:
        HTTPException(404): if batch ID does not exist or is invalid.
    """
    if not exists_gaji_batch_root_by_id(export_id):
        raise HTTPException(status_code=404, detail=MSG_UNKNOWN_BATCH)

    build_himpunan_gaji(export_id)
    return Response(status_code=200, content=MSG_SUCCESS)


@app.get("/export/table_gaji/{export_id}", status_code=200)
async def table_gaji(export_id: str):
    path_file = f"result_excel/daftar_gaji_{export_id}.xlsx"
    if not os.path.exists(path_file):
        return Response("File Not Found!", status_code=404)

    with open(path_file, "rb") as f:
        data = f.read()
        return StreamingResponse(
            io.BytesIO(data),
            headers={
                "Content-Disposition": f"attachment; filename=tabel_gaji_{export_id}.xlsx"},
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


@app.get("/export/potongan/{export_id}")
async def potongan(export_id: str):
    path_file = f"result_excel/potongan_gaji_{export_id}.xlsx"
    if not os.path.exists(path_file):
        raise HTTPException(status_code=404, detail="File Not Found!")

    with open(path_file, "rb") as f:
        data = f.read()
        return StreamingResponse(
            io.BytesIO(data),
            headers={
                "Content-Disposition": f"attachment; filename=potongan_gaji_{export_id}.xlsx"},
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


@app.patch("/upload/{root_batch_id}/additional_gaji", status_code=200)
async def upload_additional(root_batch_id: str, file: UploadFile):
    if not exists_gaji_batch_root_by_id(root_batch_id) or file is None:
        raise HTTPException(status_code=500, detail="Unknown Gaji Batch ID")

    await process_excel(root_batch_id, file)
    return Response("Success", status_code=200)
