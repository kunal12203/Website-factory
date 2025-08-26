# backend/app/api/endpoints/generate.py
import asyncio
import traceback
import difflib  # Import the diff library
from fastapi import APIRouter, HTTPException
from app.models.checklist import GenerateRequest
from app.services import (
    code_generator,
    file_handler,
    component_tester,
    test_generator,
    e2e_tester
)

router = APIRouter()

def print_code_diff(old_code: str, new_code: str):
    """Prints a colored diff of the code changes."""
    print("\n--- AI CODE CHANGES ---")
    diff = difflib.unified_diff(
        old_code.splitlines(keepends=True),
        new_code.splitlines(keepends=True),
        fromfile='before_fix',
        tofile='after_fix',
    )
    for line in diff:
        if line.startswith('+'):
            print(f"\033[92m{line.strip()}\033[0m")  # Green for additions
        elif line.startswith('-'):
            print(f"\033[91m{line.strip()}\033[0m")  # Red for deletions
        elif line.startswith('^'):
            continue
        else:
            print(line.strip())
    print("-----------------------\n")


@router.post("/generate")
async def generate_website(request: GenerateRequest):
    """Orchestrates the full build, component test, and E2E test pipeline."""
    # ... (function setup remains the same)
    MAX_COMPONENT_TRIALS = 6
    MAX_E2E_TRIALS = 10
    report = { "success": False, "component_trials": 0, "e2e_trials": 0, "finalError": None, "outputPath": None, "history": [] }
    checklist_data = request.checklist.dict()
    output_dir = file_handler.create_output_dir()
    report["outputPath"] = output_dir

    try:
        print("\n--- Phase 1: Generating Initial Codebase ---")
        initial_prompt = code_generator.create_initial_code_prompt(checklist_data)
        generated_code = code_generator.generate_ai_response(initial_prompt)

        component_test_passed = False
        for trial in range(1, MAX_COMPONENT_TRIALS + 1):
            report["component_trials"] = trial
            print(f"\n--- Component Test Attempt {trial}/{MAX_COMPONENT_TRIALS} ---")
            
            await file_handler.create_config_files(output_dir, checklist_data)
            await file_handler.write_files_from_ai_response(output_dir, generated_code)
            
            success, failures = await component_tester.install_and_test_components(output_dir)
            
            if success:
                print("✅ All component tests passed!")
                component_test_passed = True
                report["history"].append({"stage": "component-test", "attempt": trial, "status": "Success"})
                break
            
            report["history"].append({"stage": "component-test", "attempt": trial, "status": "Failed", "errors": failures})
            print(f"🔥 {len(failures)} component test(s) failed. Asking AI for a fix...")

            if trial == MAX_COMPONENT_TRIALS: break
            
            code_before_fix = generated_code
            fix_prompt = code_generator.create_collective_fix_prompt(checklist_data, failures, generated_code)
            generated_code = code_generator.generate_ai_response(fix_prompt)
            print_code_diff(code_before_fix, generated_code) # Show the changes

        if not component_test_passed:
            raise ValueError("Failed to pass component tests after maximum attempts.")

        e2e_test_passed = False
        test_generator.create_playwright_test_from_checklist(output_dir, checklist_data)

        for trial in range(1, MAX_E2E_TRIALS + 1):
            report["e2e_trials"] = trial
            print(f"\n--- E2E Test Attempt {trial}/{MAX_E2E_TRIALS} ---")
            
            await file_handler.write_files_from_ai_response(output_dir, generated_code)
            
            success, output = await e2e_tester.run_e2e_tests(output_dir)

            if success:
                print("✅ All E2E tests passed! Website is fully functional.")
                e2e_test_passed = True
                report["history"].append({"stage": "e2e-test", "attempt": trial, "status": "Success"})
                break

            report["history"].append({"stage": "e2e-test", "attempt": trial, "status": "Failed", "log": output})
            print(f"🔥 E2E test failed. Asking AI for a fix...")
            
            if trial == MAX_E2E_TRIALS: break

            code_before_fix = generated_code
            fix_prompt = code_generator.create_e2e_fix_prompt(checklist_data, output, generated_code)
            generated_code = code_generator.generate_ai_response(fix_prompt)
            print_code_diff(code_before_fix, generated_code) # Show the changes
        
        if not e2e_test_passed:
            raise ValueError("Failed to pass E2E tests after maximum attempts.")

        report["success"] = True
        await file_handler.cleanup_test_files(output_dir)
        print("\n🚀 Build successful and fully tested. Output ready.")
        return {"status": "Success", "report": report}

    except Exception as e:
        traceback.print_exc()
        report["finalError"] = str(e)
        raise HTTPException(status_code=500, detail={"status": "Critical Failure", "report": report})