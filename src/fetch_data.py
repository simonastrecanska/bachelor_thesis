import psycopg2
import config as config 

def fetch_templates(conn):
    """Fetch all templates from the TEMPLATE table."""
    with conn.cursor() as cur:
        cur.execute("SELECT template_id, template_name, template_text FROM template")
        return cur.fetchall()

def main():
    conn = psycopg2.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        database=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD
    )
    templates = fetch_templates(conn)
    print("Fetched templates:")
    for tpl in templates:
        print(f"Template ID: {tpl[0]}, Name: {tpl[1]}, Text: {tpl[2]}")
    
    conn.close()

if __name__ == "__main__":
    main()