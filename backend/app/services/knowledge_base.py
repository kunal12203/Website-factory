# backend/app/services/knowledge_base.py
import mysql.connector
import re
import json
import uuid
from app.core.config import settings

def get_db_connection():
    """Establishes a connection to the MySQL database."""
    return mysql.connector.connect(
        host=settings.DB_HOST,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME
    )

def init_db():
    """Initializes the database and creates tables if they don't exist."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # --- START: CORRECTED SQL COMMAND ---
        # Provides the full, valid schema for the debugging_incidents table.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS debugging_incidents (
                id INT AUTO_INCREMENT PRIMARY KEY,
                error_signature VARCHAR(512) UNIQUE NOT NULL,
                full_error_log TEXT,
                successful_fix_prompt TEXT NOT NULL,
                successful_patch JSON NOT NULL,
                fix_agent VARCHAR(100),
                attempts_to_fix INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                confidence_score FLOAT DEFAULT 1.0
            )
        """)
        # --- END: CORRECTED SQL COMMAND ---
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS generation_sessions (
                session_id VARCHAR(36) PRIMARY KEY,
                checklist_json JSON,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP NULL,
                final_status ENUM('IN_PROGRESS', 'SUCCESS', 'FAILED') NOT NULL,
                final_output_path VARCHAR(255)
            )
        """)

        cursor.execute("""
    CREATE TABLE IF NOT EXISTS agent_prompts (
        id INT AUTO_INCREMENT PRIMARY KEY,
        role VARCHAR(100) NOT NULL,
        prompt_text TEXT NOT NULL,
        version INT DEFAULT 1,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY `unique_active_prompt` (`role`, `is_active`)
    )
