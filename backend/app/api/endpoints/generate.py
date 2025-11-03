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

# --- AGENT ROLE DEFINITIONS (ENHANCED FOR ROOT CAUSE ANALYSIS) ---
PM_PROMPT = """You are a Project Manager AI. Your task is to take a user's website checklist and create a structured JSON project plan. The plan must be a JSON object with a 'tasks' array. Task types are 'component' or 'page'. You MUST use the Next.js App Router structure: pages are files like 'app/page.tsx' or 'app/contact/page.tsx'. Component tasks MUST come before page tasks."""

UI_DESIGNER_PROMPT = """You are a UI/UX Designer AI. Your task is to take a component description and create a JSON spec for its structure and props. For any text content like titles or labels, use descriptive placeholders in brackets, e.g., "[HERO_TITLE]". Your output must be a single JSON object."""

COPYWRITER_PROMPT = """You are an expert Copywriter AI. You will be given a component's design spec with placeholder text. Your task is to replace the placeholders with compelling, user-friendly copy. Your output must be a single JSON object containing only the finalized text content."""

FRONTEND_DEV_PROMPT = """You are an expert Frontend Developer specializing in Next.js, React, and TypeScript. Your task is to write code based on a JSON specification or a debug request. You must follow strict file path conventions: components go in `src/components/`, pages in `app/`. Your output must be a single JSON object with 'filename' and 'content' keys."""

QA_TESTER_PROMPT = """You are a QA Tester AI specializing in Jest and React Testing Library. Your task is to write a test file for a React component. The test must validate both functionality and accessibility (using jest-axe). Your output must be a single JSON object with 'filename' (e.g., `src/components/Header.test.tsx`) and 'content' keys."""

DEBUGGER_FILE_ANALYSIS_PROMPT = """You are an expert at analyzing build error logs. Your task is to read an error log and identify which source code files are most likely causing the error.

IMPORTANT: Look for the actual source of the problem, not just where symptoms appear.

Your output MUST be a JSON object with a single key "relevant_files", which is an array of strings containing the file paths."""

DEBUGGER_PROMPT = """You are a Senior Debugger AI specializing in ROOT CAUSE ANALYSIS. Your critical mission is to identify and fix the UNDERLYING CAUSE of errors, not just patch symptoms.

ANALYSIS APPROACH:
1. Read the error message carefully - what is it really telling you?
2. Examine the code flow - where does the problem originate?
3. Consider dependencies - are imports, types, or APIs missing/incorrect?
4. Think systemically - is this a design issue, not just a code typo?

ROOT CAUSE vs PATCH:
- ❌ PATCH: Adding a null check when the real issue is incorrect data flow
- ✅ ROOT CAUSE: Fixing the data source that should never produce null
- ❌ PATCH: Wrapping code in try-catch without fixing the actual problem
- ✅ ROOT CAUSE: Fixing the condition that causes the exception
- ❌ PATCH: Adding type assertions to bypass TypeScript errors
- ✅ ROOT CAUSE: Correcting the type definitions or data structure

INSTRUCTIONS:
1. Identify the ROOT CAUSE of the error (not just symptoms)
2. Propose a fix that addresses the UNDERLYING ISSUE
3. Ensure your fix prevents this entire class of errors, not just this instance

If you are provided with "known_solutions" from previous similar incidents, USE THEM AS REFERENCE ONLY. Do not blindly apply them - analyze if they truly address the root cause for THIS specific error. The known solutions may have been patches, not proper fixes.

Your output MUST be a JSON object with:
- 'file_to_fix': The exact path of the file where the ROOT CAUSE exists
- 'root_cause_analysis': A detailed explanation of the underlying problem (2-3 sentences)
- 'fix_suggestion': A clear instruction for fixing the ROOT CAUSE (not a patch)"""

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

