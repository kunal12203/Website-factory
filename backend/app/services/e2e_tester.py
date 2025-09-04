# backend/app/services/e2e_tester.py
import asyncio


async def run_command_stream(cmd: str, cwd: str):
    """
    Run a shell command asynchronously and capture logs.
    Returns (success: bool, logs: str)
    """
    process = await asyncio.create_subprocess_shell(
        cmd,
        cwd=cwd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()
    logs = stdout.decode() + "\n" + stderr.decode()
    success = process.returncode == 0

    return success, logs


async def execute_playwright_tests(output_dir: str):
    """
    Run Playwright E2E tests.
    Returns (success: bool, logs: str)
    """
    print("🎭 Running Playwright E2E tests...")
    return await run_command_stream("npx playwright test --reporter=line", cwd=output_dir)
