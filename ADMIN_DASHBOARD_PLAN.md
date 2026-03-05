# Admin Dashboard for Real-Time Suspicious Behavior Detection – Plan

This plan adds an **admin-only dashboard** to the frontend with:
- **Video upload** (Voshan process-video)
- **Real-time notifications** (WebSocket alerts)
- **Alert history** (alert cards with frame images)

Only **one user** (admin) can access this dashboard; others are blocked after Google login.

---

## Overview

| Layer | What you add |
|-------|----------------|
| **Config** | One admin email (env or Supabase) |
| **Frontend** | Admin check, Admin dashboard page, route guard |
| **Backend (optional)** | Optional: protect Voshan API by admin email |

---

## Step 1: Define the admin user

**Option A – Env allowlist (simplest, one email)**

- In **frontend** `.env`:
  ```env
  VITE_ADMIN_EMAIL=voshan1996@gmail.com
  ```
- Only this email is treated as admin. No database change.
- **Done:** `frontend/.env` has this set; `src/utils/admin.ts` defaults to this email if env is missing.

**Option B – Supabase table (flexible later)**

- In Supabase: create table `admin_users` with columns `id`, `email`, `created_at`.
- Insert one row with the admin email.
- Frontend calls a small API or Supabase RPC to check `current_user.email` against this table.

**Recommendation:** Start with **Option A** (env). You can switch to Option B later.

---

## Step 2: Add admin check in the frontend

1. **Create `src/utils/admin.ts`** (or `src/reclaim/admin.ts` if you keep reclaim under `/reclaim`):
   - `getAdminEmail(): string | undefined` → reads `import.meta.env.VITE_ADMIN_EMAIL`.
   - `isAdminUser(user: { email?: string } | null): boolean` → returns `user?.email === getAdminEmail()` (case-insensitive).

2. **Use the same auth as Google login**
   - ReclaimApp already uses `supabase.auth.getSession()` and `onAuthStateChange` and has `user`.
   - So: after Google login, `user.email` is available. Use `isAdminUser(user)` to decide if the user can see the admin dashboard.

---

## Step 3: Add the Admin Dashboard route

**Where to mount the dashboard**

- **Option 1 – Under `/reclaim` (recommended):**  
  - Route: `/reclaim/admin`.  
  - Handled inside `ReclaimApp`: when path is `/reclaim/admin`, render the Admin Dashboard only if `isAdminUser(user)`; otherwise redirect to `/reclaim` or show “Access denied”.

- **Option 2 – At app root:**  
  - Route: `/admin-dashboard`.  
  - Wrap in a guard that uses main app auth (e.g. `AuthContext`) and `isAdminUser(user)`; if not admin, redirect to `/` or `/reclaim`.

**Recommendation:** Use **Option 1** so the dashboard lives with the Reclaim/Voshan feature and reuses the same Supabase session (Google login) from ReclaimApp.

**Implementation outline**

- In `ReclaimApp`, use `useLocation()` or nested `<Routes>`:
  - If path is `/reclaim/admin` (or `*` match for `admin`):
    - If not logged in → redirect to `/reclaim` login flow.
    - If logged in and `!isAdminUser(user)` → redirect to `/reclaim` and optionally show a toast “Access denied”.
    - If logged in and `isAdminUser(user)` → render `<AdminDashboard />`.

- In `App.tsx` you already have `<Route path="/reclaim/*" element={<ReclaimApp />} />`, so no change there; only ReclaimApp gains an inner route for `admin`.

---

## Step 4: Build the Admin Dashboard page

Create **`AdminDashboard`** (e.g. `src/reclaim/pages/AdminDashboard.tsx` or `src/pages/AdminDashboard.tsx`).

**Sections:**

1. **Header**
   - Title: e.g. “Suspicious Behavior Detection – Admin”.
   - Show logged-in user (e.g. `user.email`) and a “Sign out” button (reuse existing sign-out from ReclaimApp).
   - Optional: “Back to Reclaim” linking to `/reclaim`.

2. **Video upload**
   - Form: file input (video), optional camera ID, “Save output” checkbox.
   - On submit: call Voshan backend `POST /api/voshan/detection/process-video` (multipart `video`).
   - Reuse or copy the logic from your existing Voshan upload component (e.g. `processVideo` from detection API, progress, success/error handling).
   - After success: show a short success message and optionally refresh the alert list below.

