# SkyMatrix

An ESP32-CAM inference pipeline and browser dashboard, organized as one project rooted in this folder.

## Architecture

- `backend/`: FastAPI API, YOLO inference service, Cloudinary image repository, and Firebase Admin/Firestore access.
- `backend/models/best.pt`: the custom trained model copied from `Mini_Project`.
- `frontend/`: React + TypeScript dashboard, organized into `models`, `services`, `viewmodels`, and `views` (MVVM).
- `firebase.json`: Firebase Hosting configuration for the built dashboard.
- `render.yaml`: Render deployment definition for the inference API.

Each ESP32-CAM frame is uploaded to Render, inferred with the custom YOLO model at confidence `0.45`, annotated with boxes, class names, and confidence scores, uploaded to Cloudinary, and indexed in Firestore. The dashboard refreshes the latest 50 records every 15 seconds and displays each annotated image.

Firebase Hosting serves the frontend. Cloudinary stores images. Firestore's `(default)` database stores prediction metadata and image URLs. Supabase is not used. Keep the Cloudinary API secret, Firebase service-account JSON, and device key on the backend only. The current dashboard read endpoint and Cloudinary delivery URLs are public; add Firebase Authentication before using this with sensitive operational imagery or locations.

## Local setup

1. Create a Python 3.11 environment and install the backend requirements:

   ```powershell
   cd backend
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   Copy-Item .env.example .env
   ```

2. Fill in `backend/.env` with `CLOUDINARY_URL`, the Firebase service-account JSON for project `skymatrix-hd`, and a long random `DEVICE_API_KEY`. Set `FIRESTORE_DATABASE_ID=(default)`. The backend writes documents to the `predictions` collection; keep Firestore access restricted to the Admin SDK.

3. Start the API from `backend/`:

   ```powershell
   uvicorn app.main:app --reload
   ```

4. Install Node.js 20 or newer. In another terminal, configure and start the dashboard:

   ```powershell
   cd frontend
   Copy-Item .env.example .env.local
   npm install
   npm run dev
   ```

   Set `VITE_API_BASE_URL=http://localhost:8000` in `frontend/.env.local`. Copy the Firebase web app values from Firebase Console into the `VITE_FIREBASE_*` variables. These browser config values are public; never put the Admin service-account JSON here.

## ESP32-CAM request

Send one JPEG or PNG frame as `multipart/form-data` to `POST /api/v1/predictions`. Include `X-Device-Key` and the `image` file field. Optional form fields are `device_id`, `latitude`, and `longitude`.

```text
POST https://<render-api>/api/v1/predictions
X-Device-Key: <DEVICE_API_KEY>
Content-Type: multipart/form-data

image=<frame.jpg>
device_id=esp32-cam-01
latitude=13.2039
longitude=74.8438
```

The response contains the detections, bounding boxes, and Cloudinary URL of the annotated JPEG. `GET /api/v1/predictions?limit=50` returns recent records for the dashboard. Maximum upload size is 10 MB.

The dashboard's **Test an image** panel sends the selected frame to `POST /api/v1/predictions/test` with the same `X-Device-Key`. This route returns the annotated image and detections inline without writing to Cloudinary or Firestore. Enter the configured device key into the test panel; it is held only in page memory and is not built into the frontend.

## Deployment

1. Push this project, including `backend/models/best.pt`, to a private GitHub repository connected to Render. Deploy the `skymatrix-api` service from `render.yaml` and set `CLOUDINARY_URL`, `FIREBASE_SERVICE_ACCOUNT_JSON`, and `DEVICE_API_KEY` in Render. `CORS_ORIGINS` is preconfigured for localhost and `skymatrix-hd` Firebase Hosting; add any custom hosting domains to that JSON array. Set `FIRESTORE_DATABASE_ID` to `(default)`.
2. Create a Firebase project and Firestore database. Build and deploy Hosting from the project root:

   ```powershell
   cd frontend
   Copy-Item .env.example .env.production
   # Set VITE_API_BASE_URL to the deployed Render API URL in .env.production
   npm install
   npm run build
   cd ..
   firebase login
   firebase deploy --project <firebase-project-id> --only hosting
   ```

   Add the deployed Firebase Hosting origin to the API's `CORS_ORIGINS` setting.

## Frame volume

At one frame every 10 seconds, a continuously running drone creates up to 8,640 image uploads per day. Check Cloudinary storage and delivery quotas before enabling continuous capture. Set a retention/deletion policy and consider storing only detection-positive frames if the project does not need every empty frame archived.
