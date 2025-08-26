# backend/app/services/file_handler.py
import os
import json
import shutil
import glob
from datetime import datetime
import re

def create_output_dir() -> str:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_dir = os.path.join(os.getcwd(), "output", f"site-{timestamp}")
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def get_file_content(full_code_string: str, file_path: str) -> str | None:
    """Extracts the content of a single file from the AI's full response string."""
    # Use a regex that is robust to different path formats (e.g., with or without leading '/')
    sanitized_path = file_path.strip().lstrip('/')
    pattern = re.compile(f"// FILE:.*?{re.escape(sanitized_path)}\n(.*?)(?=\n// FILE:|\Z)", re.DOTALL)
    match = pattern.search(full_code_string)
    return match.group(1).strip() if match else None

def replace_file_content(full_code_string: str, file_path: str, new_content: str) -> str:
    """Replaces the content of a single file in the AI's full response string."""
    sanitized_path = file_path.strip().lstrip('/')
    pattern = re.compile(f"(// FILE:.*?{re.escape(sanitized_path)}\n)(.*?)(?=\n// FILE:|\Z)", re.DOTALL)
    
    header = f"// FILE: {sanitized_path}\n"
    replacement = f"{header}{new_content.strip()}"
    
    # If pattern is found, replace it
    if pattern.search(full_code_string):
        return pattern.sub(replacement, full_code_string, count=1)
    else: # If file not found, append it
        return f"{full_code_string}\n\n{replacement}"


async def write_files_from_ai_response(output_dir: str, ai_response: str):
    file_regex = r"// FILE: (.+?)\n"
    # Clean up markdown fences that the AI might add
    cleaned_response = re.sub(r"```(typescript|javascript|tsx|jsx)?", "", ai_response.strip())
    
    files = re.split(file_regex, cleaned_response)
    
    if len(files) <= 1:
        print(f"Warning: No files found in AI response using '// FILE:' delimiter.")
        return

    for i in range(1, len(files), 2):
        sanitized_path = files[i].strip().lstrip('/')
        file_path = os.path.join(output_dir, sanitized_path)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as f:
            f.write(files[i+1].strip())

async def create_config_files(output_dir: str, checklist: dict):
    # ... (package.json, tailwind.config.ts, postcss.config.js generation remains the same)
    project_name = os.path.basename(output_dir)
    package_json_content = {
      "name": project_name, "version": "0.1.0", "private": True,
      "scripts": { "dev": "next dev", "build": "next build", "start": "next start", "lint": "next lint", "test": "jest", "test:e2e": "playwright test" }
    }
    with open(os.path.join(output_dir, 'package.json'), 'w') as f:
        json.dump(package_json_content, f, indent=2)

    primary_color = checklist.get('branding', {}).get('colors', {}).get('primary', '#000000')
    secondary_color = checklist.get('branding', {}).get('colors', {}).get('secondary', '#FFFFFF')
    tailwind_config_content = f"""
/** @type {{import('tailwindcss').Config}} */
module.exports = {{
  content: [ "./src/**/*.{{js,ts,jsx,tsx,mdx}}", "./app/**/*.{{js,ts,jsx,tsx,mdx}}",],
  theme: {{ extend: {{ colors: {{ primary: '{primary_color}', secondary: '{secondary_color}', }}, }}, }},
  plugins: [],
}};
"""
    with open(os.path.join(output_dir, 'tailwind.config.ts'), 'w') as f:
        f.write(tailwind_config_content)
    
    postcss_config_content = "module.exports = { plugins: { tailwindcss: {}, autoprefixer: {} } };"
    with open(os.path.join(output_dir, 'postcss.config.js'), 'w') as f:
        f.write(postcss_config_content)

    jest_config_content = """
const nextJest = require('next/jest')
const createJestConfig = nextJest({ dir: './' })
const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  testEnvironment: 'jest-environment-jsdom',
  moduleNameMapper: { '^@/components/(.*)$': '<rootDir>/components/$1', '^@/app/(.*)$': '<rootDir>/app/$1', },
}
module.exports = createJestConfig(customJestConfig)
"""
    with open(os.path.join(output_dir, 'jest.config.js'), 'w') as f:
        f.write(jest_config_content)

    jest_setup_content = "require('@testing-library/jest-dom');"
    with open(os.path.join(output_dir, 'jest.setup.js'), 'w') as f:
        f.write(jest_setup_content)
    
    tsconfig_content = {"compilerOptions": {"lib": ["dom","dom.iterable","esnext"],"allowJs": True,"skipLibCheck": True,"strict": True,"noEmit": True,"esModuleInterop": True,"module": "esnext","moduleResolution": "bundler","resolveJsonModule": True,"isolatedModules": True,"jsx": "preserve","incremental": True,"plugins": [{"name": "next"}],"paths": {"@/*": ["./src/*"]}},"include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],"exclude": ["node_modules"]}
    with open(os.path.join(output_dir, 'tsconfig.json'), 'w') as f: json.dump(tsconfig_content, f, indent=2)

    # --- THIS IS THE NEW, CRITICAL CONFIGURATION ---
    test_port = 4001
    playwright_config_content = f"""
import {{ defineConfig, devices }} from '@playwright/test';

export default defineConfig({{
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {{
    baseURL: 'http://localhost:{test_port}',
    trace: 'on-first-retry',
  }},
  projects: [
    {{
      name: 'chromium',
      use: {{ ...devices['Desktop Chrome'] }},
    }},
  ],
  webServer: {{
    command: 'npm run start -- -p {test_port}',
    url: 'http://localhost:{test_port}',
    reuseExistingServer: !process.env.CI,
    stdout: 'pipe',
    stderr: 'pipe',
  }},
}});
"""
    with open(os.path.join(output_dir, 'playwright.config.ts'), 'w') as f:
        f.write(playwright_config_content)
    
async def cleanup_test_files(output_dir: str):
    print("--- Cleaning up test files and configs ---")
    items_to_remove = ["jest.config.js", "jest.setup.js", "babel.config.js", "tsconfig.json"]
    for item in items_to_remove:
        path = os.path.join(output_dir, item)
        if os.path.isfile(path): os.remove(path)
            
    test_files = glob.glob(os.path.join(output_dir, '**', '*.test.tsx'), recursive=True)
    for file_path in test_files:
        os.remove(file_path)