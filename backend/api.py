from fastapi import FastAPI, Form
from search_engine import build_index_on_startup
from search_engine import run_real_search

build_index_on_startup()
app = FastAPI()

@app.get('/')
def root_page():
    return {'message': 'Hello World!'}

@app.post('/search/')
async def search(search_content: str = Form(...)):
    print(search_content)
    return run_real_search(search_content)