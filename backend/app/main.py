import asyncio
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import uuid
import json
import logging
from datetime import datetime

from app.models import WorkflowCreate, Workflow, WorkflowRun, RunStepResult, StepStatus, Step
from app.database import supabase
from app.service import LLMService

# Initialize App
app = FastAPI(title="Agentic Workflow Builder API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for hackathon; restrict in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

service = LLMService()
logger = logging.getLogger(__name__)

# --- Helper Functions ---

def get_workflow(workflow_id: str) -> Workflow:
    response = supabase.table("workflows").select("*").eq("id", workflow_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Workflow not found")
    data = response.data[0]
    # Parse definition to steps
    steps_data = data["definition"]
    steps = [Step(**s, workflow_id=workflow_id, id=str(uuid.uuid4())) for s in steps_data] # Assign temp IDs to steps if needed or use index
    
    return Workflow(
        id=data["id"],
        name=data["name"],
        created_at=data["created_at"],
        steps=steps
    )

async def execute_workflow_task(run_id: str, workflow_id: str):
    """
    Background task to execute the workflow steps sequentially.
    """
    logger.info(f"Starting execution for run {run_id}")
    
    # 1. Fetch Workflow Definition
    try:
        workflow = get_workflow(workflow_id)
    except Exception as e:
        logger.error(f"Failed to fetch workflow: {e}")
        # Mark run as failed immediately
        try:
             supabase.table("workflow_runs").update({
                "status": "failed",
                "steps_results": [{"error": f"Failed to initiate workflow: {str(e)}"}]
            }).eq("id", run_id).execute()
        except Exception as db_e:
            logger.error(f"Failed to update run status to failed: {db_e}")
        return

    # 2. Update Run Status to Running
    try:
        supabase.table("workflow_runs").update({"status": "running"}).eq("id", run_id).execute()
    except Exception as e:
        logger.error(f"Failed to set status to running: {e}")
        return
    
    context = ""
    results = []
    
    for index, step in enumerate(workflow.steps):
        # Update current step index
        try:
            supabase.table("workflow_runs").update({
                "current_step_index": index
            }).eq("id", run_id).execute()
        except Exception as e:
            logger.warning(f"Failed to update step index: {e}")

        step_result = RunStepResult(
            step_id=str(index), # Using index as ID for simplicity in front
            step_name=step.name,
            status=StepStatus.RUNNING,
            input_context=context,
            output=None,
            error=None
        )
        # Optimistic update of results array (append running step)
        try:
            current_results = results + [step_result.model_dump()]
            supabase.table("workflow_runs").update({"steps_results": current_results}).eq("id", run_id).execute()
        except Exception as e:
             logger.warning(f"Failed to update step results (optimistic): {e}")

        # Prepare Prompt
        base_prompt = step.prompt_template.replace("{{context}}", context)

        # If criteria is json_valid, instruct the LLM explicitly to return JSON
        if step.completion_criteria.type == "json_valid":
            base_prompt += "\n\nIMPORTANT: You MUST respond with valid JSON only. Do not include any explanation, markdown, or extra text — only a raw JSON object or array."
        elif step.completion_criteria.type == "contains" and step.completion_criteria.value:
            terms = [t.strip() for t in step.completion_criteria.value.split(",") if t.strip()]
            if terms:
                base_prompt += f"\n\nIMPORTANT: Your response MUST include the following term(s): {', '.join(terms)}."

        prompt = base_prompt
        retries = 0
        success = False
        final_output = ""
        last_error = None
        
        # Step Execution Loop (retry_limit = max number of retries after first attempt)
        while retries < step.retry_limit and not success:
            try:
                # Call LLM
                response = await service.call_llm(step.model, prompt)
                output = response['choices'][0]['message']['content']
                
                # Check Criteria
                is_valid = await service.validate_output(output, step.completion_criteria)
                
                if is_valid:
                    success = True
                    final_output = output
                else:
                    retries += 1
                    last_error = f"Criteria '{step.completion_criteria.type}' not met. Output: {output[:100]}..."
                    logger.info(f"Step {index} validation failed. Retry {retries}/{step.retry_limit}")
                    # Refine prompt for retry with explicit reminder
                    if step.completion_criteria.type == "json_valid":
                        prompt = base_prompt + f"\n\nPrevious attempt failed — your response was not valid JSON. Try again with ONLY a JSON object or array."
                    else:
                        prompt = base_prompt + f"\n\nPrevious attempt failed (criteria: {step.completion_criteria.type}). Please try again carefully."

            except Exception as e:
                logger.error(f"Step {index} error: {e}")
                last_error = str(e)
                retries += 1
                # Optional: exponential backoff here
        
        # Step Conclusion
        step_result.retries_used = retries
        if success:
            step_result.status = StepStatus.COMPLETED
            step_result.output = final_output
            context = final_output # Update context for next step
        else:
            step_result.status = StepStatus.FAILED
            # Use specific error if available, else generic
            step_result.error = f"Failed after {retries} retries. Last error: {last_error}" if last_error else "Max retries reached. Validation criteria not met."
            results.append(step_result.model_dump())
            
            # Fail the whole run
            try:
                supabase.table("workflow_runs").update({
                    "status": "failed",
                    "steps_results": results
                }).eq("id", run_id).execute()
            except Exception as e:
                logger.error(f"Failed to update run status to failed after step error: {e}")
            return # Stop execution

        results.append(step_result.model_dump())
        # Update run with latest completed step
        try:
            supabase.table("workflow_runs").update({"steps_results": results}).eq("id", run_id).execute()
        except Exception as e:
             logger.error(f"Failed to save step completion: {e}")

    # Workflow Completed
    try:
        supabase.table("workflow_runs").update({"status": "completed"}).eq("id", run_id).execute()
        logger.info(f"Run {run_id} completed successfully")
    except Exception as e:
        logger.error(f"Failed to mark run as completed: {e}")



async def execute_step_task(run_id: str, step_index: int):
    """
    Background task to execute a single workflow step.
    """
    logger.info(f"Re-running step {step_index} for run {run_id}")
    
    try:
        # 1. Fetch Run and Workflow
        run_res = supabase.table("workflow_runs").select("*").eq("id", run_id).execute()
        if not run_res.data:
            return
        run_data = run_res.data[0]
        workflow_id = run_data["workflow_id"]
        results = run_data["steps_results"]
        
        workflow = get_workflow(workflow_id)
        if step_index >= len(workflow.steps):
            return
            
        step = workflow.steps[step_index]
        
        # 2. Get context from previous step
        context = ""
        if step_index > 0:
            if step_index - 1 < len(results):
                context = results[step_index - 1].get("output", "")
        
        # 3. Update step status to running
        step_result = RunStepResult(
            step_id=str(step_index),
            step_name=step.name,
            status=StepStatus.RUNNING,
            input_context=context,
            output=None,
            error=None
        )
        
        # Update results array at specific index
        if step_index < len(results):
            results[step_index] = step_result.model_dump()
        else:
            # Should not happen if history is consistent, but handle anyway
            while len(results) < step_index:
                results.append({"status": "pending"})
            results.append(step_result.model_dump())
            
        supabase.table("workflow_runs").update({"steps_results": results}).eq("id", run_id).execute()

        # 4. Prepare Prompt
        base_prompt = step.prompt_template.replace("{{context}}", context)
        if step.completion_criteria.type == "json_valid":
            base_prompt += "\n\nIMPORTANT: You MUST respond with valid JSON only. Do not include any explanation, markdown, or extra text — only a raw JSON object or array."
        elif step.completion_criteria.type == "contains" and step.completion_criteria.value:
            terms = [t.strip() for t in step.completion_criteria.value.split(",") if t.strip()]
            if terms:
                base_prompt += f"\n\nIMPORTANT: Your response MUST include the following term(s): {', '.join(terms)}."

        prompt = base_prompt
        retries = 0
        success = False
        final_output = ""
        last_error = None
        
        # Step Execution Loop
        while retries < step.retry_limit and not success:
            try:
                response = await service.call_llm(step.model, prompt)
                output = response['choices'][0]['message']['content']
                is_valid = await service.validate_output(output, step.completion_criteria)
                
                if is_valid:
                    success = True
                    final_output = output
                else:
                    retries += 1
                    last_error = f"Criteria '{step.completion_criteria.type}' not met."
                    if step.completion_criteria.type == "json_valid":
                        prompt = base_prompt + f"\n\nPrevious attempt failed — your response was not valid JSON. Try again with ONLY a JSON object or array."
                    else:
                        prompt = base_prompt + f"\n\nPrevious attempt failed. Please try again carefully."
            except Exception as e:
                logger.error(f"Step {step_index} retry {retries} error: {e}")
                last_error = str(e)
                retries += 1
        
        # 5. Step Conclusion
        step_result.retries_used = retries
        if success:
            step_result.status = StepStatus.COMPLETED
            step_result.output = final_output
        else:
            step_result.status = StepStatus.FAILED
            step_result.error = f"Failed after {retries} retries. Last error: {last_error}"
            
        results[step_index] = step_result.model_dump()
        
        # Determine overall run status
        all_completed = all(r.get("status") == "completed" for r in results)
        any_failed = any(r.get("status") == "failed" for r in results)
        
        new_status = run_data["status"]
        if all_completed:
            new_status = "completed"
        elif any_failed:
            new_status = "failed"
        
        supabase.table("workflow_runs").update({
            "steps_results": results,
            "status": new_status
        }).eq("id", run_id).execute()
        
    except Exception as e:
        logger.error(f"Error in execute_step_task: {e}")

# --- Endpoints ---


@app.post("/workflows")
async def create_workflow(workflow: WorkflowCreate):
    """Save a new workflow definition."""
    try:
        data = {
            "name": workflow.name,
            "definition": [step.model_dump() for step in workflow.steps]
        }
        response = supabase.table("workflows").insert(data).execute()
        return response.data[0]
    except Exception as e:
        logger.error(f"Error creating workflow: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create workflow: {str(e)}")

@app.get("/workflows")
async def list_workflows():
    try:
        response = supabase.table("workflows").select("*").order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        logger.error(f"Error listing workflows: {e}")
        raise HTTPException(status_code=500, detail="Failed to list workflows")

@app.post("/run/{workflow_id}")
async def run_workflow(workflow_id: str, background_tasks: BackgroundTasks):
    """Trigger a workflow run."""
    try:
        # Create valid UUID for run
        # Insert pending run
        run_data = {
            "workflow_id": workflow_id,
            "status": "pending",
            "current_step_index": 0,
            "steps_results": []
        }
        response = supabase.table("workflow_runs").insert(run_data).execute()
        if not response.data:
             raise Exception("Failed to insert run into database")
             
        run_id = response.data[0]["id"]
        
        # Start Background Task
        background_tasks.add_task(execute_workflow_task, run_id, workflow_id)
        
        return {"run_id": run_id, "status": "pending"}
    except Exception as e:
        logger.error(f"Error starting workflow run: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start workflow: {str(e)}")

@app.get("/history")
async def get_history():
    """Get recent runs."""
    try:
        # Note: 'workflows(name)' requires a foreign key relationship to be detected by PostgREST
        response = supabase.table("workflow_runs").select("*, workflows(name)").order("created_at", desc=True).limit(50).execute()
        return response.data
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        # Fallback query without join if that fails?
        try:
             logger.info("Attempting fallback history query without join")
             response = supabase.table("workflow_runs").select("*").order("created_at", desc=True).limit(50).execute()
             return response.data
        except Exception as fallback_e:
             logger.error(f"Fallback history fetch failed: {fallback_e}")
             raise HTTPException(status_code=500, detail="Failed to fetch history")

@app.get("/run/{run_id}")
async def get_run_status(run_id: str):
    response = supabase.table("workflow_runs").select("*").eq("id", run_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Run not found")
    return response.data[0]

@app.delete("/run/{run_id}")
async def delete_run(run_id: str):
    """Delete a workflow run."""
    try:
        supabase.table("workflow_runs").delete().eq("id", run_id).execute()
        return {"status": "deleted"}
    except Exception as e:
        logger.error(f"Error deleting run: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete run: {str(e)}")

@app.delete("/workflow/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """Delete a workflow permanently."""
    try:
        supabase.table("workflows").delete().eq("id", workflow_id).execute()
        return {"status": "deleted"}
    except Exception as e:
        logger.error(f"Error deleting workflow: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete workflow: {str(e)}")

@app.post("/run/{run_id}/step/{step_index}")
async def run_single_step(run_id: str, step_index: int, background_tasks: BackgroundTasks):
    """Trigger a single step execution."""
    try:
        background_tasks.add_task(execute_step_task, run_id, step_index)
        return {"status": "queued", "step_index": step_index}
    except Exception as e:
        logger.error(f"Error starting single step run: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start step run: {str(e)}")
