# Kruger Park Sightings – New App

This project is a fully functional version of the Kruger Park sightings platform, combining a Python FastAPI backend with a modern, dark‑themed frontend powered by Leaflet.  Sightings (including images and videos) are stored persistently in a SQLite database under `database.db`, while uploaded media files are saved in the `uploads/` directory.  The app loads Leaflet from a CDN to avoid broken dependencies and is ready for deployment to services such as Render or any container‑based platform.

## Features

* **Interactive map** – Users can click on the map to select the latitude and longitude for a sighting.  Existing sightings are rendered as markers with pop‑ups showing species, description and attached media.
* **Media uploads** – The submission form accepts multiple images and videos.  Files are stored under `uploads/images/` and `uploads/videos/` and served back to the client.
* **Persistent storage** – Sightings are stored in a SQLite database (`database.db`).  Data persists across server restarts.
* **Modern UI** – A dark‑themed user interface with a floating action button and modal form makes it easy to add new sightings.  All styling is defined in `frontend/style.css`.

## Directory Structure

```
Project/
├── server.py           # FastAPI server with API endpoints and static file serving
├── requirements.txt    # Python dependencies
├── database.db         # SQLite database (auto‑created if missing)
├── uploads/
│   ├── images/         # Uploaded images
│   └── videos/         # Uploaded videos
└── frontend/
    ├── index.html      # Main HTML page
    ├── app.js          # Front‑end JavaScript
    └── style.css       # CSS styling
```

## Running Locally

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Launch the server:

   ```bash
   uvicorn server:app --reload
   ```

3. Navigate to `http://localhost:8000` in your browser to use the app.

## Deployment

Deploy this application to any service that supports running Python.  For example, on Render you can configure:

* **Build command**: `pip install -r requirements.txt`
* **Start command**: `uvicorn server:app --host 0.0.0.0 --port $PORT`

## Notes

Leaflet assets (CSS and JS) are loaded from a CDN (`unpkg.com`).  If your deployment environment restricts outbound HTTP requests, you can download the Leaflet files and place them in a local folder inside `frontend/`, then update the `<link>` and `<script>` tags in `index.html` accordingly.
