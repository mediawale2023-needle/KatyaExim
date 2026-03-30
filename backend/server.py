import os
import json
import time
import shutil
import secrets
from pathlib import Path
from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from bs4 import BeautifulSoup
import jwt

app = FastAPI(title="KatyaExim CMS API")

# Config
JWT_SECRET = os.environ.get("JWT_SECRET", secrets.token_hex(32))
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "katyaexim2026")
PUBLIC_DIR = Path("/app/public")
INDEX_PATH = PUBLIC_DIR / "index.html"
IMAGES_DIR = PUBLIC_DIR / "images"
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── AUTH ───
def verify_token(request: Request):
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = auth_header[7:]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        if payload.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Forbidden")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.post("/api/admin/login")
async def admin_login(request: Request):
    body = await request.json()
    password = body.get("password", "")
    if not password:
        raise HTTPException(status_code=400, detail="Password is required")
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Incorrect password")
    token = jwt.encode(
        {"role": "admin", "exp": datetime.now(timezone.utc) + timedelta(hours=24)},
        JWT_SECRET,
        algorithm="HS256"
    )
    return {"success": True, "token": token}


@app.get("/api/admin/verify")
async def admin_verify(admin=Depends(verify_token)):
    return {"success": True, "message": "Token is valid"}


# ─── CONTENT ───
def read_html():
    return INDEX_PATH.read_text(encoding="utf-8")

def parse_content():
    html = read_html()
    soup = BeautifulSoup(html, "html.parser")

    content = {
        "hero": {
            "eyebrow": get_inner_html(soup, "cms-hero-eyebrow"),
            "title": get_inner_html(soup, "cms-hero-title"),
            "tagline": get_inner_html(soup, "cms-hero-tagline"),
        },
        "about": {
            "title": get_inner_html(soup, "cms-about-title"),
            "p1": get_inner_html(soup, "cms-about-p1"),
            "p2": get_inner_html(soup, "cms-about-p2"),
            "p3": get_inner_html(soup, "cms-about-p3"),
        },
        "products": [],
        "gallery": [],
        "certificates": [],
        "contact": {
            "address": get_inner_html(soup, "cms-contact-address"),
            "email": get_inner_html(soup, "cms-contact-email"),
        },
    }

    for i in range(6):
        content["products"].append({
            "cat": get_inner_html(soup, f"cms-product-{i}-cat"),
            "name": get_inner_html(soup, f"cms-product-{i}-name"),
            "desc": get_inner_html(soup, f"cms-product-{i}-desc"),
        })

    for i in range(5):
        content["gallery"].append({
            "label": get_inner_html(soup, f"cms-gallery-{i}-label"),
        })

    for i in range(3):
        content["certificates"].append({
            "title": get_inner_html(soup, f"cms-cert-{i}-title"),
            "desc": get_inner_html(soup, f"cms-cert-{i}-desc"),
            "badge": get_inner_html(soup, f"cms-cert-{i}-badge"),
        })

    return content


def get_inner_html(soup, element_id):
    el = soup.find(id=element_id)
    if el is None:
        return ""
    return "".join(str(c) for c in el.children).strip()


def save_content(content):
    html = read_html()
    soup = BeautifulSoup(html, "html.parser")

    def set_inner(el_id, value):
        el = soup.find(id=el_id)
        if el and value is not None:
            el.clear()
            el.append(BeautifulSoup(value, "html.parser"))

    if "hero" in content:
        h = content["hero"]
        if "eyebrow" in h: set_inner("cms-hero-eyebrow", h["eyebrow"])
        if "title" in h: set_inner("cms-hero-title", h["title"])
        if "tagline" in h: set_inner("cms-hero-tagline", h["tagline"])

    if "about" in content:
        a = content["about"]
        if "title" in a: set_inner("cms-about-title", a["title"])
        if "p1" in a: set_inner("cms-about-p1", a["p1"])
        if "p2" in a: set_inner("cms-about-p2", a["p2"])
        if "p3" in a: set_inner("cms-about-p3", a["p3"])

    if "products" in content:
        for i, prod in enumerate(content["products"]):
            if "cat" in prod: set_inner(f"cms-product-{i}-cat", prod["cat"])
            if "name" in prod: set_inner(f"cms-product-{i}-name", prod["name"])
            if "desc" in prod: set_inner(f"cms-product-{i}-desc", prod["desc"])

    if "gallery" in content:
        for i, item in enumerate(content["gallery"]):
            if "label" in item: set_inner(f"cms-gallery-{i}-label", item["label"])

    if "certificates" in content:
        for i, cert in enumerate(content["certificates"]):
            if "title" in cert: set_inner(f"cms-cert-{i}-title", cert["title"])
            if "desc" in cert: set_inner(f"cms-cert-{i}-desc", cert["desc"])
            if "badge" in cert: set_inner(f"cms-cert-{i}-badge", cert["badge"])

    if "contact" in content:
        c = content["contact"]
        if "address" in c: set_inner("cms-contact-address", c["address"])
        if "email" in c:
            el = soup.find(id="cms-contact-email")
            if el:
                el.clear()
                el.append(BeautifulSoup(c["email"], "html.parser"))
                plain_email = BeautifulSoup(c["email"], "html.parser").get_text().strip()
                el["href"] = f"mailto:{plain_email}"

    INDEX_PATH.write_text(str(soup), encoding="utf-8")


