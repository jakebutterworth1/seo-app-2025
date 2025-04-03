from fastapi import FastAPI
from app.routes import analyze, estimates, rewrite  # ✅ Import your custom route modules

app = FastAPI()

# ✅ Register routes with FastAPI
app.include_router(analyze.router)
app.include_router(estimates.router)
app.include_router(rewrite.router)

@app.get("/")
def read_root():
    return {"message": "Hello from your SEO app backend!"}
