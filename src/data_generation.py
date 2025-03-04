import re
import random
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from db_connection import get_db_connection
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def interpret_param_value(placeholder_name: str, value_from_db: str) -> str:

    if re.match(r"^\d+-\d+$", value_from_db):
        min_str, max_str = value_from_db.split("-")
        min_val, max_val = int(min_str), int(max_str)
        return str(random.randint(min_val, max_val))
    
    if value_from_db.startswith("RANDOM(") and value_from_db.endswith(")"):
        inside = value_from_db[len("RANDOM("):-1]
        options = [opt.strip() for opt in inside.split(",")]
        return random.choice(options)
    
    if value_from_db.startswith("DATE(") and value_from_db.endswith(")"):
        format_str = value_from_db[len("DATE("):-1]
        format_str = format_str.replace("YY", "%y").replace("YYYY", "%Y")
        format_str = format_str.replace("MM", "%m").replace("DD", "%d")
        return datetime.now().strftime(format_str)
    
    if value_from_db.startswith("REF(") and value_from_db.endswith(")"):
        inside = value_from_db[len("REF("):-1]
        parts = [p.strip() for p in inside.split(",")]
        if len(parts) != 2:
            raise ValueError(f"REF format should be REF(prefix,length), got {value_from_db}")
        prefix, length_str = parts
        try:
            length = int(length_str)
            random_part = ''.join(str(random.randint(0, 9)) for _ in range(length))
            return f"{prefix}{random_part}"
        except ValueError:
            raise ValueError(f"REF length must be an integer, got {length_str}")
    
    return value_from_db

def get_template_and_placeholders(template_name: str) -> Tuple[int, str, List[str]]:
    """Get template details and extract placeholders."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT template_id, template_text
                FROM template
                WHERE template_name = %s
                LIMIT 1
            """, (template_name,))
            row = cur.fetchone()
            if not row:
                raise ValueError(f"No template found with name='{template_name}'")
            
            template_id, template_text = row
            
            placeholders = re.findall(r"\{([\w_]+)\}", template_text)
            if not placeholders:
                raise ValueError(f"No placeholders found in template '{template_name}'.")
                
            return template_id, template_text, placeholders
    finally:
        conn.close()

def get_params_for_placeholders(placeholders: List[str]) -> Dict[str, str]:
    """Fetch parameters for each placeholder from database."""
    conn = get_db_connection()
    try:
        placeholder_map = {}
        with conn.cursor() as cur:
            for ph in placeholders:
                cur.execute("""
                    SELECT param_value
                    FROM parameters
                    WHERE param_name = %s
                    ORDER BY param_id
                    LIMIT 1
                """, (ph,))
                res = cur.fetchone()
                if not res:
                    raise ValueError(f"No parameter found for placeholder '{ph}'")
                
                value_from_db = res[0]
                final_val = interpret_param_value(ph, value_from_db)
                placeholder_map[ph] = final_val
                
        return placeholder_map
    finally:
        conn.close()

def fill_template_and_insert(template_name: str) -> int:
    """
    1) Fetch the template_text from 'template' by template_name.
    2) Extract placeholders (e.g. {amount}, {currency}).
    3) For each placeholder, fetch 'param_value' from 'parameters'.
       Then interpret (range, random, or fixed).
    4) Replace placeholders in the template text.
    5) Insert the filled message into 'messages', returning message_id.
    """
    conn = get_db_connection()
    try:
        template_id, template_text, placeholders = get_template_and_placeholders(template_name)
        
        placeholder_map = get_params_for_placeholders(placeholders)
        
        filled_text = template_text
        for ph, val in placeholder_map.items():
            filled_text = filled_text.replace(f"{{{ph}}}", val)
        
        # 5) Insert into messages
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO messages (template_id, generated_text)
                VALUES (%s, %s)
                RETURNING message_id
            """, (template_id, filled_text))
            new_msg_id = cur.fetchone()[0]
        
        conn.commit()
        return new_msg_id
    except Exception as e:
        conn.rollback()
        logger.error(f"Error in fill_template_and_insert: {e}")
        raise
    finally:
        conn.close()

'''
def validate_swift_message(message: str) -> bool:

    return True
'''

def generate_messages(template_name: str, count: int = 1, validate: bool = True) -> List[int]:
    message_ids = []
    for i in range(count):
        try:
            new_id = fill_template_and_insert(template_name)
            logger.info(f"[{i+1}/{count}] Created message_id={new_id} from '{template_name}'")
            
            if validate:
                # Fetch the message we just created to validate it
                conn = get_db_connection()
                try:
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT generated_text FROM messages WHERE message_id = %s
                        """, (new_id,))
                        message_text = cur.fetchone()[0]
                        
                    #if not validate_swift_message(message_text):
                finally:
                    conn.close()
            
            message_ids.append(new_id)
        except ValueError as ex:
            logger.error(f"Error generating message #{i+1}: {ex}")
            break
    
    return message_ids

def batch_generate_with_stats(template_names: List[str], count_per_template: int = 10) -> Dict:
    """
    Generate multiple messages from multiple templates and return statistics.
    
    Args:
        template_names: List of template names to use
        count_per_template: Number of messages to generate per template
        
    Returns:
        Dictionary with statistics about generation process
    """
    start_time = datetime.now()
    stats = {
        "total_templates": len(template_names),
        "total_messages_requested": len(template_names) * count_per_template,
        "successful_generations": 0,
        "failed_generations": 0,
        "messages_by_template": {},
        "execution_time": None
    }
    
    for template_name in template_names:
        try:
            message_ids = generate_messages(template_name, count_per_template)
            successful = len(message_ids)
            failed = count_per_template - successful
            
            stats["successful_generations"] += successful
            stats["failed_generations"] += failed
            stats["messages_by_template"][template_name] = {
                "successful": successful,
                "failed": failed,
                "message_ids": message_ids
            }
        except Exception as e:
            logger.error(f"Template '{template_name}' failed completely: {e}")
            stats["failed_generations"] += count_per_template
            stats["messages_by_template"][template_name] = {
                "successful": 0,
                "failed": count_per_template,
                "error": str(e)
            }
    
    stats["execution_time"] = (datetime.now() - start_time).total_seconds()
    return stats
