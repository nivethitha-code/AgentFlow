from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from datetime import datetime
from enum import Enum

class ModelType(str, Enum):
    LLAMA_3_3_70B = "llama-3.3-70b-versatile"
    LLAMA_3_1_8B = "llama-3.1-8b-instant"
    MIXTRAL_8X7B = "mixtral-8x7b-32768"
    GEMMA_7B = "gemma-7b-it"

class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class CompletionCriteria(BaseModel):
    type: str  # "contains", "regex", "llm_judge", "json_valid"
    value: Optional[str] = None
    instruction: Optional[str] = None # For LLM judge

class StepCreate(BaseModel):
    name: Optional[str] = None
    order: int
    prompt_template: str
    model: ModelType
    completion_criteria: CompletionCriteria
    retry_limit: int = 3

class WorkflowCreate(BaseModel):
    name: str
    steps: List[StepCreate]

class Step(StepCreate):
    id: str
    workflow_id: str

class Workflow(WorkflowCreate):
    id: str
    created_at: datetime
    steps: List[Step]

class RunStepResult(BaseModel):
    step_id: str
    step_name: Optional[str] = None
    status: StepStatus
    input_context: Optional[str]
    output: Optional[str]
    error: Optional[str]
    retries_used: int = 0
    cost: float = 0.0

class WorkflowRun(BaseModel):
    id: str
    workflow_id: str
    status: str # "running", "completed", "failed"
    current_step_index: int
    steps_results: List[RunStepResult]
    created_at: datetime
    updated_at: datetime
