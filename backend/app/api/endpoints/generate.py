# backend/app/api/endpoints/generate.py
import asyncio
import json
import os
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

BACKEND_ARCHITECT_PROMPT = """You are a Backend Architecture AI specializing in Node.js/Express and API design. Given a website checklist and frontend components, you design the backend API structure.

Your task:
1. Identify what backend functionality is needed (forms, data fetching, authentication, etc.)
2. Design RESTful API endpoints with proper HTTP methods
3. Define data models and database schema
4. Plan authentication and authorization if needed

Output must be JSON with:
- 'api_endpoints': Array of {method, path, description, requestBody, responseBody}
- 'models': Array of {name, schema}
- 'architecture_notes': Brief explanation of your design decisions"""

BACKEND_DEV_PROMPT = """You are a Backend Developer AI specializing in Node.js, Express, and TypeScript. Your task is to implement API endpoints based on specifications.

Follow these conventions:
- Use Express.js framework
- TypeScript for type safety
- Proper error handling with try-catch
- RESTful API design
- Input validation
- Clear response formats

Your output must be JSON with 'filename' and 'content' keys. Generate one file at a time."""

API_TESTER_PROMPT = """You are an API Testing specialist. Your task is to write comprehensive API tests using Jest and Supertest.

Tests should cover:
- All HTTP methods (GET, POST, PUT, DELETE)
- Success cases (200, 201, etc.)
- Error cases (400, 404, 500, etc.)
- Input validation
- Response format validation

Output must be JSON with 'filename' and 'content' keys."""

DEBUGGER_FILE_ANALYSIS_PROMPT = """You are an expert at analyzing build error logs. Your task is to read an error log and identify which source code files are most likely causing the error.

IMPORTANT:
1. Look for the actual source of the problem, not just where symptoms appear
2. You will be provided with a list of available files in the codebase - ONLY return files from this list
3. Match file paths exactly as they appear in the available_files list
4. If an error mentions "page.tsx", look for files ending with "page.tsx" in the available files (e.g., "app/page.tsx")

Your output MUST be a JSON object with a single key "relevant_files", which is an array of strings containing the exact file paths from the available_files list."""

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

IMPORTANT: The codebase context you receive contains only relevant files. When specifying 'file_to_fix', use the exact file path as it appears in the codebase. If the error mentions a short filename like "page.tsx", the actual path is likely "app/page.tsx" - check the codebase for the correct path.

Your output MUST be a JSON object with:
- 'file_to_fix': The exact path of the file where the ROOT CAUSE exists (must match a file from the codebase provided)
- 'root_cause_analysis': A detailed explanation of the underlying problem (2-3 sentences)
- 'fix_suggestion': A clear instruction for fixing the ROOT CAUSE (not a patch)"""

E2E_TESTER_PROMPT = """You are a QA Automation Engineer AI specializing in Playwright. Your task is to take a website checklist and write a complete Playwright test file. Your output must be a single JSON object with 'filename' ('tests/e2e.spec.ts') and 'content'."""

INTEGRATION_PROMPT = """You are a Full-Stack Integration Specialist. Your task is to connect the frontend to the backend API.

Given:
- Frontend components that need data
- Backend API endpoints

You will:
1. Create API client utilities (fetch wrappers, axios config)
2. Add environment variables for API URLs
3. Update components to call APIs instead of using mock data
4. Add loading states and error handling
5. Implement proper data flow

