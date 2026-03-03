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
    steps = [Step(**s, workflow_id=workflow_id) for s in steps_data]
    
    return Workflow(
        id=data["id"],
        name=data["name"],
        created_at=data["created_at"],
        steps=steps
    )

async def execute_task(run_id: str, step: Step, context: str, results: List[Dict]):
    """Helper to execute a single task step."""
    logger.info(f"Executing step {step.name} ({step.id})")
    
    step_result = RunStepResult(
        step_id=step.id,
        step_name=step.name,
        status=StepStatus.RUNNING,
        input_context=context,
        output=None,
        error=None
    )
    
    # Update status in DB
    try:
        # Find the index of this step in the results list, or append if new
        step_index = -1
        for i, res in enumerate(results):
            if res.get("step_id") == step.id:
                step_index = i
                break
        
        if step_index != -1:
            results[step_index] = step_result.model_dump()
        else:
            results.append(step_result.model_dump())

        supabase.table("workflow_runs").update({"steps_results": results}).eq("id", run_id).execute()
    except Exception as e:
        logger.warning(f"Failed to update step status to running: {e}")

    # Prepare Prompt
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
                last_error = f"Criteria '{step.completion_criteria.type}' not met. Output: {output[:100]}..."
                # Refine prompt for retry with explicit reminder
                if step.completion_criteria.type == "json_valid":
                    prompt = base_prompt + f"\n\nPrevious attempt failed — your response was not valid JSON. Try again with ONLY a JSON object or array."
                else:
                    prompt = base_prompt + f"\n\nPrevious attempt failed (criteria: {step.completion_criteria.type}). Please try again carefully."
        except Exception as e:
            logger.error(f"Step {step.id} error: {e}")
            last_error = str(e)
            retries += 1
    
    step_result.retries_used = retries
    if success:
        step_result.status = StepStatus.COMPLETED
        step_result.output = final_output
    else:
        step_result.status = StepStatus.FAILED
        step_result.error = f"Failed after {retries} retries. Last error: {last_error}" if last_error else "Max retries reached. Validation criteria not met."
    
    # Update final result for this step
    # Find the index of this step in the results list, or append if new
    step_index = -1
    for i, res in enumerate(results):
        if res.get("step_id") == step.id:
            step_index = i
            break
    
    if step_index != -1:
        results[step_index] = step_result.model_dump()
    else:
        results.append(step_result.model_dump())

    try:
        supabase.table("workflow_runs").update({"steps_results": results}).eq("id", run_id).execute()
    except Exception as e:
        logger.error(f"Failed to save step result: {e}")
    
    return step_result

