from contextlib import asynccontextmanager
from fastapi import FastAPI, Form
from search_engine import build_index_on_startup
from search_engine import run_real_search
import asyncio

index_ready = asyncio.Event()

async def start_engine():
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, build_index_on_startup)
    index_ready.set()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("--- Aplication startup ---")
    print("Loading Search Engine")
    asyncio.create_task(start_engine())
    print("Finished loading search engine")
    yield
    print("Shutting down. . .")



app = FastAPI(lifespan=lifespan)

@app.get('/')
def root_page():
    return {'message': 'Hello World!'}

@app.post('/search/')
async def search(search_content: str = Form(...)):

    if not index_ready.is_set():
        return {'error': 'El motor esta inicializandose...'}, 503

    print(search_content)

    return run_real_search(search_content)