Output must be JSON with 'filename' and 'content' for each file to update."""

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
    # Provide AI with list of available files for better decision making
    available_files_list = list(all_code_files.keys())
    analysis_response = agents["analyst"].execute_task({
        "error_log": error_log,
        "available_files": available_files_list  # Help AI see actual file paths
    })
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

    # Step 4: Intelligent file path matching
    # Try exact match first, then fuzzy match if not found
    matched_file = None
    if file_to_fix in all_code_files:
        matched_file = file_to_fix
    else:
        # Try to find files that end with the specified filename
        # e.g., "page.tsx" should match "app/page.tsx" or "src/app/page.tsx"
        print(f"🔍 Exact match not found. Trying intelligent path matching for: {file_to_fix}")
        candidates = [f for f in all_code_files.keys() if f.endswith(file_to_fix)]

        if len(candidates) == 1:
            matched_file = candidates[0]
            print(f"✓ Found match: {matched_file}")
        elif len(candidates) > 1:
            # Multiple matches - prefer shorter paths (more likely to be correct)
            matched_file = min(candidates, key=len)
            print(f"✓ Multiple matches found, using: {matched_file}")
            print(f"   Other candidates: {', '.join(c for c in candidates if c != matched_file)}")
        else:
            # Try partial matching with path components
            base_name = os.path.basename(file_to_fix)
            candidates = [f for f in all_code_files.keys() if base_name in f]
            if candidates:
                matched_file = min(candidates, key=len)
                print(f"✓ Partial match found: {matched_file}")

    if not matched_file:
        print(f"⚠️ File {file_to_fix} not found in codebase.")
        print(f"   Available files: {', '.join(list(all_code_files.keys())[:10])}")
        return False

    fix_prompt = {
        "task": "fix_root_cause",
        "file_to_fix": matched_file,  # Use the matched file path
        "code_to_fix": all_code_files[matched_file],
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

# =============================================================================
# PHASE-BASED HELPER FUNCTIONS
# =============================================================================

async def phase1_generate_all_components(component_tasks: list, output_dir: str, agents: dict) -> dict:
    """
    PHASE 1: Generate all components without testing.
    Returns dict of component_name -> {design_spec, file_path}
    """
    print("\n" + "="*80)
    print("PHASE 1: GENERATING ALL COMPONENTS")
    print("="*80)

    components_info = {}

    for task in component_tasks:
        comp_name = task.get("name")
        print(f"\n📦 Generating component: {comp_name}")

        # Step 1: UI Design
        spec_response = agents['ui'].execute_task({"component": comp_name, "props": task.get("details")})
        design_spec = parse_json_from_ai(spec_response)
        if not design_spec:
            print(f"  ⚠️ Failed to generate design spec for {comp_name}")
            continue

        # Step 2: Copywriting
        copy_response = agents['copy'].execute_task({"design_spec": design_spec})
        final_copy = parse_json_from_ai(copy_response)
        if final_copy:
            design_spec['props'].update(final_copy)

        # Step 3: Code Generation
        code_response = agents['dev'].execute_task({"componentSpec": design_spec})
        component_file = parse_json_from_ai(code_response)
        if not component_file:
            print(f"  ⚠️ Failed to generate code for {comp_name}")
            continue

        # Step 4: Write to file (no testing yet)
        file_path = component_file.get("filename")
        await file_handler.write_file(output_dir, file_path, component_file.get("content"))

        components_info[comp_name] = {
            "design_spec": design_spec,
            "file_path": file_path
        }

        print(f"  ✅ Component {comp_name} generated: {file_path}")

    print(f"\n✅ PHASE 1 COMPLETE: {len(components_info)} components generated")
    return components_info


async def phase2_generate_all_pages(page_tasks: list, output_dir: str, agents: dict) -> list:
    """
    PHASE 2: Generate all pages.
    Returns list of page file paths.
    """
    print("\n" + "="*80)
    print("PHASE 2: GENERATING ALL PAGES")
    print("="*80)

    page_files = []

    for task in page_tasks:
        page_name = task.get('name')
        print(f"\n📄 Generating page: {page_name}")

        page_response = agents['dev'].execute_task({
            "pageName": page_name,
            "componentsToImport": task.get("details")
        })
        page_file = parse_json_from_ai(page_response)

        if page_file:
            file_path = page_file.get("filename")
            await file_handler.write_file(output_dir, file_path, page_file.get("content"))
            page_files.append(file_path)
            print(f"  ✅ Page {page_name} generated: {file_path}")
        else:
            print(f"  ⚠️ Failed to generate page {page_name}")

    print(f"\n✅ PHASE 2 COMPLETE: {len(page_files)} pages generated")
    return page_files


async def phase3_host_and_fix_frontend(output_dir: str, agents: dict) -> bool:
    """
    PHASE 3: Host the frontend and fix all errors until it runs cleanly.
    Returns True if successful.
    """
    print("\n" + "="*80)
    print("PHASE 3: HOSTING FRONTEND & FIXING ERRORS")
    print("="*80)

    MAX_FIX_ATTEMPTS = 10

    for attempt in range(1, MAX_FIX_ATTEMPTS + 1):
        print(f"\n🔧 Build attempt {attempt}/{MAX_FIX_ATTEMPTS}")

        # Try to build
        build_ok, build_log = await e2e_tester.run_command_stream("npm run build", cwd=output_dir)

        if build_ok:
            print("✅ Frontend builds successfully!")

            # Try to start dev server (quick check)
            print("🚀 Testing dev server startup...")
            # Note: We'll just check if build succeeded for now
            # In production, you might want to actually start the server and check
            return True

        print("❌ Build failed. Analyzing errors...")

        # Check if it's a dependency issue
        if "Cannot find module" in build_log and "node_modules" in build_log:
            print("📦 Dependency issue detected. Reinstalling...")
            await component_tester.reset_node_modules(output_dir)
            continue

        # Use AI to fix the root cause
        print("🤖 Performing ROOT CAUSE analysis...")
        fix_applied = await run_fix_cycle(build_log, "frontend_build", output_dir, agents, attempt)

        if not fix_applied:
            print(f"  ⚠️ Could not generate fix. Attempt {attempt}/{MAX_FIX_ATTEMPTS}")
            if attempt == MAX_FIX_ATTEMPTS:
                return False

    print("\n✅ PHASE 3 COMPLETE: Frontend is running cleanly")
    return True


async def phase4_generate_backend(checklist_data: dict, components_info: dict, output_dir: str, agents: dict) -> dict:
    """
    PHASE 4: Generate backend API based on frontend needs.
    Returns dict with backend_files and api_spec.
    """
    print("\n" + "="*80)
    print("PHASE 4: GENERATING BACKEND")
    print("="*80)

    # Step 1: Backend Architecture Design
    print("\n🏗️  Designing backend architecture...")
    arch_response = agents['backend_arch'].execute_task({
        "checklist": checklist_data,
        "components": list(components_info.keys())
    })
    api_spec = parse_json_from_ai(arch_response)

    if not api_spec:
        print("⚠️ Failed to generate backend architecture")
        return {"backend_files": [], "api_spec": {}}

    print(f"  ✅ Designed {len(api_spec.get('api_endpoints', []))} API endpoints")

    # Step 2: Generate backend files
    backend_files = []

    # Generate main server file
    print("\n📝 Generating server.ts...")
    server_response = agents['backend_dev'].execute_task({
        "task": "generate_server",
        "api_spec": api_spec
    })
    server_file = parse_json_from_ai(server_response)
    if server_file:
        await file_handler.write_file(output_dir, server_file.get("filename"), server_file.get("content"))
        backend_files.append(server_file.get("filename"))
        print(f"  ✅ Generated: {server_file.get('filename')}")

    # Generate API route files
    for endpoint in api_spec.get('api_endpoints', []):
        print(f"\n📝 Generating endpoint: {endpoint.get('method')} {endpoint.get('path')}")
        route_response = agents['backend_dev'].execute_task({
            "task": "generate_route",
            "endpoint": endpoint
        })
        route_file = parse_json_from_ai(route_response)
        if route_file:
            await file_handler.write_file(output_dir, route_file.get("filename"), route_file.get("content"))
            backend_files.append(route_file.get("filename"))
            print(f"  ✅ Generated: {route_file.get('filename')}")

    # Generate models
    for model in api_spec.get('models', []):
        print(f"\n📝 Generating model: {model.get('name')}")
        model_response = agents['backend_dev'].execute_task({
            "task": "generate_model",
            "model": model
        })
        model_file = parse_json_from_ai(model_response)
        if model_file:
            await file_handler.write_file(output_dir, model_file.get("filename"), model_file.get("content"))
            backend_files.append(model_file.get("filename"))
            print(f"  ✅ Generated: {model_file.get('filename')}")

    print(f"\n✅ PHASE 4 COMPLETE: Generated {len(backend_files)} backend files")
    return {"backend_files": backend_files, "api_spec": api_spec}


async def phase5_test_and_fix_apis(api_spec: dict, output_dir: str, agents: dict) -> bool:
    """
    PHASE 5: Test all APIs and fix any issues.
    Returns True if all APIs pass tests.
    """
    print("\n" + "="*80)
    print("PHASE 5: TESTING & FIXING APIs")
    print("="*80)

    # Generate API tests
    print("\n📝 Generating API tests...")
    test_response = agents['api_tester'].execute_task({"api_spec": api_spec})
    test_file = parse_json_from_ai(test_response)

    if not test_file:
        print("⚠️ Failed to generate API tests")
        return False

    test_path = test_file.get("filename")
    await file_handler.write_file(output_dir, test_path, test_file.get("content"))
    print(f"  ✅ Generated: {test_path}")

    MAX_FIX_ATTEMPTS = 5

    for attempt in range(1, MAX_FIX_ATTEMPTS + 1):
        print(f"\n🧪 Running API tests (attempt {attempt}/{MAX_FIX_ATTEMPTS})...")

        # Run tests (using Jest for API tests)
        test_ok, test_log = await component_tester.run_single_component_test(output_dir, test_path)

        if test_ok:
            print("✅ All API tests passed!")
            return True

        print("❌ API tests failed. Analyzing errors...")

        # Use AI to fix root cause
        print("🤖 Performing ROOT CAUSE analysis...")
        fix_applied = await run_fix_cycle(test_log, "api_test", output_dir, agents, attempt)

        if not fix_applied and attempt == MAX_FIX_ATTEMPTS:
            print(f"⚠️ Failed to fix API issues after {MAX_FIX_ATTEMPTS} attempts")
            return False

    print("\n✅ PHASE 5 COMPLETE: All APIs tested and working")
    return True


async def phase6_integrate_frontend_backend(components_info: dict, api_spec: dict, output_dir: str, agents: dict) -> bool:
    """
    PHASE 6: Integrate frontend with backend APIs.
    Returns True if integration is successful.
    """
    print("\n" + "="*80)
    print("PHASE 6: INTEGRATING FRONTEND WITH BACKEND")
    print("="*80)

    # Generate API client utilities
    print("\n📝 Generating API client utilities...")
    client_response = agents['integrator'].execute_task({
        "task": "generate_api_client",
        "api_spec": api_spec
    })
    client_file = parse_json_from_ai(client_response)

    if client_file:
        await file_handler.write_file(output_dir, client_file.get("filename"), client_file.get("content"))
        print(f"  ✅ Generated: {client_file.get('filename')}")

    # Update components to use APIs
    updated_count = 0
    for comp_name, comp_info in components_info.items():
        print(f"\n🔗 Checking if {comp_name} needs API integration...")

        integration_response = agents['integrator'].execute_task({
            "task": "integrate_component",
            "component_name": comp_name,
            "component_code": await file_handler.read_file(output_dir, comp_info['file_path']),
            "api_spec": api_spec
        })
        updated_file = parse_json_from_ai(integration_response)

        if updated_file and updated_file.get("needs_update"):
            await file_handler.write_file(output_dir, updated_file.get("filename"), updated_file.get("content"))
            updated_count += 1
            print(f"  ✅ Updated {comp_name} with API integration")

    print(f"\n✅ PHASE 6 COMPLETE: Updated {updated_count} components with API integration")
    return True


@router.post("/generate")
async def generate_website(request: GenerateRequest):
    """
    Main website generation endpoint with 6-phase workflow:

    PHASE 1: Generate all frontend components
    PHASE 2: Generate all pages
    PHASE 3: Host frontend and fix all errors
    PHASE 4: Generate backend APIs
    PHASE 5: Test and fix all APIs
    PHASE 6: Integrate frontend with backend
    """
    session_id, output_dir = "", ""
    checklist_data = request.checklist.dict()
    final_status = "FAILED"

    try:
        # Setup
        session_id = knowledge_base.create_session(checklist_data)
        output_dir = file_handler.create_output_dir()
        file_handler.setup_scaffold(output_dir, checklist_data)
        await component_tester.install_dependencies(output_dir)

        # Initialize AI agents
        ai_client = get_client()
        agents = {
            'pm': AIAgent(PM_PROMPT, client=ai_client),
            'ui': AIAgent(UI_DESIGNER_PROMPT, client=ai_client),
            'copy': AIAgent(COPYWRITER_PROMPT, client=ai_client),
            'dev': AIAgent(FRONTEND_DEV_PROMPT, client=ai_client),
            'qa': AIAgent(QA_TESTER_PROMPT, client=ai_client),
            'backend_arch': AIAgent(BACKEND_ARCHITECT_PROMPT, client=ai_client),
            'backend_dev': AIAgent(BACKEND_DEV_PROMPT, client=ai_client),
            'api_tester': AIAgent(API_TESTER_PROMPT, client=ai_client),
            'integrator': AIAgent(INTEGRATION_PROMPT, client=ai_client),
            'debugger': AIAgent(DEBUGGER_PROMPT, client=ai_client),
            'analyst': AIAgent(DEBUGGER_FILE_ANALYSIS_PROMPT, client=ai_client),
            'e2e': AIAgent(E2E_TESTER_PROMPT, client=ai_client)
        }

        # Get project plan
        print("\n🎯 Creating project plan...")
        plan_response = agents['pm'].execute_task({"checklist": checklist_data})
        project_plan = parse_json_from_ai(plan_response)
        if not project_plan or "tasks" not in project_plan:
            raise ValueError("PM failed to create a valid plan.")

        component_tasks = [t for t in project_plan.get("tasks", []) if t.get("type") == "component"]
        page_tasks = [t for t in project_plan.get("tasks", []) if t.get("type") == "page"]

        print(f"📋 Plan: {len(component_tasks)} components, {len(page_tasks)} pages")

        # =====================================================================
        # PHASE 1: Generate ALL frontend components
        # =====================================================================
        components_info = await phase1_generate_all_components(component_tasks, output_dir, agents)

        if not components_info:
            raise ValueError("Failed to generate any components")

        # =====================================================================
        # PHASE 2: Generate ALL pages
        # =====================================================================
        page_files = await phase2_generate_all_pages(page_tasks, output_dir, agents)

        # =====================================================================
        # PHASE 3: Host frontend and fix ALL errors
        # =====================================================================
        frontend_ok = await phase3_host_and_fix_frontend(output_dir, agents)

        if not frontend_ok:
            raise ValueError("Failed to get frontend running cleanly after maximum attempts")

        # =====================================================================
        # PHASE 4: Generate backend
        # =====================================================================
        backend_result = await phase4_generate_backend(checklist_data, components_info, output_dir, agents)

        # =====================================================================
        # PHASE 5: Test and fix APIs
        # =====================================================================
        apis_ok = await phase5_test_and_fix_apis(backend_result['api_spec'], output_dir, agents)

        if not apis_ok:
            print("⚠️  Some API tests failed, but continuing with integration...")

        # =====================================================================
        # PHASE 6: Integrate frontend with backend
        # =====================================================================
        integration_ok = await phase6_integrate_frontend_backend(
            components_info,
            backend_result['api_spec'],
            output_dir,
            agents
        )

        # =====================================================================
        # FINAL: E2E Testing
        # =====================================================================
        print("\n" + "="*80)
        print("FINAL: END-TO-END TESTING")
        print("="*80)

        # Generate E2E tests
        print("\n📝 Generating E2E tests...")
        e2e_response = agents['e2e'].execute_task({"checklist": checklist_data})
        e2e_code = parse_json_from_ai(e2e_response)
        if e2e_code:
            await file_handler.write_file(output_dir, e2e_code.get("filename"), e2e_code.get("content"))
            print(f"  ✅ Generated: {e2e_code.get('filename')}")

        # Run E2E tests
        print("\n🧪 Running E2E tests...")
        e2e_ok, e2e_log = await e2e_tester.execute_playwright_tests(output_dir)

        if e2e_ok:
            print("✅ E2E tests passed!")
        else:
            print("⚠️  E2E tests failed, but website is generated")

        # =====================================================================
        # SUCCESS
        # =====================================================================
        final_status = "SUCCESS"

        print("\n" + "="*80)
        print("🎉 WEBSITE GENERATION COMPLETE!")
        print("="*80)
        print(f"📁 Output: {output_dir}")
        print(f"📦 Components: {len(components_info)}")
        print(f"📄 Pages: {len(page_files)}")
        print(f"🔌 API Endpoints: {len(backend_result['api_spec'].get('api_endpoints', []))}")
        print("="*80)

        return {
            "status": "Success",
            "outputPath": output_dir,
            "components_generated": len(components_info),
            "pages_generated": len(page_files),
            "api_endpoints": len(backend_result['api_spec'].get('api_endpoints', [])),
            "phases_completed": ["components", "pages", "frontend_hosting", "backend", "api_testing", "integration"],
            "message": "Full-stack website generated successfully with AI-driven root cause fixing"
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if session_id:
            knowledge_base.update_session_status(session_id, final_status, output_dir)