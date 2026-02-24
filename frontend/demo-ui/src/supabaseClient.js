import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

export const supabase = createClient(supabaseUrl, supabaseAnonKey);


export async function processItem({
  status,
  file,
  userCategory = null,
  location = null,
  time = null,
  description = null,
  userId = "demo_user",
  userEmail = "demo@test.com",
}) {
  if (!file) throw new Error("Image file is required");

  const fileExt = file.name.split(".").pop();
  const tempId = crypto.randomUUID();
  const filePath = `${status}/${tempId}.${fileExt}`;

  // 1️⃣ Upload image
  const { error: uploadError } = await supabase.storage
    .from("items")
    .upload(filePath, file);

  if (uploadError) throw uploadError;

  // 2️⃣ Get public URL
  const { data } = supabase.storage.from("items").getPublicUrl(filePath);
  const imageUrl = data.publicUrl;

  // 3️⃣ Insert row
  const { data: inserted, error: insertError } = await supabase
    .from("items")
    .insert({
      user_id: userId,
      user_email: userEmail,
      item_type: status,
      image_url: imageUrl,
      user_category: userCategory,
      location: location,
      time_of_incident: time,
      description: description,
      status: "active",
    })
    .select();

  if (insertError) throw insertError;

  const itemId = inserted[0].id;

  // 4️⃣ Call AI backend
  const payload = {
    item_id: itemId,
    item_type: status,
    image_url: imageUrl,
    user_category: userCategory,
    k: 4,
    mc_T: 20,
  };

  const res = await fetch("http://127.0.0.1:8000/items/process", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const responseData = await res.json();
  return responseData;
}