async def execute_workflow_task(run_id: str, workflow_id: str):
    """
    Background task to execute the workflow graph.
    """
    logger.info(f"Starting GRAPH execution for run {run_id}")
    
    try:
        workflow = get_workflow(workflow_id)
        # 1. Update Run Status to Running
        supabase.table("workflow_runs").update({"status": "running"}).eq("id", run_id).execute()
        
        # Build map for easy lookup
        steps_map = {s.id: s for s in workflow.steps}
        # Start with step marked as order 0 (or find root)
        current_steps = [s for s in workflow.steps if s.order == 0]
        
        # Fetch existing results if any (for re-runs or partial runs)
        run_res = supabase.table("workflow_runs").select("steps_results").eq("id", run_id).execute()
        results = run_res.data[0]["steps_results"] if run_res.data and run_res.data[0]["steps_results"] else []

        # Keep track of completed step outputs for context
        completed_outputs = {}
        for res in results:
            if res.get("status") == StepStatus.COMPLETED and res.get("output") is not None:
                completed_outputs[res["step_id"]] = res["output"]

        last_batch_outputs = [] # Tracks outputs of the immediately preceding batch for merging

        while current_steps:
            next_queue = []
            
            # If multiple current steps, run in parallel!
            if len(current_steps) > 1:
                # Parallel Execution Logic
                tasks = []
                for s in current_steps:
                    # For parallel, context is typically from a common ancestor or empty
                    # For simplicity, we'll use the output of the *last* completed step that is an ancestor
                    # or an empty string if no relevant context is found.
                    # A more robust solution would involve explicit context passing or merging.
                    
                    # For now, let's assume parallel steps don't strictly depend on each other's immediate output
                    # and might use a shared initial context or context from a single preceding step.
                    # If a step has 'input_step_id', use that. Otherwise, use empty.
                    context_for_parallel_step = ""
                    if s.input_step_id and s.input_step_id in completed_outputs:
                        context_for_parallel_step = completed_outputs[s.input_step_id]
                    
                    tasks.append(execute_task(run_id, s, context_for_parallel_step, results))
                
                step_results = await asyncio.gather(*tasks)
                
                last_batch_outputs = []
                
                # Determine next steps for each
                for i, s_res in enumerate(step_results):
                    if s_res.status == StepStatus.COMPLETED:
                        completed_outputs[s_res.step_id] = s_res.output # Store output for future context
                        last_batch_outputs.append((s_res.step_id, s_res.output))
                        step_obj = current_steps[i]
                        for branch in step_obj.next_steps:
                             if branch.next_step_id and steps_map[branch.next_step_id] not in next_queue:
                                 next_queue.append(steps_map[branch.next_step_id])
                    else:
                        # A parallel step failed, fail the whole workflow
                        supabase.table("workflow_runs").update({"status": "failed"}).eq("id", run_id).execute()
                        logger.error(f"Workflow {workflow_id} run {run_id} failed due to parallel step {s_res.step_id} failure.")
                        return
            else: # Single step execution
                s = current_steps[0]
                
                # Determine context for the current step
                context_for_step = ""
                if s.input_step_id and s.input_step_id in completed_outputs:
                    context_for_step = completed_outputs[s.input_step_id]
                elif len(last_batch_outputs) > 1:
                    # Merge contexts from parallel steps automatically
                    merged = []
                    for idx, (out_id, out_text) in enumerate(last_batch_outputs):
                        # Use step name if available for clearer context
                        step_name = steps_map[out_id].name if out_id in steps_map else out_id
                        merged.append(f"--- Output from Parallel Task '{step_name}' ---\n{out_text}")
                    context_for_step = "\n\n".join(merged)
                elif last_batch_outputs and last_batch_outputs[0][1]:
                    context_for_step = last_batch_outputs[0][1]
                elif results: # Fallback to last completed step's output if no specific input_step_id
                    for res in reversed(results):
                        if res.get("status") == StepStatus.COMPLETED and res.get("output") is not None:
                            context_for_step = res["output"]
                            break
                
                res = await execute_task(run_id, s, context_for_step, results)
                
                last_batch_outputs = []
                if res.status == StepStatus.COMPLETED:
                    completed_outputs[res.step_id] = res.output # Store output for future context
                    last_batch_outputs.append((res.step_id, res.output))
                    # Branching / Routing Logic
                    if s.type == "router":
                        # Match res.output against branch labels
                        label = res.output.strip().upper()
                        next_id = None
                        for branch in s.next_steps:
                            if branch.condition and branch.condition.upper() in label:
                                next_id = branch.next_step_id
                                break
                        # Fallback to DEFAULT branch if label not found
                        if not next_id:
                            for branch in s.next_steps:
                                if branch.condition == "DEFAULT":
                                    next_id = branch.next_step_id
                                    break
                        
                        if next_id and steps_map[next_id] not in next_queue:
                            next_queue.append(steps_map[next_id])
                    else:
                        # Standard task, follow all next steps (could be one or more for parallel spawn)
                        for branch in s.next_steps:
                            if branch.next_step_id and steps_map[branch.next_step_id] not in next_queue:
                                next_queue.append(steps_map[branch.next_step_id])
                else:
                    # Step failed, stop workflow
                    supabase.table("workflow_runs").update({"status": "failed"}).eq("id", run_id).execute()
                    logger.error(f"Workflow {workflow_id} run {run_id} failed due to step {s.id} failure.")
                    return

            current_steps = next_queue

        # Workflow Completed
        supabase.table("workflow_runs").update({
            "status": "completed"
        }).eq("id", run_id).execute()
        logger.info(f"Run {run_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Workflow execution failed for run {run_id}: {e}")
        try:
            supabase.table("workflow_runs").update({"status": "failed"}).eq("id", run_id).execute()
        except Exception as db_e:
            logger.error(f"Failed to update run status to failed after workflow error: {db_e}")



async def execute_step_task(run_id: str, step_id: str):
    """
    Background task to execute a single workflow step.
    """
    logger.info(f"Re-running step {step_id} for run {run_id}")
    
    try:
        # 1. Fetch Run and Workflow
        run_res = supabase.table("workflow_runs").select("*").eq("id", run_id).execute()
        if not run_res.data:
            return
        run_data = run_res.data[0]
        workflow_id = run_data["workflow_id"]
        results = run_data["steps_results"]
        
        workflow = get_workflow(workflow_id)
        steps_map = {s.id: s for s in workflow.steps}
        if step_id not in steps_map:
            return
            
        step = steps_map[step_id]
        
        # 2. Get context from previous step (optimistic fallback or input_step_id)
        context = ""
        if step.input_step_id:
             for res in results:
                 if res.get("step_id") == step.input_step_id:
                     context = res.get("output", "")
                     break
        
        # 3. Call execute_task
        await execute_task(run_id, step, context, results)
        
        # 4. Determine overall run status
        # (This is simplified; a full graph status check would be more complex)
        all_completed = all(r.get("status") == "completed" for r in results)
        any_failed = any(r.get("status") == "failed" for r in results)
        
        new_status = run_data["status"]
        if all_completed:
            new_status = "completed"
        elif any_failed:
            new_status = "failed"
        
        supabase.table("workflow_runs").update({
            "status": new_status
        }).eq("id", run_id).execute()
        
    except Exception as e:
        logger.error(f"Error in execute_step_task: {e}")
        
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

@app.post("/run/{run_id}/step/{step_id}")
async def run_single_step(run_id: str, step_id: str, background_tasks: BackgroundTasks):
    """Trigger a single step execution."""
    try:
        background_tasks.add_task(execute_step_task, run_id, step_id)
        return {"status": "queued", "step_id": step_id}
    except Exception as e:
        logger.error(f"Error starting single step run: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start step run: {str(e)}")
