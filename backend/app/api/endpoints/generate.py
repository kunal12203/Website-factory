# backend/app/api/endpoints/generate.py
import asyncio
import json
import traceback
from fastapi import APIRouter, HTTPException
from app.models import GenerateRequest
from app.agents.base_agent import AIAgent
from app.agents.ai_clients import get_client
from app.services import (
    file_handler,
    component_tester,
    e2e_tester,
    knowledge_base,
)

# --- AGENT ROLE DEFINITIONS (FINAL & OPTIMIZED) ---
PM_PROMPT = """You are a Project Manager AI. Your task is to take a user's website checklist and create a structured JSON project plan. The plan must be a JSON object with a 'tasks' array. Task types are 'component' or 'page'. You MUST use the Next.js App Router structure: pages are files like 'app/page.tsx' or 'app/contact/page.tsx'. Component tasks MUST come before page tasks."""
UI_DESIGNER_PROMPT = """You are a UI/UX Designer AI. Your task is to take a component description and create a JSON spec for its structure and props. For any text content like titles or labels, use descriptive placeholders in brackets, e.g., "[HERO_TITLE]". Your output must be a single JSON object."""
COPYWRITER_PROMPT = """You are an expert Copywriter AI. You will be given a component's design spec with placeholder text. Your task is to replace the placeholders with compelling, user-friendly copy. Your output must be a single JSON object containing only the finalized text content."""
FRONTEND_DEV_PROMPT = """You are an expert Frontend Developer specializing in Next.js, React, and TypeScript. Your task is to write code based on a JSON specification or a debug request. You must follow strict file path conventions: components go in `src/components/`, pages in `app/`. Your output must be a single JSON object with 'filename' and 'content' keys."""
QA_TESTER_PROMPT = """You are a QA Tester AI specializing in Jest and React Testing Library. Your task is to write a test file for a React component. The test must validate both functionality and accessibility (using jest-axe). Your output must be a single JSON object with 'filename' (e.g., `src/components/Header.test.tsx`) and 'content' keys."""
DEBUGGER_FILE_ANALYSIS_PROMPT = """You are an expert at analyzing build error logs. Your task is to read an error log and identify which source code files are most likely causing the error. Your output MUST be a JSON object with a single key "relevant_files", which is an array of strings containing the file paths."""
DEBUGGER_PROMPT = """You are a Senior Debugger AI. Your task is to analyze an error log and relevant source code to find the root cause. Your output MUST be a JSON object with 'file_to_fix' (the exact path of the file causing the error) and 'fix_suggestion' (a clear, one-sentence instruction for the developer)."""
E2E_TESTER_PROMPT = """You are a QA Automation Engineer AI specializing in Playwright. Your task is to take a website checklist and write a complete Playwright test file. Your output must be a single JSON object with 'filename' ('tests/e2e.spec.ts') and 'content'."""

router = APIRouter()


def parse_json_from_ai(ai_response: str) -> dict | None:
    try:
        if "```json" in ai_response:
             ai_response = ai_response.split("```json")[1].split("```")[0]
        return json.loads(ai_response)
    except (json.JSONDecodeError, IndexError):
        print(f"❌ Invalid JSON from AI: {ai_response[:200]}")
        return None