""")
        conn.commit()
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        print(f"Failed to initialize database: {err}")

# --- (The rest of the file remains the same) ---

def create_session(checklist_json: dict) -> str:
    """Logs the start of a new generation session and returns its unique ID."""
    session_id = str(uuid.uuid4())
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "INSERT INTO generation_sessions (session_id, checklist_json, final_status) VALUES (%s, %s, %s)"
        cursor.execute(query, (session_id, json.dumps(checklist_json), 'IN_PROGRESS'))
        conn.commit()
        cursor.close()
        conn.close()
        print(f"📊 New Session Started: {session_id}")
        return session_id
    except mysql.connector.Error as err:
        print(f"Failed to create session: {err}")
        return ""

def update_session_status(session_id: str, status: str, output_path: str = ""):
    """Updates the final status and end time of a session."""
    if not session_id: return
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "UPDATE generation_sessions SET final_status = %s, final_output_path = %s, end_time = CURRENT_TIMESTAMP WHERE session_id = %s"
        cursor.execute(query, (status, output_path, session_id))
        conn.commit()
        cursor.close()
        conn.close()
        print(f"📊 Session {session_id} finished with status: {status}")
    except mysql.connector.Error as err:
        print(f"Failed to update session: {err}")

def create_error_signature(log: str) -> str | None:
    """Creates a simplified, consistent signature from a complex error log."""
    match = re.search(r"Error: (.*?)\n", log)
    if match:
        return f"build_error:{match.group(1).strip()}"
    
    match = re.search(r"● (.*?)\n\n\s*(.*?)\n", log, re.DOTALL)
    if match:
        return f"jest_error:{match.group(1).strip()}:{match.group(2).strip()}"
        
    return None

def find_known_solution(signature: str) -> str | None:
    """Queries the database for a single, known-good solution patch."""
    if not signature:
        return None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "SELECT successful_patch FROM debugging_incidents WHERE error_signature = %s ORDER BY confidence_score DESC LIMIT 1"
        cursor.execute(query, (signature,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result[0] if result else None
    except mysql.connector.Error as err:
        print(f"Database query failed: {err}")
        return None

def find_similar_incidents(signature: str, limit: int = 2) -> list:
    """Queries the DB for successfully resolved past incidents to use as examples."""
    if not signature:
        return []
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT error_signature, successful_fix_prompt, successful_patch FROM debugging_incidents WHERE error_signature LIKE %s ORDER BY confidence_score DESC LIMIT %s"
        like_signature = f"%{signature.split(':')[-1]}%"
        
        cursor.execute(query, (like_signature, limit))
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return results
    except mysql.connector.Error as err:
        print(f"Database query for similar incidents failed: {err}")
        return []

# In backend/app/services/knowledge_base.py

def get_active_prompt(role: str) -> str | None:
    """Fetches the active prompt for a specific agent role from the database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT prompt_text FROM agent_prompts WHERE role = %s AND is_active = TRUE"
        cursor.execute(query, (role,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        if result:
            print(f"✅ Loaded prompt for '{role}' from Knowledge Base.")
            return result['prompt_text']
        else:
            print(f"⚠️ No active prompt found for '{role}' in Knowledge Base. Using fallback.")
            return None
    except mysql.connector.Error as err:
        print(f"Database query for prompt failed: {err}")
        return None
    
def save_incident(signature: str, log: str, prompt: dict, patch_or_action: dict, agent: str, attempts: int):
    """Saves a new, successfully resolved incident to the Knowledge Base."""
    if not all([signature, log, patch_or_action]):
        return
    
    # This allows us to save either a code patch or an action dictionary
    solution_str = json.dumps(patch_or_action)
    prompt_str = json.dumps(prompt)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query_select = "SELECT id, confidence_score FROM debugging_incidents WHERE error_signature = %s"
        cursor.execute(query_select, (signature,))
        existing = cursor.fetchone()
        
        if existing:
            new_score = existing[1] + 1
            query_update = "UPDATE debugging_incidents SET confidence_score = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s"
            cursor.execute(query_update, (new_score, existing[0]))
        else:
            query_insert = "INSERT INTO debugging_incidents (error_signature, full_error_log, successful_fix_prompt, successful_patch, fix_agent, attempts_to_fix) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(query_insert, (signature, log, prompt_str, solution_str, agent, attempts))
        
        conn.commit()
        cursor.close()
        conn.close()
        print(f"✅ Knowledge Base updated for error: {signature}")
    except mysql.connector.Error as err:
        print(f"Failed to save incident to database: {err}")

    

def mark_solution_successful(signature: str):
        """Increase confidence score for a solution that worked."""
        if not signature:
            return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            query = "UPDATE debugging_incidents SET confidence_score = confidence_score + 1.5, updated_at = CURRENT_TIMESTAMP WHERE error_signature = %s"
            cursor.execute(query, (signature,))
            conn.commit()
            cursor.close()
            conn.close()
            print(f"✅ Increased confidence for solution: {signature}")
        except mysql.connector.Error as err:
            print(f"Failed to mark solution successful: {err}")

def mark_solution_failed(signature: str):
        """Decrease confidence score for a solution that failed."""
        if not signature:
            return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            query = "UPDATE debugging_incidents SET confidence_score = GREATEST(0.1, confidence_score - 0.5), updated_at = CURRENT_TIMESTAMP WHERE error_signature = %s"
            cursor.execute(query, (signature,))
            conn.commit()
            cursor.close()
            conn.close()
            print(f"⚠️ Decreased confidence for failed solution: {signature}")
        except mysql.connector.Error as err:
            print(f"Failed to mark solution failed: {err}")

def get_failed_solutions(signature: str, limit: int = 3) -> list:
        """Get previously failed solutions to avoid repeating them."""
        if not signature:
            return []
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            query = "SELECT successful_patch FROM debugging_incidents WHERE error_signature = %s AND confidence_score < 1.0 ORDER BY updated_at DESC LIMIT %s"
            cursor.execute(query, (signature, limit))
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            return [result['successful_patch'] for result in results]
        except mysql.connector.Error as err:
            print(f"Database query for failed solutions failed: {err}")
            return []
# Initialize the database when the module is loaded
init_db()