# --- START: ENHANCED ROOT CAUSE FIX CYCLE ---
async def run_fix_cycle(
    error_log: str, error_type: str, output_dir: str, agents: dict, attempt: int
) -> bool:
    """
    Runs enhanced self-healing with AI-driven root cause analysis.

    PHILOSOPHY:
    - ALWAYS use AI to analyze and propose fixes (never auto-apply patches)
    - Known solutions are provided as SUGGESTIONS, not automatic fixes
    - Focus on ROOT CAUSE fixes, not symptomatic patches
    - AI validates and adapts known solutions to the current context

    Returns True if a fix was applied, False otherwise.
    """
    error_signature = knowledge_base.create_error_signature(error_log)

    # Gather context for AI analysis
    print("🤖 Delegating to AI Debugger for ROOT CAUSE analysis...")
    all_code_files = await file_handler.read_all_code_files(output_dir)

    # Step 1: Identify relevant files
    analysis_response = agents["analyst"].execute_task({"error_log": error_log})
    analysis = parse_json_from_ai(analysis_response)
    relevant_files = analysis.get("relevant_files", []) if analysis else []

    targeted_codebase = {name: all_code_files[name] for name in relevant_files if name in all_code_files}

    # Step 2: Retrieve known solutions as SUGGESTIONS (not auto-apply)
    known_solution_str = knowledge_base.find_known_solution(error_signature)
    past_examples = knowledge_base.find_similar_incidents(error_signature)

    # Prepare context for AI with known solutions as reference
    ai_context = {
        "error_log": error_log,
        "error_type": error_type,
        "codebase": targeted_codebase,
        "similar_past_incidents": past_examples if past_examples else []
    }

    # Add known solution as a SUGGESTION (not mandatory)
    if known_solution_str:
        print(f"📚 Found a known solution. Providing to AI as REFERENCE (not auto-applying)...")
        try:
            known_solution = json.loads(known_solution_str)
            ai_context["known_solution_suggestion"] = {
                "note": "This solution worked for a similar error before. Analyze if it addresses the ROOT CAUSE for this specific case. Do NOT blindly apply it - it may have been a patch, not a proper fix.",
                "previous_solution": known_solution
            }
        except json.JSONDecodeError:
            print("⚠️ Could not parse known solution. Proceeding with AI analysis...")

    if past_examples:
        print(f"📚 Found {len(past_examples)} similar past incidents. Providing as reference to AI...")

    # Step 3: AI performs root cause analysis
    diagnosis_response = agents["debugger"].execute_task(ai_context)
    diagnosis = parse_json_from_ai(diagnosis_response)

    if not diagnosis or "file_to_fix" not in diagnosis:
        print("⚠️ AI could not identify root cause. Diagnosis failed.")
        return False

    file_to_fix = diagnosis['file_to_fix']
    root_cause = diagnosis.get('root_cause_analysis', 'Not provided')
    fix_suggestion = diagnosis.get('fix_suggestion', diagnosis.get('fix_suggestion'))

    print(f"🎯 ROOT CAUSE IDENTIFIED: {root_cause}")
    print(f"🔧 Proposed fix: {fix_suggestion}")

    # Step 4: AI generates the fix based on root cause analysis
    if file_to_fix not in all_code_files:
        print(f"⚠️ File {file_to_fix} not found in codebase.")
        return False

    fix_prompt = {
        "task": "fix_root_cause",
        "file_to_fix": file_to_fix,
        "code_to_fix": all_code_files[file_to_fix],
        "root_cause_analysis": root_cause,
        "fix_instructions": fix_suggestion,
        "context": f"This is attempt {attempt} to fix a {error_type} error. Focus on addressing the ROOT CAUSE, not just suppressing symptoms."
    }

    fix_response = agents["dev"].execute_task(fix_prompt)
    fix_code = parse_json_from_ai(fix_response)

    if not fix_code or not fix_code.get("filename") or not fix_code.get("content"):
        print("⚠️ AI could not generate a valid fix.")
        return False

    # Step 5: Apply the AI-generated fix
    await file_handler.write_file(output_dir, fix_code.get("filename"), fix_code.get("content"))

    # Step 6: Save to knowledge base for future reference
    knowledge_base.save_incident(
        error_signature,
        error_log,
        {**fix_prompt, "root_cause": root_cause},  # Include root cause in saved data
        fix_code,
        "AI_RootCauseAnalysis",
        attempt
    )

    print("✅ ROOT CAUSE fix applied successfully.")
    return True
# --- END: ENHANCED ROOT CAUSE FIX CYCLE ---

async def build_and_test_component(task: dict, output_dir: str, agents: dict):
    """
    Builds and tests components with AI-driven root cause analysis for failures.

    Uses iterative approach with intelligent error fixing:
    - AI analyzes root causes, not just symptoms
    - Known solutions used as suggestions, not auto-applied
    - Focuses on preventing entire classes of errors
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

        print(f"🔥 Test failed for {task_name}. Performing AI-driven ROOT CAUSE analysis...")

        # Use AI to perform root cause analysis (known solutions provided as reference only)
        fix_applied = await run_fix_cycle(test_log, "component_test", output_dir, agents, attempt)
        
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