"""Convert a model response into a Pydantic object, then apply business validation."""

import os
from typing import Literal

from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field


class SupportTriage(BaseModel):
    priority: Literal["low", "medium", "high"] = Field(
        description="Urgency for a customer-support ticket."
    )
    summary: str = Field(description="A concise, neutral summary of the customer issue.")
    needs_human: bool = Field(description="Whether a human should review the request.")


def main() -> None:
    model = init_chat_model(os.getenv("LC_MODEL", "openai:gpt-4.1-mini"), temperature=0)
    triage_model = model.with_structured_output(SupportTriage)
    triage = triage_model.invoke(
        "Customer says: I was charged twice for my annual plan and I cannot access invoices."
    )

    print(triage.model_dump_json(indent=2))

    # Shape validation succeeded. This is separate application policy.
    if triage.priority == "high" and not triage.needs_human:
        raise ValueError("Business rule violation: high priority tickets require human review.")


if __name__ == "__main__":
    main()
