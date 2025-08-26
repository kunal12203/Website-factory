# backend/app/services/component_tester.py
import asyncio
import os
import re

async def run_command(command: str, cwd: str) -> tuple[bool, str]:
    print(f"Executing in '{cwd}': $ {command}")
    
    process = await asyncio.create_subprocess_shell(
        command, cwd=cwd,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    output = f"STDOUT:\n{stdout.decode()}\n\nSTDERR:\n{stderr.decode()}"
    return process.returncode == 0, output

def parse_jest_errors(jest_output: str) -> list[dict]:
    # ... (this function remains the same)
    failures = []
    fail_pattern = re.compile(r"FAIL\s+((?:src|components).+?\.test\.tsx)(.*?)(?=FAIL\s+src|Test Suites:)", re.DOTALL)
    matches = fail_pattern.finditer(jest_output)
    for match in matches:
        file_path, error_details = match.groups()
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0?]*[ -/]*[@-~])')
        cleaned_details = ansi_escape.sub('', error_details.strip())
        failures.append({"file": file_path.strip(), "error": cleaned_details})
    return failures

async def install_and_test_components(output_dir: str) -> tuple[bool, list[dict]]:
    print("--- Running Component Tests ---")
    print("Installing dependencies for Jest...")
    deps_command = 'npm install next react react-dom jest @testing-library/react @testing-library/jest-dom jest-environment-jsdom @types/jest'
    
    # --- THIS LINE IS MODIFIED ---
    # Added @tailwindcss/postcss to solve the build error.
    dev_deps_command = 'npm install --save-dev typescript ts-jest @types/node @types/react @types/react-dom postcss autoprefixer tailwindcss @tailwindcss/postcss eslint eslint-config-next'
    
    await run_command('npm init -y', cwd=output_dir)
    await run_command(deps_command, cwd=output_dir)
    await run_command(dev_deps_command, cwd=output_dir)

    print("Running Jest tests...")
    success, output = await run_command('npm test', cwd=output_dir)
    if not success:
        print("\n--- JEST TEST FAILURE DETAILS ---")
        print(output)
        print("-----------------------------------\n")
        
        failures = parse_jest_errors(output)
        return False, failures if failures else [{"file": "Unknown", "error": output}]
    return True, []