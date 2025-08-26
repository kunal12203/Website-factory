# backend/app/services/e2e_tester.py
import asyncio

async def run_command_stream(command: str, cwd: str, timeout: int = 600): # Increased timeout for build
    """Runs a command and streams its output."""
    print(f"Executing in '{cwd}': $ {command}")
    process = await asyncio.create_subprocess_shell(
        command, cwd=cwd,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        output = stdout.decode() + stderr.decode()
        return process.returncode == 0, output
    except asyncio.TimeoutError:
        process.kill()
        return False, f"Command timed out after {timeout} seconds."

async def run_e2e_tests(output_dir: str) -> tuple[bool, str]:
    """Builds, and runs Playwright E2E tests. Playwright's config now handles the server."""
    print("--- Running End-to-End (E2E) Tests ---")

    print("Installing Playwright...")
    success, output = await run_command_stream("npm install --save-dev @playwright/test && npx playwright install --with-deps", output_dir)
    if not success:
        print("\n--- PLAYWRIGHT INSTALL FAILURE DETAILS ---")
        print(output)
        print("-------------------------------------------\n")
        return False, f"Failed to install Playwright:\n{output}"

    # The 'npm run build' is now implicitly handled by Playwright's webServer config if not already built
    # But it's good practice to build explicitly first.
    print("Building production Next.js app...")
    success, output = await run_command_stream("npm run build", output_dir)
    if not success:
        print("\n--- NEXT.JS BUILD FAILURE DETAILS ---")
        print(output)
        print("-------------------------------------\n")
        return False, f"Next.js build failed:\n{output}"

    # Playwright will now automatically start and stop the server as defined in playwright.config.ts
    print("Running Playwright tests (Playwright will manage the server)...")
    success, output = await run_command_stream("npx playwright test", output_dir)
    
    if not success:
        print("\n--- PLAYWRIGHT TEST FAILURE DETAILS ---")
        print(output)
        print("---------------------------------------\n")
        
    return success, output