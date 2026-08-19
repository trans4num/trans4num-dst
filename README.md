# trans4num-dst

This repository contains the open-source application code for Trans4num DST:

- `frontend/`: Vite, React, and TypeScript web application.
- `backend/`: FastAPI API service.
- `common/`: Shared Python data models used by the backend and engine.
- `engine/`: Optimization and simulation service.

## Run locally

The root `trans4num` CLI starts the engine, backend, and frontend together:

```bash
./trans4num
```

When the engine source files are not present, the CLI asks for the S3 URI that
contains them. It can also be supplied non-interactively:

```bash
./trans4num --source-data-uri s3://YOUR_SOURCE_BUCKET/YOUR_PREFIX
```

### Run with fake data

From a clean checkout, collaborators without access to the private source data
can generate a deterministic local dataset and start all services with:

```bash
./trans4num --fake-data
```

This creates 2,000 synthetic, non-overlapping grid fields, fake farm IDs,
randomized field values, a synthetic region fallback when needed, and starts
the default region with a Status Quo. No AWS access is required.

Keep the command running while using the application. Press Ctrl-C in that
terminal to stop the backend, frontend, and engine container.

The same URI can be stored in `TRANS4NUM_SOURCE_DATA_URI`. To initialize a
region with an idempotent Status Quo while starting locally, pass its UUID:

```bash
./trans4num --region REGION_ID
```

The CLI creates the local backend configuration and installs frontend
dependencies when needed. Press Ctrl-C to stop the backend and frontend; the
engine container is stopped as well. It runs the engine container as the
current host user so bind-mounted files remain writable. Empty bind-mount
directories previously created by Docker as root are repaired automatically.

Useful commands are:

```bash
./trans4num engine --region REGION_ID  # Start only the engine
./trans4num download                    # Download source data only
./trans4num stop                        # Stop the engine container
```

The backend uses the local file store and a local engine queue when started by
the CLI. Deployment infrastructure is maintained separately and is not
implemented by this repository's CLI.

### Prerequisites

- Node.js and npm for the frontend.
- Python 3 for fake-data generation.
- [Pixi](https://pixi.sh/) for the backend Python environment.
- Docker and Docker Compose for the engine.
- `curl` and the command-line tools required by the source-data download script.

### Manual service startup

The individual service commands remain available when separate terminals or
custom configuration are needed.

#### Start the backend

From the repository root, run:

```bash
cd backend
pixi run setup-config
mkdir -p src/data/regions src/data/simulations
pixi run start
```

The API is then available at `http://localhost:8000`. The API health check is
available at `http://localhost:8000/api/healthz`.

`pixi run setup-config` copies `backend/config.default.json` to
`backend/config.json` if no local configuration exists. The default local
login is:

```text
username: admin
password: change-me
```

Change these values, especially the token secret, before using the application
outside local development. `backend/config.json` is ignored by Git.

#### Start the frontend

In a second terminal, run:

```bash
cd frontend
npm ci
npm run dev
```

Open the URL printed by Vite, normally `http://localhost:5173`, and log in
with the default credentials above.

The frontend uses `http://localhost:8000/api/v1` by default. To use another
backend URL, set `VITE_API_BASE_URL` when starting or building the frontend:

```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1 npm run dev
```

### Data and engine limitations

Starting both services works with the repository contents, but the populated
region and simulation data is not committed to this repository. The local
backend therefore needs data under `backend/src/data/` to display regions and
simulations. That directory is intentionally ignored by Git; obtain the
prepared data separately if you need a populated local application.

The default fake job queue only logs newly created simulation jobs. It does not
run the optimizer.

### Run the engine locally

The engine can be run in Docker using the local file store. First make sure
the source files described in the [engine README](./engine/README.md) are
available in `engine/data`, then start the container from the repository root:

```bash
docker compose up --build engine
```

To download missing source files, start the container, and initialize a region
with a Status Quo in one step, use the compatibility wrapper:

```bash
export TRANS4NUM_SOURCE_DATA_URI=s3://YOUR_SOURCE_BUCKET/YOUR_PREFIX
./start-local-engine.sh REGION_ID
```

The wrapper delegates to `./trans4num engine`, skips downloading files that are
already present, leaves the engine running in Docker, and ensures that Status
Quo exists for the selected region.
If Status Quo already exists, the engine skips recomputing it. Replace
`REGION_ID` with the UUID of the region to initialize. Stop the container with
`docker compose down` when finished.

The backend still needs the region metadata under
`backend/src/data/regions/<REGION_ID>/` before the frontend can list the
region. The engine setup creates the Status Quo and generated simulation files;
it does not create that metadata.

The container listens for Lambda-style invocations at
`http://localhost:8080/2015-03-31/functions/function/invocations`. The compose
configuration mounts `engine/data` and `backend/src/data/simulations` into the
container so the engine and backend use the same local files.

To let the backend submit jobs to the container, start it with the local
engine queue enabled:

```bash
cd backend
TRANS4NUM_ENGINE_JOB_QUEUE_TYPE=local \
TRANS4NUM_ENGINE_JOB_QUEUE_URL=http://localhost:8080/2015-03-31/functions/function/invocations \
pixi run start
```

The local queue invokes the engine in the background, so creating a simulation
returns immediately while the engine updates its files. The default `fake`
queue remains available when the engine is not running.

The engine expects a Status Quo simulation to exist before the frontend can
show alternatives. It can be created through the local invocation endpoint by
posting an event with `create_status_quo` set to `true`:

```bash
curl -X POST http://localhost:8080/2015-03-31/functions/function/invocations \
  -H 'Content-Type: application/json' \
  --data '{"Records":[{"body":"{\"region\":\"REGION_ID\",\"create_status_quo\":true}"}]}'
```

Replace `REGION_ID` with the region UUID. See `engine/src/handler.py` for the
event shape and the required source data.
