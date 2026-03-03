import os

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from dataset_summary import (
    DEFAULT_BASE_URL,
    DEFAULT_MODEL,
    generate_summaries,
    generate_mock_summaries,
    read_csv_rows_from_bytes,
    read_rows_from_bytes,
)

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok", "service": "sample"}


@app.get("/")
def index() -> FileResponse:
    return FileResponse("index.html")


@app.post("/api/summarize")
def summarize(
    file: UploadFile = File(...),
    sheet: str | None = Form(default=None),
    group_key: str | None = Form(default=None),
    org_name: str | None = Form(default=None),
    include_rows: bool = Form(default=False),
    mock: bool = Form(default=False),
    include_prompt: bool = Form(default=False),
    include_debug: bool = Form(default=False),
    header_start: str | None = Form(default=None),
    header_end: str | None = Form(default=None),
) -> JSONResponse:
    use_mock = mock or os.environ.get("MOCK_MODE") == "1"
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key and not use_mock:
        raise HTTPException(status_code=400, detail="Missing GEMINI_API_KEY/OPENAI_API_KEY.")
    if not org_name or not org_name.strip():
        raise HTTPException(status_code=400, detail="Missing org_name.")

    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename.")

    data = file.file.read()
    header_range = (header_start, header_end) if header_start and header_end else None
    header_debug = None
    if file.filename.endswith(".xlsx"):
        try:
            if include_debug:
                rows, header_debug = read_rows_from_bytes(
                    data, sheet, header_range=header_range, return_debug=True
                )
            else:
                rows = read_rows_from_bytes(data, sheet, header_range=header_range)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    elif file.filename.endswith(".csv"):
        try:
            if include_debug:
                rows, header_debug = read_csv_rows_from_bytes(
                    data, header_range=header_range, return_debug=True
                )
            else:
                rows = read_csv_rows_from_bytes(data, header_range=header_range)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    else:
        raise HTTPException(status_code=400, detail="Only .xlsx or .csv files are supported.")
    if not rows:
        raise HTTPException(status_code=400, detail="No rows found.")

    if use_mock:
        results = generate_mock_summaries(
            rows,
            group_key,
            include_rows=include_rows,
            include_prompt=include_prompt,
            org_name=org_name,
            header_debug=header_debug if include_debug else None,
        )
    else:
        results = generate_summaries(
            rows,
            group_key,
            DEFAULT_BASE_URL,
            api_key,
            DEFAULT_MODEL,
            include_rows=include_rows,
            include_prompt=include_prompt,
            org_name=org_name,
            header_debug=header_debug if include_debug else None,
        )
    if include_debug:
        return JSONResponse({"results": results, "debug": header_debug})
    return JSONResponse(results)