# --- START: MISSING HELPER FUNCTION ---
# This function was missing from the previous file, causing the TypeError.
async def run_fix_cycle(
    error_log: str, error_type: str, output_dir: str, agents: dict, attempt: int
) -> bool:
    """
    Runs the full self-healing process: Knowledge Base -> Two-Stage AI Debugging -> Save Solution.
    Returns True if a fix was applied, False otherwise.
    """
    error_signature = knowledge_base.create_error_signature(error_log)
    known_solution_str = knowledge_base.find_known_solution(error_signature)
    fix_code = None

    if known_solution_str:
        print("🧠 Found a known solution in the Knowledge Base. Applying patch...")
        fix_code = json.loads(known_solution_str)
    else:
        print("🤖 No known solution found. Delegating to AI Debugger for analysis...")
        all_code_files = await file_handler.read_all_code_files(output_dir)
        analysis_response = agents["analyst"].execute_task({"error_log": error_log})
        analysis = parse_json_from_ai(analysis_response)
        relevant_files = analysis.get("relevant_files", []) if analysis else []
        
        targeted_codebase = {name: all_code_files[name] for name in relevant_files if name in all_code_files}
        
        past_examples = knowledge_base.find_similar_incidents(error_signature)
        if past_examples: print(f"🧠 Found {len(past_examples)} similar incidents to use as examples.")

        debugger_prompt = {"error_log": error_log, "codebase": targeted_codebase, "successful_examples": past_examples}
        diagnosis_response = agents["debugger"].execute_task(debugger_prompt)
        diagnosis = parse_json_from_ai(diagnosis_response)
        
        if diagnosis and "file_to_fix" in diagnosis:
            file_to_fix = diagnosis['file_to_fix']
            if file_to_fix in all_code_files:
                fix_prompt = {"task": "fix_code", "file_to_fix": file_to_fix, "code_to_fix": all_code_files[file_to_fix], "instructions": diagnosis['fix_suggestion']}
                fix_response = agents["dev"].execute_task(fix_prompt)
                fix_code = parse_json_from_ai(fix_response)
                if fix_code:
                    knowledge_base.save_incident(error_signature, error_log, fix_prompt, fix_code, "FrontendDevAgent", attempt)

    if fix_code and fix_code.get("filename") and fix_code.get("content"):
        await file_handler.write_file(output_dir, fix_code.get("filename"), fix_code.get("content"))
        return True
    
    print("⚠️ AI Debugging cycle could not produce a valid fix.")
    return False
# --- END: MISSING HELPER FUNCTION ---

async def build_and_test_component(task: dict, output_dir: str, agents: dict):
    """
    Helper for the incremental, per-component build and test loop with learning.
    """
    MAX_TRIALS_PER_COMPONENT = 3
    task_name = task.get("name")
    print(f"\n--- Building & Validating Component: {task_name} ---")

    for attempt in range(1, MAX_TRIALS_PER_COMPONENT + 1):
        print(f"--- Attempt {attempt}/{MAX_TRIALS_PER_COMPONENT} for {task_name} ---")
        
        spec_response = agents['ui'].execute_task({"component": task_name, "props": task.get("details")})
        design_spec = parse_json_from_ai(spec_response)
        if not design_spec: continue

        copy_response = agents['copy'].execute_task({"design_spec": design_spec})
        final_copy = parse_json_from_ai(copy_response)
        if final_copy: design_spec['props'].update(final_copy)

        code_response = agents['dev'].execute_task({"componentSpec": design_spec})
        component_file = parse_json_from_ai(code_response)
        if not component_file: continue
        await file_handler.write_file(output_dir, component_file.get("filename"), component_file.get("content"))

        test_response = agents['qa'].execute_task({"componentSpec": design_spec, "componentCode": component_file.get("content")})
        test_file = parse_json_from_ai(test_response)
        if not test_file or not test_file.get("filename"): continue
        test_filepath = test_file.get("filename")
        await file_handler.write_file(output_dir, test_filepath, test_file.get("content"))
        
        test_ok, test_log = await component_tester.run_single_component_test(output_dir, test_filepath)
        if test_ok:
            print(f"✅ Component {task_name} passed its test.")
            return

        print(f"🔥 Test failed for {task_name}. Consulting Knowledge Base and attempting AI fix...")

         # --- START: CORRECTED FUNCTION CALL ---
        # Pass the entire 'agents' dictionary as a single argument.
        fix_applied = await run_fix_cycle(test_log, "component_test", output_dir, agents, attempt)
        # --- END: CORRECTED FUNCTION CALL ---
        
        if fix_applied:
            print(f"  Verifying the fix for {task_name}...")
            fix_test_ok, _ = await component_tester.run_single_component_test(output_dir, test_filepath)
            if fix_test_ok:
                print(f"  ✅ Fix successful for {task_name}!")
                return
        print(f"  ⚠️ Fix did not work for {task_name}. Retrying generation.")


        # if await run_fix_cycle(test_log, "component_test", output_dir, agents['analyst'], agents['debugger'], agents['dev'], attempt):
        #     print(f"  Verifying the fix for {task_name}...")
        #     fix_test_ok, _ = await component_tester.run_single_component_test(output_dir, test_filepath)
        #     if fix_test_ok:
        #         print(f"  ✅ Fix successful for {task_name}!")
        #         return
        # print(f"  ⚠️ Fix did not work for {task_name}. Retrying generation.")

    raise ValueError(f"Failed to build and test component '{task_name}' after max attempts.")


