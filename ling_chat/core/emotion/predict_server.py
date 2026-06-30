from contextlib import asynccontextmanager
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ling_chat.core.emotion.classifier import EmotionClassifier

classifier = None  # 初始化分类器


@asynccontextmanager
async def lifespan(app: FastAPI):
    global classifier
    try:
        classifier = EmotionClassifier.get_instance()
    except Exception as e:
        raise Exception(f"Failed to initialize classifier: {str(e)}") from e
    yield


app = FastAPI(
    title="Emotion Classification API",
    description="API for emotion classification using BERT model",
    version="1.0.0",
    lifespan=lifespan,
)


class PredictionRequest(BaseModel):
    text: str
    confidence_threshold: Optional[float] = 0.08


class EmotionResult(BaseModel):
    label: str
    probability: float


class PredictionResponse(BaseModel):
    label: str
    confidence: float
    top3: List[EmotionResult]
    warning: Optional[str] = None


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/predict", response_model=PredictionResponse)
async def predict_emotion(request: PredictionRequest):
    if classifier is None:
        raise HTTPException(status_code=500, detail="Classifier not initialized")
    try:
        confidence_threshold = (
            request.confidence_threshold
            if request.confidence_threshold is not None
            else 0.08
        )
        result = classifier.predict(request.text, confidence_threshold)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


if __name__ == "__main__":
    from ling_chat.configs.runtime_config import runtime_config

    host = runtime_config.get("emotion.emotion_bind_addr", "0.0.0.0")
    port = int(runtime_config.get("emotion.emotion_port", 8000))

    uvicorn.run(
        "predictor_server:app", host=host, port=port, workers=1, log_level="info"
    )
