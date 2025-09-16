# backend/app/services/file_handler.py
import os
import aiofiles
import shutil
import datetime
import json

def create_output_dir(base_dir: str = "output") -> str:
    """Create a unique output directory for each generation run."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    output_dir = os.path.join(base_dir, f"site-{timestamp}")
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def setup_scaffold(output_dir: str, checklist: dict):
    """Copies the golden_scaffold and updates the tailwind.config.ts with brand colors."""
    scaffold_dir = "golden_scaffold"
    if not os.path.isdir(scaffold_dir):
        raise FileNotFoundError(f"Golden scaffold directory not found at '{scaffold_dir}'")
        
    shutil.copytree(scaffold_dir, output_dir, dirs_exist_ok=True)
    print(f"✅ Golden scaffold copied to {output_dir}")

    try:
        primary_color = checklist.get("branding", {}).get("colors", {}).get("primary", "#000000")
        secondary_color = checklist.get("branding", {}).get("colors", {}).get("secondary", "#FFFFFF")

        tailwind_config_path = os.path.join(output_dir, "tailwind.config.ts")
        with open(tailwind_config_path, "r") as f:
            content = f.read()
        
        content = content.replace("'#6366F1'", f"'{primary_color}'")
        content = content.replace("'#10B981'", f"'{secondary_color}'")

        with open(tailwind_config_path, "w") as f:
            f.write(content)
        print("🎨 Tailwind config updated with brand colors.")

    except Exception as e:
        print(f"⚠️ Could not update tailwind config: {e}")

async def write_file(output_dir: str, filename: str, content: str):
    """Write a single file safely, creating directories if needed."""
    if not filename or not content:
        print(f"⚠️ Skipping write for empty filename or content.")
        return
    
    filepath = os.path.join(output_dir, filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    async with aiofiles.open(filepath, "w", encoding='utf-8') as f:
        await f.write(content)
    print(f"✅ Wrote file: {filename}")

# In backend/app/services/file_handler.py

async def read_all_code_files(output_dir: str) -> dict:
    """
    Reads all RELEVANT code files from the output directory into a dictionary,
    excluding unnecessary files and directories.
    """
    code_files = {}
    # --- START: NEW EXCLUSION LISTS ---
    excluded_dirs = {'node_modules', '.next', '.vscode'}
    excluded_files = {'package-lock.json'}
    # --- END: NEW EXCLUSION LISTS ---

    for root, dirs, files in os.walk(output_dir):
        # Modify the dir list in-place to prevent os.walk from descending into excluded directories
        dirs[:] = [d for d in dirs if d not in excluded_dirs]
        
        for file in files:
            if file in excluded_files:
                continue

            if file.endswith((".tsx", ".ts", ".css", ".js", ".mjs", ".json")):
                filepath = os.path.join(root, file)
                relative_path = os.path.relpath(filepath, output_dir)
                try:
                    # Using standard open for this synchronous function part
                    with open(filepath, "r", encoding='utf-8', errors='ignore') as f:
                        code_files[relative_path] = f.read()
                except Exception as e:
                    print(f"Warning: Could not read file {filepath}: {e}")
                    continue
                    
    return code_files