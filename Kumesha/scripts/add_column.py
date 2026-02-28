"""Add image_url column using the Supabase client's RPC capability."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

import requests

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Use the Supabase REST SQL endpoint (available via service role key)
sql_url = f"{url}/rest/v1/rpc"

headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal",
}

# Try the pg_net approach - actually let's just use psycopg2 or the direct DB connection
# The simplest is to use the Supabase postgREST query approach

# Actually, let's try using the supabase-py client to check if column exists
from supabase import create_client
client = create_client(url, key)

# Test if column already exists
print("Checking if image_url column exists...")
try:
    test = client.table("lost_items").select("image_url").limit(1).execute()
    print(f"  lost_items.image_url EXISTS (rows: {len(test.data)})")
    col_exists_lost = True
except Exception as e:
    print(f"  lost_items.image_url MISSING")
    col_exists_lost = False

try:
    test = client.table("found_items").select("image_url").limit(1).execute()
    print(f"  found_items.image_url EXISTS (rows: {len(test.data)})")
    col_exists_found = True
except Exception as e:
    print(f"  found_items.image_url MISSING")
    col_exists_found = False

if not col_exists_lost or not col_exists_found:
    # Use direct PostgreSQL connection via DATABASE_URL
    db_url = os.getenv("DATABASE_URL", "")
    if not db_url:
        # Construct from Supabase project
        # Try the Supabase SQL API endpoint
        sql_api_url = f"{url}/pg/query"
        print(f"\nAttempting SQL via {sql_api_url}...")
        
        for table in ["lost_items", "found_items"]:
            sql = f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS image_url TEXT;"
            resp = requests.post(
                sql_api_url,
                headers=headers,
                json={"query": sql}
            )
            print(f"  {table}: {resp.status_code} - {resp.text[:200]}")
    else:
        print(f"\nUsing DATABASE_URL to add columns...")
        try:
            import psycopg2
            conn = psycopg2.connect(db_url)
            cur = conn.cursor()
            for table in ["lost_items", "found_items"]:
                cur.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS image_url TEXT;")
                print(f"  Added image_url to {table}")
            conn.commit()
            cur.close()
            conn.close()
            print("  DONE!")
        except ImportError:
            print("  psycopg2 not installed. Install with: pip install psycopg2-binary")
        except Exception as e:
            print(f"  Error: {e}")
else:
    print("\nBoth columns already exist! No migration needed.")
