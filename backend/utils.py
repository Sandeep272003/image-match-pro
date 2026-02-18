# backend/utils.py
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from deepface import DeepFace
from fpdf import FPDF
from skimage.metrics import structural_similarity as ssim
from skimage.metrics import peak_signal_noise_ratio as psnr
from datetime import datetime
import os

def get_face_similarity(img1_path: str, img2_path: str) -> float:
    try:
        result = DeepFace.verify(
            img1_path, img2_path,
            model_name="Facenet512",
            detector_backend="retinaface",
            enforce_detection=False,
            distance_metric="cosine",
            silent=True
        )
        distance = result.get("distance", 1.0)
        similarity = 1 - distance
        return max(0.0, min(1.0, similarity))
    except Exception as e:
        print(f"Face similarity failed: {e}")
        return 0.0

def get_feature_similarity(img1_path: str, img2_path: str) -> float:
    try:
        img1 = cv2.imread(img1_path, cv2.IMREAD_GRAYSCALE)
        img2 = cv2.imread(img2_path, cv2.IMREAD_GRAYSCALE)
        
        img1 = cv2.resize(img1, (200, 200))  # Very small for speed
        img2 = cv2.resize(img2, (200, 200))
        
        orb = cv2.ORB_create(nfeatures=300)
        kp1, des1 = orb.detectAndCompute(img1, None)
        kp2, des2 = orb.detectAndCompute(img2, None)
        
        if des1 is None or des2 is None:
            return 0.0
        
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = bf.match(des1, des2)
        matches = sorted(matches, key=lambda x: x.distance)
        
        good_matches = [m for m in matches if m.distance < 50]
        similarity = len(good_matches) / max(len(matches), 1)
        return max(0.0, min(1.0, similarity))
    except Exception as e:
        print(f"Feature similarity failed: {e}")
        return 0.0

def get_ssim_psnr(img1_path: str, img2_path: str):
    try:
        img1 = cv2.imread(img1_path)
        img2 = cv2.imread(img2_path)
        img1 = cv2.resize(img1, (200, 200))
        img2 = cv2.resize(img2, (200, 200))
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        
        ssim_score = ssim(gray1, gray2, data_range=gray2.max() - gray2.min())
        psnr_score = psnr(img1, img2)
        return ssim_score, psnr_score
    except Exception as e:
        print(f"SSIM/PSNR failed: {e}")
        return 0.0, 0.0