@app.get("/api/admin/content")
async def get_content(admin=Depends(verify_token)):
    try:
        content = parse_content()
        return {"success": True, "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/content")
async def update_content(request: Request, admin=Depends(verify_token)):
    try:
        body = await request.json()
        content = body.get("content")
        if not content:
            raise HTTPException(status_code=400, detail="Content is required")
        save_content(content)
        return {"success": True, "message": "Content saved successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── IMAGES ───
@app.get("/api/admin/images")
async def list_images(admin=Depends(verify_token)):
    try:
        IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        images = []
        for f in IMAGES_DIR.iterdir():
            if f.suffix.lower() in ALLOWED_EXTENSIONS:
                stat = f.stat()
                images.append({
                    "name": f.name,
                    "url": f"/images/{f.name}",
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                })
        images.sort(key=lambda x: x["modified"], reverse=True)
        return {"success": True, "images": images}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/upload")
async def upload_image(image: UploadFile = File(...), admin=Depends(verify_token)):
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    ext = Path(image.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only image files (jpg, png, gif, webp, svg) are allowed")

    contents = await image.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 5MB.")

    # Generate safe filename
    stem = Path(image.filename).stem
    safe_stem = "".join(c if c.isalnum() or c in "_-" else "_" for c in stem)[:50]
    unique = hex(int(time.time()))[2:]
    filename = f"{safe_stem}_{unique}{ext}"

    filepath = IMAGES_DIR / filename
    filepath.write_bytes(contents)

    return {
        "success": True,
        "image": {
            "name": filename,
            "url": f"/images/{filename}",
            "size": len(contents),
        }
    }


@app.delete("/api/admin/images/{name}")
async def delete_image(name: str, admin=Depends(verify_token)):
    if ".." in name or "/" in name:
        raise HTTPException(status_code=400, detail="Invalid filename")
    if name == "logo.png":
        raise HTTPException(status_code=403, detail="Cannot delete the site logo")

    filepath = IMAGES_DIR / name
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Image not found")

    filepath.unlink()
    return {"success": True, "message": "Image deleted"}


@app.post("/api/admin/replace-image")
async def replace_image(request: Request, admin=Depends(verify_token)):
    try:
        body = await request.json()
        selector = body.get("selector")
        new_src = body.get("newSrc")
        if not selector or not new_src:
            raise HTTPException(status_code=400, detail="selector and newSrc are required")

        html = read_html()
        soup = BeautifulSoup(html, "html.parser")
        el = soup.select_one(selector)
        if not el:
            raise HTTPException(status_code=404, detail="Element not found")

        el["src"] = new_src
        INDEX_PATH.write_text(str(soup), encoding="utf-8")
        return {"success": True, "message": "Image replaced"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Contact form proxy (matches the Node.js endpoint)
@app.post("/api/contact")
async def contact_form(request: Request):
    body = await request.json()
    name = body.get("name", "")
    email = body.get("email", "")
    message = body.get("message", "")
    if not name or not email or not message:
        raise HTTPException(status_code=400, detail="Name, email and message are required.")
    print(f"Contact form submission: {name} ({email})")
    return {"success": True}