3. **Real-time notifications**
   - Connect to Voshan WebSocket: `ws://<backend>/api/voshan/socket.io` (or the URL from your Voshan backend).
   - On `alert` (or whatever event the backend sends): show a toast/notification (e.g. “New alert: BAG_UNATTENDED – High”).
   - Reuse or adapt your existing Voshan WebSocket hook/component if you have one.

4. **Alert history**
   - Call `GET /api/voshan/detection/alerts` (with pagination: `page`, `limit`).
   - For each alert, render an **alert card**:
     - Type, severity, timestamp, camera ID.
     - **Frame image:** if the backend stores or returns a frame URL (e.g. from `alert_frames` or Supabase storage), show it in the card; otherwise show a placeholder or “No frame”.
   - Optional: filters (type, severity, camera, date range) and “Refresh” button.

**API base URL**

- Ensure the frontend uses the correct Voshan backend base URL (e.g. `VITE_VOSHAN_API_URL` or existing `VITE_API_URL` pointing to the Node backend that proxies to Voshan).

---

## Step 5: Link to the Admin Dashboard only for admin

- In **HomePage** (or the Reclaim home view that shows after login), conditionally show a button/link “Admin Dashboard” only when `isAdminUser(user)`.
  - Example: `{isAdminUser(user) && <Link to="/reclaim/admin">Admin Dashboard</Link>}` or a button that navigates to `/reclaim/admin`.
- Do **not** show this link for non-admin users.

---

## Step 6: (Optional) Backend protection for Voshan API

- In the **Voshan backend** (Node), for routes that modify data or return sensitive lists (e.g. `process-video`, `alerts`):
  - Read `Authorization: Bearer <token>` and validate the token with Supabase (e.g. `supabase.auth.getUser(accessToken)`).
  - If the token is valid, get `user.email` and compare to an allowlist (e.g. `ADMIN_EMAIL` in backend `.env`).
  - If not admin → respond with `403 Forbidden`.
- This way, even if someone discovers the API, only the admin can upload videos or list alerts. Frontend guard alone is enough for UX; backend check is for security.

---

## Step 7: Frame images in alert cards

- **Backend (Voshan):**  
  - Alerts are stored in Supabase (`sus_alerts` or similar). If you want frame images:
    - Either store a **URL** (e.g. Supabase Storage public URL or path like `/api/voshan/detection/alert-frames/<id>.jpg`) in the alert record, or
    - Serve frames from a known path (you already have `alert-frames` static route) and build the URL from `alert_id` or `frame_number`.
- **Frontend:**  
  - In each alert card, if the alert has `frame_url` or you can build it from `alert_id`/`frame`, set `<img src={frameUrl} />`; otherwise show a placeholder.

---

## Order of implementation (summary)

1. **Config:** Add `VITE_ADMIN_EMAIL` to frontend `.env`.
2. **Util:** Add `src/utils/admin.ts` with `getAdminEmail` and `isAdminUser`.
3. **Route:** In ReclaimApp, add route for `/reclaim/admin` with guard: must be logged in and `isAdminUser(user)`.
4. **Page:** Create `AdminDashboard` with upload, WebSocket notifications, and alert list.
5. **API:** Ensure detection API client (process-video, alerts, WebSocket) uses the correct Voshan backend URL.
6. **Nav:** On Reclaim home, show “Admin Dashboard” link only when `isAdminUser(user)`.
7. **(Optional)** Backend: validate JWT and admin email for Voshan routes.
8. **(Optional)** Add frame image URL to alerts and show it in alert cards.

---

## File checklist

| Action | File / place |
|--------|------------------|
| Add env | `frontend/.env` → `VITE_ADMIN_EMAIL=voshan1996@gmail.com` ✅ |
| Create | `frontend/src/utils/admin.ts` (or under `reclaim/`) ✅ |
| Create | `frontend/src/reclaim/pages/AdminDashboard.tsx` (or `src/pages/`) |
| Modify | `frontend/src/reclaim/ReclaimApp.tsx` – routes + admin guard + link to dashboard |
| Modify | `frontend/src/pages/HomePage.tsx` – conditional “Admin Dashboard” link |
| Optional | Voshan backend: middleware or route-level admin check using Supabase JWT + allowlist |
| Optional | Voshan backend + frontend: frame URL in alert response and in alert card |

---

## Security note

- **Frontend-only check:** Hides the dashboard from non-admins but does not prevent a non-admin from calling the API if they know the URL. Use for UX.
- **Backend check:** Validates the same admin email (or role) on the server and returns 403 for non-admins. Use for real protection.

Once this is in place, only the one admin user (by email) can open the admin dashboard and, if you add Step 6, only they can use the Voshan upload and alerts API.
