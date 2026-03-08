import { supabase } from '../supabaseClient';

export { supabase };

export async function processItem({
    status,
    file,
    userCategory = null,
    location = null,
    time = null,
    description = null,
    userId = 'demo_user',
    userEmail = 'demo@test.com',
}: {
    status: string;
    file: File;
    userCategory?: string | null;
    location?: string | null;
    time?: string | null;
    description?: string | null;
    userId?: string;
    userEmail?: string;
}) {
    if (!file) throw new Error('Image file is required');

    const fileExt = file.name.split('.').pop();
    const tempId = crypto.randomUUID();
    const filePath = `${status}/${tempId}.${fileExt}`;

    // 1️⃣ Upload image to Supabase Storage (items bucket)
    const { error: uploadError } = await supabase.storage.from('items').upload(filePath, file);
    if (uploadError) throw uploadError;

    // 2️⃣ Get public URL
    const { data } = supabase.storage.from('items').getPublicUrl(filePath);
    const imageUrl = data.publicUrl;

    // 3️⃣ Insert row into items table
    const { data: inserted, error: insertError } = await supabase
        .from('items')
        .insert({
            user_id: userId,
            user_email: userEmail,
            item_type: status,
            image_url: imageUrl,
            user_category: userCategory,
            location,
            description,
            status: 'active',
        })
        .select();
    if (insertError) throw insertError;

    const itemId = inserted[0].id;

    // 4️⃣ Call group AI backend via Vite proxy
    const payload = {
        item_id: itemId,
        item_type: status,
        image_url: imageUrl,
        user_category: userCategory,
        k: 4,
        mc_T: 20,
    };

    const res = await fetch('/items/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    });

    return res.json();
}
