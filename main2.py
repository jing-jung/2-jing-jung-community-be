from fastapi import FastAPI, HTTPException
from typing import Dict

app = FastAPI()

@app.post("/posts")
def create_post(post: Dict):
    if "title" in post and "content" in post and "writer" in post:
        pass
    else:
        raise HTTPException(status_code=400, detail="Missing required fields")

    if isinstance(post["title"], str) and isinstance(post["content"], str) and isinstance(post["writer"], str):
        pass
    else:
        raise HTTPException(status_code=400, detail="Invalid data type")

    response_data = {
        "title": post["title"],
        "content": post["content"],
        "writer": post["writer"],
        "status": "saved"
    }

    return {
        "message": "create_success",
        "data": response_data
    }
