from fastapi import FastAPI
from utils import initiate_flow
app = FastAPI()
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In dev, "*" is OK; in prod, be specific
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Mermaid API!"}
class Page(BaseModel):
    title: str

@app.post("/generate-mermaid-code")
def generate_mermaid_code(page: Page):
    mermaid_code = initiate_flow(page.title)
    return {"mermaid_code": mermaid_code}
