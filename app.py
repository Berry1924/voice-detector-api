import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib  # <--- CHANGED FROM PICKLE
import numpy as np
import librosa
import base64
import os
import uuid
import warnings

# --- 1. SETUP & CONFIG ---
warnings.filterwarnings("ignore")
app = FastAPI()

# --- 2. LOAD YOUR MODEL (Using Joblib) ---
# We use the path you found: model/voice_model.pkl
MODEL_PATH = "model/voice_model.pkl"

try:
    # Joblib loads directly from the file path, not 'with open(...)'
    model = joblib.load(MODEL_PATH)
    print(f"✅ Model loaded successfully from {MODEL_PATH}")
    
    # Check features expected (Debugging)
    if hasattr(model, "n_features_in_"):
        print(f"ℹ️ Model expects {model.n_features_in_} features.")
        
except FileNotFoundError:
    print(f"❌ CRITICAL ERROR: Could not find model at '{MODEL_PATH}'.")
    model = None
except Exception as e:
    print(f"❌ ERROR LOADING MODEL: {e}")
    print("👉 If this fails, your model file might be corrupted or in a completely different format (like .h5).")
    model = None

# --- 3. DEFINE INPUT FORMAT ---
class VoiceData(BaseModel):
    language: str
    audioFormat: str
    audioBase64: str

# --- 4. FEATURE EXTRACTION ---
def extract_features_from_file(file_path):
    try:
        y, sr = librosa.load(file_path, duration=30)
        
        # Extract 20 MFCCs (Mean)
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20)
        mfccs_mean = np.mean(mfccs.T, axis=0)
        
        # Extract Zero Crossing Rate (Mean)
        zcr = librosa.feature.zero_crossing_rate(y)
        zcr_mean = np.mean(zcr.T, axis=0)
        
        # Combine to get 21 Features
        features = np.hstack([mfccs_mean, zcr_mean]) 
        
        return features
    except Exception as e:
        print(f"❌ Feature extraction error: {e}")
        return None

# --- 5. THE API ENDPOINT ---
@app.post("/api/voice-detection")
async def predict_voice(data: VoiceData):
    if not model:
        raise HTTPException(status_code=500, detail="Model file failed to load.")

    temp_filename = f"temp_{uuid.uuid4()}.mp3"
    
    try:
        # A. Decode Base64
        b64_string = data.audioBase64
        if "," in b64_string:
            b64_string = b64_string.split(",")[1]
            
        decoded_audio = base64.b64decode(b64_string)
        with open(temp_filename, "wb") as f:
            f.write(decoded_audio)

        # B. Extract Features
        features = extract_features_from_file(temp_filename)
        if features is None:
            raise HTTPException(status_code=400, detail="Could not extract features from audio.")

        # C. Reshape & Check
        features_reshaped = features.reshape(1, -1)
        
        if hasattr(model, "n_features_in_"):
            expected = model.n_features_in_
            if features_reshaped.shape[1] != expected:
                msg = f"Shape Mismatch: Model expects {expected}, got {features_reshaped.shape[1]}."
                print(f"❌ {msg}")
                # Attempt fallback if mismatch is small (optional, but safer to error out)
                raise HTTPException(status_code=500, detail=msg)

        # D. Predict
        prediction = model.predict(features_reshaped)[0]
        
        # Get confidence
        confidence = 0.0
        if hasattr(model, "predict_proba"):
            probs = model.predict_proba(features_reshaped)
            confidence = float(np.max(probs)) * 100

        result_label = "AI Generated" if prediction == 1 else "Human"
        
        return {
            "status": "success",
            "classification": str(prediction),
            "label": result_label,
            "confidence": f"{confidence:.2f}%"
        }

    except Exception as e:
        print(f"Server Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
