from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from backend import GroqRateLimitError, run_travel_agent


class TravelRequest(BaseModel):
	user_input: str = Field(
		...,
		min_length=1,
		max_length=4_000,
		description="The travel request to plan.",
	)
	thread_id: str | None = Field(
		default=None,
		min_length=1,
		max_length=200,
		description="Optional conversation identifier for continuing a trip plan.",
	)

	@field_validator("user_input")
	@classmethod
	def validate_user_input(cls, value: str) -> str:
		value = value.strip()
		if not value:
			raise ValueError("user_input must contain non-whitespace text")
		return value


class TravelResponse(BaseModel):
	thread_id: str
	answer: str
	flight_results: str
	hotel_results: str
	itinerary: str
	llm_calls: int


app = FastAPI(
	title="TripMate Travel API",
	version="1.0.0",
	description="AI-powered travel planning API.",
)

app.add_middleware(
	CORSMiddleware,
	allow_origins=[
		"http://localhost:3000",
		"http://localhost:5173",
		"http://127.0.0.1:3000",
		"http://127.0.0.1:5173",
	],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)


@app.get("/", tags=["Health"])
def root() -> dict[str, str]:
	return {"name": "TripMate Travel API", "status": "ok"}


@app.get("/health", tags=["Health"])
def health() -> dict[str, str]:
	return {"status": "ok"}


@app.post("/api/travel", response_model=TravelResponse, tags=["Travel"])
def create_travel_plan(request: TravelRequest) -> dict[str, Any]:
	try:
		return run_travel_agent(
			user_input=request.user_input.strip(),
			thread_id=request.thread_id,
		)
	except GroqRateLimitError as error:
		raise HTTPException(
			status_code=429,
			detail=str(error),
			headers={"Retry-After": "60"},
		) from error
	except Exception as error:
		raise HTTPException(
			status_code=502,
			detail=f"Travel agent failed: {error}",
		) from error