@router.post("/generate")
async def generate_website(request: GenerateRequest):
    session_id, output_dir = "", ""
    checklist_data = request.checklist.dict()
    final_status = "FAILED"
    try:
        session_id = knowledge_base.create_session(checklist_data)
        output_dir = file_handler.create_output_dir()
        file_handler.setup_scaffold(output_dir, checklist_data)
        await component_tester.install_dependencies(output_dir)

        ai_client = get_client()
        agents = {
            'pm': AIAgent(PM_PROMPT, client=ai_client),
            'ui': AIAgent(UI_DESIGNER_PROMPT, client=ai_client),
            'copy': AIAgent(COPYWRITER_PROMPT, client=ai_client),
            'dev': AIAgent(FRONTEND_DEV_PROMPT, client=ai_client),
            'qa': AIAgent(QA_TESTER_PROMPT, client=ai_client),
            'debugger': AIAgent(DEBUGGER_PROMPT, client=ai_client),
            'analyst': AIAgent(DEBUGGER_FILE_ANALYSIS_PROMPT, client=ai_client),
            'e2e': AIAgent(E2E_TESTER_PROMPT, client=ai_client)
        }

        plan_response = agents['pm'].execute_task({"checklist": checklist_data})
        project_plan = parse_json_from_ai(plan_response)
        if not project_plan or "tasks" not in project_plan: raise ValueError("PM failed to create a valid plan.")

        for task in [t for t in project_plan.get("tasks", []) if t.get("type") == "component"]:
            await build_and_test_component(task, output_dir, agents)
        
        for task in [t for t in project_plan.get("tasks", []) if t.get("type") == "page"]:
            print(f"\n--- Building Page: {task.get('name')} ---")
            page_response = agents['dev'].execute_task({"pageName": task.get("name"), "componentsToImport": task.get("details")})
            page_file = parse_json_from_ai(page_response)
            if page_file: await file_handler.write_file(output_dir, page_file.get("filename"), page_file.get("content"))

        MAX_TRIALS_FINAL = 5
        for trial in range(1, MAX_TRIALS_FINAL + 1):
            print(f"\n--- Final Validation Attempt {trial}/{MAX_TRIALS_FINAL} ---")
            
            build_ok, build_log = await e2e_tester.run_command_stream("npm run build", cwd=output_dir)
            if not build_ok:
                print("🔥 Final build failed.")
                if "Cannot find module" in build_log and "node_modules" in build_log:
                    await component_tester.reset_node_modules(output_dir)
                else:
                    # --- CORRECTED FUNCTION CALL ---
                    await run_fix_cycle(build_log, "build_error", output_dir, agents, trial)
                continue
            print("✅ Final build successful!")
            
            e2e_response = agents['e2e'].execute_task({"checklist": checklist_data})
            e2e_code = parse_json_from_ai(e2e_response)
            if e2e_code: await file_handler.write_file(output_dir, e2e_code.get("filename"), e2e_code.get("content"))
            
            e2e_ok, e2e_log = await e2e_tester.execute_playwright_tests(output_dir)
            if not e2e_ok:
                print("🔥 E2E tests failed.")
                # --- CORRECTED FUNCTION CALL ---
                await run_fix_cycle(e2e_log, "e2e_error", output_dir, agents, trial)
                continue
            print("🚀 E2E tests passed!")

            lighthouse_ok, lighthouse_log = await e2e_tester.run_command_stream("npm run lighthouse", cwd=output_dir)
            if not lighthouse_ok:
                print(f"🔥 Lighthouse Quality Gates failed.")
                # --- CORRECTED FUNCTION CALL ---
                await run_fix_cycle(lighthouse_log, "lighthouse_error", output_dir, agents, trial)
                continue
            print("🏆 Performance and Accessibility checks passed!")
            
            final_status = "SUCCESS"
            return {"status": "Success", "outputPath": output_dir}
        
        raise ValueError("Failed to pass final validation stages after maximum attempts.")

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if session_id:
            knowledge_base.update_session_status(session_id, final_status, output_dir)