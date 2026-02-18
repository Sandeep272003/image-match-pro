# backend/main.py
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os
import uuid
from datetime import datetime

# Import all functions from utils
from utils import (
    get_face_similarity,
    get_feature_similarity,
    get_ssim_psnr,
    advanced_enhance,
    remove_background,
    brighten_dark_image,
    denoise_image,
    sharpen_image,
    generate_report_image,
    generate_report_pdf,
    generate_clean_report_image,
    generate_clean_report_pdf
)

# Import database functions
from database import init_db, save_entry, get_history, get_comparison_result, get_clean_result

# Create FastAPI app
app = FastAPI(title="Image Match Pro - AI Image Comparison & Cleaning Tool")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create required directories
directories = ["uploads", "diffs", "cleaned", "reports"]
for directory in directories:
    Path(directory).mkdir(exist_ok=True)

# Mount static folders
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/diffs", StaticFiles(directory="diffs"), name="diffs")
app.mount("/cleaned", StaticFiles(directory="cleaned"), name="cleaned")
app.mount("/reports", StaticFiles(directory="reports"), name="reports")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()
    print("Database initialized. No torchvision/CLIP used - fully stable!")

@app.get("/")
async def root():
    return {"message": "Image Match Pro API is running (torchvision-free)!",
            "timestamp": datetime.now().isoformat()}

# COMPARISON ENDPOINT
@app.post("/api/compare")
async def compare_images(image1: UploadFile = File(...), image2: UploadFile = File(...)):
    if image1.size > 2_000_000 or image2.size > 2_000_000:
        raise HTTPException(status_code=400, detail="Each image must be less than 2MB")

    # Generate unique IDs
    uid = str(uuid.uuid4())[:8]
    img1_path = f"uploads/{uid}_1_{image1.filename}"
    img2_path = f"uploads/{uid}_2_{image2.filename}"

    # Save uploaded files
    contents1 = await image1.read()
    contents2 = await image2.read()
    with open(img1_path, "wb") as f:
        f.write(contents1)
    with open(img2_path, "wb") as f:
        f.write(contents2)

    # Compute advanced similarities (highly optimized for speed)
    face_sim = get_face_similarity(img1_path, img2_path)
    feature_sim = get_feature_similarity(img1_path, img2_path)
    ssim_score, psnr_score = get_ssim_psnr(img1_path, img2_path)

    # Advanced blend
    normalized_psnr = min(psnr_score / 40.0, 1.0)
    final_score = (face_sim * 0.25) + (feature_sim * 0.25) + (ssim_score * 0.25) + (normalized_psnr * 0.25)
    is_same_person = final_score > 0.75

    # Prepare detailed result with all scores
    result = {
        "face_structure_similarity": round(face_sim * 100, 2),
        "feature_similarity": round(feature_sim * 100, 2),
        "ssim_similarity": round(ssim_score * 100, 2),
        "psnr_similarity": round(normalized_psnr * 100, 2),
        "face_match": round(face_sim * 100, 2),
        "final_similarity": round(final_score * 100, 2),
        "is_same_person": bool(is_same_person),
        "image1": f"/uploads/{os.path.basename(img1_path)}",
        "image2": f"/uploads/{os.path.basename(img2_path)}",
        "comparison_id": uid
    }

    # Save to history
    save_entry({
        "type": "comparison",
        "img1_name": image1.filename,
        "img2_name": image2.filename,
        "face_similarity": face_sim,
        "final_score": final_score,
        "is_same_person": int(is_same_person),
        "comparison_id": uid,
        "img1_path": img1_path,
        "img2_path": img2_path
    })

    return JSONResponse(content=result)

