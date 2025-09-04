# backend/app/services/component_tester.py
import asyncio
import os


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


async def install_dependencies(output_dir: str):
    """
    Install dependencies for the generated project.
    (npm install --force to avoid peer dep issues)
    """
    print("📦 Installing dependencies...")
    return await run_command_stream("npm install --force", cwd=output_dir)


async def run_component_tests(output_dir: str):
    """
    Run Jest component tests.
    Returns (success: bool, logs: str)
    """
    print("🧪 Running component tests (Jest)...")
    return await run_command_stream("npm test -- --runInBand", cwd=output_dir)

# Add this new function to the file
async def run_single_component_test(output_dir: str, test_file_path: str):
    """
    Run a single Jest test file.
    """
    print(f"🔬 Running single test: {test_file_path}")
    # The command runs jest and specifies the single test file to run
    return await run_command_stream(f"npm test -- {test_file_path}", cwd=output_dir)


# In backend/app/services/component_tester.py

async def reset_node_modules(output_dir: str):
    """
    Deletes node_modules and package-lock.json, then runs a fresh npm install.
    This is a powerful reset step for fixing corrupted dependency issues.
    """
    print(" Bashing node_modules and package-lock.json to fix dependency issues...")
    
    # Use '&&' to chain commands safely. The '|| true' handles cases where a file might not exist.
    reset_command = (
        "rm -rf node_modules package-lock.json || true && "
        "npm cache clean --force || true && "
        "npm install"
    )
    
    success, logs = await run_command_stream(reset_command, cwd=output_dir)
    if not success:
        print(f"  Failed to reset node modules. Logs:\n{logs}")
    else:
        print("  Node modules have been successfully reset.")
    return success