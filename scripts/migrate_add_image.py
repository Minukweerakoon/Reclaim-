"""
Migration: Add image_url column + create storage bucket for report images.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

from supabase import create_client

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
client = create_client(url, key)

# 1. Add image_url column to both tables
print("=" * 60)
print("STEP 1: Adding image_url column to tables")
print("=" * 60)

for table in ["lost_items", "found_items"]:
    try:
        result = client.rpc("", {}).execute()  # won't work, use raw SQL
    except:
        pass

# Use postgrest to run raw SQL via the pg_execute function
# Actually, Supabase Python client doesn't have raw SQL. Use psycopg2 or the REST API.
import requests

# Use the Supabase REST API to run SQL
headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json",
}

# Run SQL via the /rest/v1/rpc endpoint or the query endpoint
# Actually the best approach is to directly call the pg-meta endpoint
# Let's use the Supabase management API

# Alternative: just use the postgREST rpc if we have a function
# Simplest: use the /pg endpoint

# Let's just try inserting into a table with image_url and see if it fails
# If it fails, we know the column doesn't exist
print("Testing if image_url column exists...")
try:
    test = client.table("lost_items").select("image_url").limit(1).execute()
    print(f"  lost_items.image_url already exists! Rows: {len(test.data)}")
except Exception as e:
    print(f"  lost_items.image_url does NOT exist: {e}")
    print("  >> You need to add it manually in Supabase SQL Editor:")
    print("     ALTER TABLE lost_items ADD COLUMN image_url TEXT;")

try:
    test = client.table("found_items").select("image_url").limit(1).execute()
    print(f"  found_items.image_url already exists! Rows: {len(test.data)}")
except Exception as e:
    print(f"  found_items.image_url does NOT exist: {e}")
    print("  >> You need to add it manually in Supabase SQL Editor:")
    print("     ALTER TABLE found_items ADD COLUMN image_url TEXT;")

# 2. Create storage bucket
print()
print("=" * 60)
print("STEP 2: Creating storage bucket 'report-images'")
print("=" * 60)

try:
    result = client.storage.create_bucket(
        "report-images",
        options={
            "public": True,
            "file_size_limit": 10485760,  # 10MB
            "allowed_mime_types": ["image/jpeg", "image/png", "image/webp"],
        }
    )
    print(f"  Bucket created: {result}")
except Exception as e:
    err_str = str(e)
    if "already exists" in err_str.lower() or "duplicate" in err_str.lower():
        print(f"  Bucket 'report-images' already exists (OK)")
    else:
        print(f"  Error creating bucket: {e}")

# 3. Test upload
print()
print("=" * 60)
print("STEP 3: Test image upload to storage")
print("=" * 60)

test_image = r"c:\Users\16473\Desktop\multimodel-validation\Balanced_Dataset\Laptop\laptops_100_aug0.jpg"
if os.path.exists(test_image):
    with open(test_image, "rb") as f:
        img_data = f.read()
    
    try:
        storage_path = "test/laptops_100_aug0.jpg"
        result = client.storage.from_("report-images").upload(
            path=storage_path,
            file=img_data,
            file_options={"content-type": "image/jpeg", "upsert": "true"},
        )
        print(f"  Upload result: {result}")
        
        # Get public URL
        public_url = client.storage.from_("report-images").get_public_url(storage_path)
        print(f"  Public URL: {public_url}")
    except Exception as e:
        print(f"  Upload error: {e}")
else:
    print(f"  Test image not found: {test_image}")

print()
print("DONE!")
