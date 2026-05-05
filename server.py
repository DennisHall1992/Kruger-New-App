"""
Kruger Park Sightings – Rebuilt Server
------------------------------------

This FastAPI application powers the rebuilt version of the Kruger Park wildlife
sighting platform.  It exposes a RESTful API for listing and creating
sightings and serves static files for the client application.  Data is
stored persistently in a local SQLite database, while uploaded media files
are saved on disk under the `uploads/` directory.  The app is lightweight
yet ready for deployment to platforms like Render, Fly.io, or any
container‑based infrastructure.

Endpoints
---------
```
GET  /api/sightings         Retrieve all recorded sightings.
POST /api/sightings         Create a new sighting with optional images/videos.

Static files
------------
The frontend lives in the `frontend/` directory and is mounted at the root
URL.  Uploaded media in `uploads/` is mounted at `/uploads` for easy
access.

Running the server
------------------
Install dependencies (see requirements.txt) and launch the app with
uvicorn:

    uvicorn server:app --reload --host 0.0.0.0 --port 8000

The `--reload` flag watches for code changes.  In production, omit it.
"""

import os
import json
import sqlite3
import uuid
import datetime
from typing import List

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse


# Base directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
IMAGES_DIR = os.path.join(UPLOAD_DIR, "images")
VIDEOS_DIR = os.path.join(UPLOAD_DIR, "videos")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")


def init_storage() -> None:
    """Ensure required directories and database table exist."""
    os.makedirs(IMAGES_DIR, exist_ok=True)
    os.makedirs(VIDEOS_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS sightings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            species TEXT NOT NULL,
            description TEXT,
            lat REAL NOT NULL,
            lng REAL NOT NULL,
            images TEXT,
            videos TEXT,
            timestamp TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


# Initialize storage and database
init_storage()

app = FastAPI(title="Kruger Park Sightings API (Rebuilt)")

# Allow all origins during development.  In production, restrict this as needed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# Mount static directories unconditionally.  The frontend directory must
# exist in this rebuild; otherwise deployment will fail.
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.get("/api/sightings")
async def list_sightings():
    """Return all sightings as a JSON list, sorted by newest first."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM sightings ORDER BY datetime(timestamp) DESC"
    ).fetchall()
    conn.close()
    sightings: List[dict] = []
    for row in rows:
        images = json.loads(row["images"]) if row["images"] else []
        videos = json.loads(row["videos"]) if row["videos"] else []
        sightings.append(
            {
                "id": row["id"],
                "species": row["species"],
                "description": row["description"],
                "lat": row["lat"],
                "lng": row["lng"],
                "images": images,
                "videos": videos,
                "timestamp": row["timestamp"],
            }
        )
    return JSONResponse(content=sightings)


@app.post("/api/sightings")
async def create_sighting(
    species: str = Form(...),
    description: str = Form(""),
    lat: float = Form(...),
    lng: float = Form(...),
    images: List[UploadFile] = File([]),
    videos: List[UploadFile] = File([]),
):
    """Create a new sighting.

    Saves uploaded images and videos to disk.  Returns the created record.
    """
    species = species.strip()
    description = description.strip()
    if not species:
        raise HTTPException(status_code=400, detail="Species must not be empty.")
    timestamp = datetime.datetime.utcnow().isoformat()
    saved_images: List[str] = []
    saved_videos: List[str] = []

    # Helper to save each uploaded file
    async def save_files(files: List[UploadFile], target_dir: str, prefix: str) -> List[str]:
        saved_paths: List[str] = []
        for file in files:
            # Determine extension; fallback to .bin
            _, ext = os.path.splitext(file.filename or "")
            if not ext:
                ext = ".bin"
            # Use UUID to avoid collisions
            filename = f"{uuid.uuid4().hex}{ext}"
            file_path = os.path.join(target_dir, filename)
            # Persist file
            try:
                content = await file.read()
                with open(file_path, "wb") as f:
                    f.write(content)
            finally:
                await file.close()
            # Return public URL relative to root (mounted at /uploads)
            public_path = f"/uploads/{prefix}/{filename}"
            saved_paths.append(public_path)
        return saved_paths

    # Save images and videos
    if images:
        saved_images = await save_files(images, IMAGES_DIR, "images")
    if videos:
        saved_videos = await save_files(videos, VIDEOS_DIR, "videos")

    # Insert into database
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO sightings (species, description, lat, lng, images, videos, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            species,
            description,
            float(lat),
            float(lng),
            json.dumps(saved_images),
            json.dumps(saved_videos),
            timestamp,
        ),
    )
    sighting_id = c.lastrowid
    conn.commit()
    conn.close()

    return JSONResponse(
        content={
            "id": sighting_id,
            "species": species,
            "description": description,
            "lat": float(lat),
            "lng": float(lng),
            "images": saved_images,
            "videos": saved_videos,
            "timestamp": timestamp,
        },
        status_code=201,
    )