# CLEANING ENDPOINT
@app.post("/api/clean")
async def clean_image_endpoint(image: UploadFile = File(...), operation: str = Form(...), intensity: float = Form(0.5)):
    if image.size > 2_000_000:
        raise HTTPException(status_code=400, detail="Image must be less than 2MB")

    uid = str(uuid.uuid4())[:8]
    orig_path = f"uploads/{uid}_{image.filename}"
    cleaned_path = f"cleaned/cleaned_{uid}.png"

    # Save original
    contents = await image.read()
    with open(orig_path, "wb") as f:
        f.write(contents)

    # Perform selected advanced operation with intensity
    if operation == "enhance":
        advanced_enhance(orig_path, cleaned_path, intensity)
    elif operation == "remove_bg":
        remove_background(orig_path, cleaned_path)
    elif operation == "brighten":
        brighten_dark_image(orig_path, cleaned_path, intensity)
    elif operation == "denoise":
        denoise_image(orig_path, cleaned_path, intensity)
    elif operation == "sharpen":
        sharpen_image(orig_path, cleaned_path, intensity)
    else:
        raise HTTPException(status_code=400, detail="Invalid operation")

    result = {
        "original": f"/uploads/{os.path.basename(orig_path)}",
        "cleaned": f"/cleaned/{os.path.basename(cleaned_path)}",
        "operation": operation,
        "clean_id": uid
    }

    # Save to history
    save_entry({
        "type": "cleaning",
        "img1_name": image.filename,
        "clean_id": uid,
        "img1_path": orig_path,
        "cleaned_path": cleaned_path
    })

    return JSONResponse(content=result)

# CLEAN REPORT ENDPOINT
@app.get("/api/clean_report/{clean_id}/{format}")
async def get_clean_report(clean_id: str, format: str = "png"):
    if format not in ["png", "pdf"]:
        raise HTTPException(status_code=400, detail="Format must be 'png' or 'pdf'")

    orig_files = [f for f in os.listdir("uploads") if f.startswith(f"{clean_id}_")]
    cleaned_files = [f for f in os.listdir("cleaned") if f.startswith(f"cleaned_{clean_id}")]
    if not orig_files or not cleaned_files:
        raise HTTPException(status_code=404, detail="Clean result not found")

    orig_path = f"uploads/{orig_files[0]}"
    cleaned_path = f"cleaned/{cleaned_files[0]}"

    report_img_path = f"reports/clean_report_{clean_id}.png"
    report_pdf_path = f"reports/clean_report_{clean_id}.pdf"

    result = {"operation": "Unknown"}

    generate_clean_report_image(orig_path, cleaned_path, result, report_img_path)

    if format == "pdf":
        generate_clean_report_pdf(report_img_path, result, report_pdf_path)
        return FileResponse(report_pdf_path, filename="clean_report.pdf")

    return FileResponse(report_img_path, filename="clean_report.png")

# REPORT ENDPOINT for compare
@app.get("/api/report/{comparison_id}/{format}")
async def get_report(comparison_id: str, format: str = "png"):
    if format not in ["png", "pdf"]:
        raise HTTPException(status_code=400, detail="Format must be 'png' or 'pdf'")

    img1_files = [f for f in os.listdir("uploads") if f.startswith(f"{comparison_id}_1_")]
    img2_files = [f for f in os.listdir("uploads") if f.startswith(f"{comparison_id}_2_")]
    if not img1_files or not img2_files:
        raise HTTPException(status_code=404, detail="Comparison not found")

    img1_path = f"uploads/{img1_files[0]}"
    img2_path = f"uploads/{img2_files[0]}"

    report_img_path = f"reports/report_{comparison_id}.png"
    report_pdf_path = f"reports/report_{comparison_id}.pdf"

    result = get_comparison_result(comparison_id)
    if not result:
        result = {"final_similarity": 0.0, "face_similarity": 0.0, "is_same_person": False}

    generate_report_image(img1_path, img2_path, result, report_img_path)

    if format == "pdf":
        generate_report_pdf(report_img_path, result, report_pdf_path)
        return FileResponse(report_pdf_path, filename="report.pdf")

    return FileResponse(report_img_path, filename="report.png")

# HISTORY ENDPOINT
@app.get("/api/history")
async def get_history_endpoint():
    rows = get_history()
    history_list = []
    for row in rows:
        entry = {
            "id": row[0],
            "time": row[1],
            "type": row[2],
            "img1_name": row[3]
        }
        if row[2] == "comparison":
            entry["img2_name": row[4]]
            entry["score"] = round(row[6] * 100, 1) if row[6] else None
        history_list.append(entry)
    return history_list

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)