def advanced_enhance(input_path: str, output_path: str, intensity: float = 0.5):
    try:
        img = cv2.imread(input_path)
        height, width = img.shape[:2]
        
        # Denoise
        denoised = cv2.fastNlMeansDenoisingColored(img, None, int(10 * intensity), int(10 * intensity), 7, 21)
        
        # Contrast enhancement
        lab = cv2.cvtColor(denoised, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0 * intensity, tileGridSize=(8,8))
        l = clahe.apply(l)
        lab = cv2.merge((l, a, b))
        enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        # Sharpen
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]]) * intensity
        sharpened = cv2.filter2D(enhanced, -1, kernel)
        
        # Brightness
        hsv = cv2.cvtColor(sharpened, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        v = cv2.add(v, int(20 * intensity))
        v = np.clip(v, 0, 255)
        hsv = cv2.merge((h, s, v))
        final = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        
        final = cv2.resize(final, (width, height))
        cv2.imwrite(output_path, final, [cv2.IMWRITE_PNG_COMPRESSION, 0])  # High quality
    except Exception as e:
        print(f"Advanced enhance failed: {e}")

def remove_background(input_path: str, output_path: str):
    try:
        img = cv2.imread(input_path)
        height, width = img.shape[:2]
        
        # Detect faces
        try:
            faces = DeepFace.extract_faces(img_path=input_path, detector_backend="retinaface", enforce_detection=False)
        except:
            faces = []
        
        mask = np.zeros(img.shape[:2], np.uint8)
        
        has_person = False
        
        # For each face, mark face and body
        for face in faces:
            coords = face["facial_area"]
            x, y, w, h = coords['x'], coords['y'], coords['w'], coords['h']
            if w <= 0 or h <= 0:
                continue
            
            has_person = True
            
            # Face definite foreground
            cv2.rectangle(mask, (x, y, x+w, y+h), cv2.GC_FGD, -1)
            
            # Body estimation: ellipse for dress shape
            center = (int(x + w/2), int(y + h/2))
            axes = (int(w * 1.5), int(h * 4))
            if axes[0] > 0 and axes[1] > 0:
                cv2.ellipse(mask, center, axes, 0, 0, 360, cv2.GC_PR_FGD, -1)
        
        # If no person detected, fallback to center rect
        if not has_person:
            rect = (width//4, height//4, width//2, height//2)
            bgdModel = np.zeros((1,65), np.float64)
            fgdModel = np.zeros((1,65), np.float64)
            cv2.grabCut(img, mask, rect, bgdModel, fgdModel, 5, cv2.GC_INIT_WITH_RECT)
        else:
            # Dress shape detection using edges
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = cv2.Canny(blurred, 30, 100)
            dilated_edges = cv2.dilate(edges, np.ones((3,3), np.uint8), iterations=1)
            
            # Find contours for dress/body shapes
            contours, _ = cv2.findContours(dilated_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Fill large contours (people/dress)
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area > 5000:
                    cv2.fillPoly(mask, [cnt], cv2.GC_PR_FGD)
            
            # Edges to background
            mask[0:20, :] = cv2.GC_BGD
            mask[:, 0:20] = cv2.GC_BGD
            mask[height-20:height, :] = cv2.GC_BGD
            mask[:, width-20:width] = cv2.GC_BGD
            
            # GrabCut
            bgdModel = np.zeros((1,65), np.float64)
            fgdModel = np.zeros((1,65), np.float64)
            cv2.grabCut(img, mask, None, bgdModel, fgdModel, 8, cv2.GC_INIT_WITH_MASK)
        
        # Final mask
        mask2 = np.where((mask==cv2.GC_BGD)|(mask==cv2.GC_PR_BGD), 0, 1).astype('uint8')
        
        # White background
        result = img.copy()
        result[mask2 == 0] = [255, 255, 255]
        
        cv2.imwrite(output_path, result, [cv2.IMWRITE_PNG_COMPRESSION, 0])
    except Exception as e:
        print(f"Background removal failed: {e}")

def brighten_dark_image(input_path: str, output_path: str, intensity: float = 0.5):
    try:
        img = cv2.imread(input_path)
        height, width = img.shape[:2]
        
        # Denoise
        denoised = cv2.fastNlMeansDenoisingColored(img, None, int(15 * intensity), int(15 * intensity), 10, 30)
        
        # CLAHE
        lab = cv2.cvtColor(denoised, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=4.0 * intensity, tileGridSize=(8,8))
        l = clahe.apply(l)
        lab = cv2.merge((l, a, b))
        bright = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        # Gamma
        avg_brightness = np.mean(cv2.cvtColor(bright, cv2.COLOR_BGR2GRAY))
        gamma = 1.0 + (1 - avg_brightness / 255) * 1.5 * intensity
        inv_gamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
        bright = cv2.LUT(bright, table)
        
        # HSV boost
        hsv = cv2.cvtColor(bright, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        v = np.clip(v.astype(np.uint16) + int(40 * intensity), 0, 255).astype(np.uint8)
        hsv = cv2.merge((h, s, v))
        final = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        
        final = cv2.resize(final, (width, height))
        cv2.imwrite(output_path, final, [cv2.IMWRITE_PNG_COMPRESSION, 0])
    except Exception as e:
        print(f"Brighten failed: {e}")

def denoise_image(input_path: str, output_path: str, intensity: float = 0.5):
    try:
        img = cv2.imread(input_path)
        height, width = img.shape[:2]
        
        denoised = cv2.fastNlMeansDenoisingColored(img, None, int(15 * intensity), int(15 * intensity), 7, 21)
        bilateral = cv2.bilateralFilter(denoised, d=int(9 * intensity), sigmaColor=75, sigmaSpace=75)
        
        bilateral = cv2.resize(bilateral, (width, height))
        cv2.imwrite(output_path, bilateral, [cv2.IMWRITE_PNG_COMPRESSION, 0])
    except Exception as e:
        print(f"Denoise failed: {e}")

def sharpen_image(input_path: str, output_path: str, intensity: float = 0.5):
    try:
        img = cv2.imread(input_path)
        height, width = img.shape[:2]
        
        gaussian = cv2.GaussianBlur(img, (0, 0), 3 * intensity)
        sharpened = cv2.addWeighted(img, 1.5 * intensity, gaussian, -0.5 * intensity, 0)
        
        sharpened = cv2.resize(sharpened, (width, height))
        cv2.imwrite(output_path, sharpened, [cv2.IMWRITE_PNG_COMPRESSION, 0])
    except Exception as e:
        print(f"Sharpen failed: {e}")

def generate_report_image(img1_path, img2_path, result, output_path):
    try:
        width, height = 1400, 900  # Higher resolution
        report = Image.new('RGB', (width, height), color=(250, 250, 250))
        draw = ImageDraw.Draw(report)
        try:
            font_large = ImageFont.truetype("arial.ttf", 60)
            font_med = ImageFont.truetype("arial.ttf", 40)
            font_small = ImageFont.truetype("arial.ttf", 30)
        except:
            font_large = ImageFont.load_default()
            font_med = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        img1 = Image.open(img1_path).resize((400, 400))
        img2 = Image.open(img2_path).resize((400, 400))
        report.paste(img1, (100, 200))
        report.paste(img2, (600, 200))
        
        draw.text((100, 50), "IMAGE MATCH PRO - ADVANCED SIMILARITY REPORT", fill="black", font=font_large)
        draw.text((100, 130), f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", fill="gray", font=font_small)
        
        color = "green" if result['is_same_person'] else "red"
        draw.text((100, 650), f"FINAL SIMILARITY: {result['final_similarity']}%", fill=color, font=font_large)
        draw.text((100, 730), f"FACE MATCH: {result['face_similarity']}%", fill="black", font=font_med)
        verdict = "SAME PERSON" if result['is_same_person'] else "DIFFERENT PERSON"
        draw.text((100, 800), f"VERDICT: {verdict}", fill=color, font=font_large)
        
        report.save(output_path, quality=95, dpi=(300,300))  # High quality
    except Exception as e:
        print(f"Report image failed: {e}")

def generate_report_pdf(report_img_path, result, output_path):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.image(report_img_path, x=10, y=10, w=190)
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 20, f"Image Match Pro Report - {datetime.now().strftime('%Y-%m-%d')}", ln=1, align='C')
        pdf.cell(0, 15, f"Final Similarity: {result['final_similarity']}%", ln=1)
        pdf.cell(0, 15, f"Face Match: {result['face_similarity']}%", ln=1)
        pdf.output(output_path)
    except Exception as e:
        print(f"PDF failed: {e}")

def generate_clean_report_image(orig_path, cleaned_path, result, output_path):
    try:
        width, height = 1400, 900
        report = Image.new('RGB', (width, height), color=(250, 250, 250))
        draw = ImageDraw.Draw(report)
        try:
            font_large = ImageFont.truetype("arial.ttf", 60)
            font_med = ImageFont.truetype("arial.ttf", 40)
            font_small = ImageFont.truetype("arial.ttf", 30)
        except:
            font_large = ImageFont.load_default()
            font_med = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        orig_img = Image.open(orig_path).resize((400, 400))
        cleaned_img = Image.open(cleaned_path).resize((400, 400))
        report.paste(orig_img, (100, 200))
        report.paste(cleaned_img, (600, 200))
        
        draw.text((100, 50), "IMAGE CLEAN PRO - ENHANCEMENT REPORT", fill="black", font=font_large)
        draw.text((100, 130), f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", fill="gray", font=font_small)
        draw.text((100, 650), f"Operation: {result.get('operation', 'Unknown')}", fill="black", font=font_large)
        draw.text((100, 730), "Original (Left) vs Processed (Right)", fill="black", font=font_med)
        
        report.save(output_path, quality=95, dpi=(300,300))
    except Exception as e:
        print(f"Clean report image failed: {e}")

def generate_clean_report_pdf(report_img_path, result, output_path):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.image(report_img_path, x=10, y=10, w=190)
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 20, f"Image Clean Pro Report - {datetime.now().strftime('%Y-%m-%d')}", ln=1, align='C')
        pdf.cell(0, 15, f"Operation: {result.get('operation', 'Unknown')}", ln=1)
        pdf.output(output_path)
    except Exception as e:
        print(f"Clean PDF failed: {e}")