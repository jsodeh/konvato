
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sys
import os

# Add the current directory to the path to allow importing other modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from convert_betslip import convert_betslip

app = FastAPI(
    title="Betslip Converter Automation API",
    description="An API for converting betslip codes between bookmakers using AI-powered browser automation.",
    version="1.0.0"
)

class ConversionRequest(BaseModel):
    betslip_code: str
    source_bookmaker: str
    destination_bookmaker: str

@app.post("/convert")
async def handle_conversion(request: ConversionRequest):
    """
    Receives a betslip conversion request, processes it, and returns the result.
    """
    try:
        result = await convert_betslip(
            request.betslip_code,
            request.source_bookmaker,
            request.destination_bookmaker
        )
        if result and result.get("success"):
            return result
        else:
            # Log the full error for debugging
            print(f"Conversion failed: {result.get('error')}")
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown conversion error"))
    except Exception as e:
        print(f"Unhandled exception during conversion: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@app.get("/health")
def health_check():
    """
    Simple health check endpoint.
    """
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
