from contextlib import asynccontextmanager
from fastapi import FastAPI, Form
from search_engine import build_index_on_startup
from search_engine import run_real_search


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("--- Aplication startup ---")
    print("Loading Search Engine")
    build_index_on_startup()
    print("Finished loading search engine")
    yield
    print("Shutting down. . .")



app = FastAPI(lifespan=lifespan)

@app.get('/')
def root_page():
    return {'message': 'Hello World!'}

@app.post('/search/')
async def search(search_content: str = Form(...)):
    print(search_content)
    return run_real_search(search_content)