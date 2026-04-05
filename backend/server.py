import os
import re
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


# ─── CONTENT HELPERS ───
def read_html():
    return INDEX_PATH.read_text(encoding="utf-8")

def get_inner_html(soup, element_id):
    el = soup.find(id=element_id)
    if el is None:
        return ""
    return "".join(str(c) for c in el.children).strip()

def get_bg_image(el):
    """Extract background-image URL from a BeautifulSoup element's style."""
    if el is None:
        return ""
    style = el.get("style", "")
    m = re.search(r"url\(['\"]?([^'\")\s]+)['\"]?\)", style)
    return m.group(1) if m else ""


# ─── PARSE CONTENT ───
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
        },
        "products": [],
        "gallery": [],
        "certificates": [],
        "contact": {
            "address": get_inner_html(soup, "cms-contact-address"),
            "email": get_inner_html(soup, "cms-contact-email"),
        },
    }

    # About paragraphs – detect dynamically (p1, p2, p3, ...)
    i = 1
    while soup.find(id=f"cms-about-p{i}"):
        content["about"][f"p{i}"] = get_inner_html(soup, f"cms-about-p{i}")
        i += 1

    # Products – detect dynamically
    i = 0
    while soup.find(id=f"cms-product-{i}"):
        card = soup.find(id=f"cms-product-{i}")
        bg = card.find(class_=lambda c: c and "product-bg" in c.split()
                       and any(x.startswith("product-bg-") for x in c.split()))
        content["products"].append({
            "cat": get_inner_html(soup, f"cms-product-{i}-cat"),
            "name": get_inner_html(soup, f"cms-product-{i}-name"),
            "desc": get_inner_html(soup, f"cms-product-{i}-desc"),
            "image": get_bg_image(bg),
        })
        i += 1

    # Gallery – detect dynamically
    i = 0
    while soup.find(id=f"cms-gallery-{i}"):
        item = soup.find(id=f"cms-gallery-{i}")
        tile = item.find(class_=lambda c: c and "gallery-tile" in c.split()
                          and any(x.startswith("gallery-tile-") for x in c.split()))
        content["gallery"].append({
            "label": get_inner_html(soup, f"cms-gallery-{i}-label"),
            "image": get_bg_image(tile),
        })
        i += 1

    # Certificates – detect dynamically
    i = 0
    while soup.find(id=f"cms-cert-{i}"):
        content["certificates"].append({
            "title": get_inner_html(soup, f"cms-cert-{i}-title"),
            "desc": get_inner_html(soup, f"cms-cert-{i}-desc"),
            "badge": get_inner_html(soup, f"cms-cert-{i}-badge"),
        })
        i += 1

    return content


# ─── SAVE CONTENT ───
BG_CLASSES = ["product-bg-1","product-bg-2","product-bg-3","product-bg-4","product-bg-5","product-bg-6"]
PRODUCT_ICONS = ["🛁","🛏️","🍽️","🧣","✨","🎨"]
GALLERY_CLASSES = ["gallery-tile-1","gallery-tile-2","gallery-tile-3","gallery-tile-4","gallery-tile-5"]
CERT_ICONS = ["🏛️","📦","✅","🏆","📋"]
REVEAL_DELAYS = ["","reveal-delay-1","reveal-delay-2","reveal-delay-3"]

def img_style(url):
    if not url:
        return ""
    return f' style="background-image:url(\'{url}\');background-size:cover;background-position:center"'

def make_product_html(i, prod):
    bg_cls = BG_CLASSES[i % len(BG_CLASSES)]
    icon = PRODUCT_ICONS[i % len(PRODUCT_ICONS)]
    return (
        f'<div class="product-card" id="cms-product-{i}">'
        f'<div class="product-bg {bg_cls}"{img_style(prod.get("image",""))}></div>'
        f'<div class="product-pattern"></div>'
        f'<div class="product-overlay"></div>'
        f'<div class="product-icon">{icon}</div>'
        f'<div class="product-info">'
        f'<p class="product-cat" id="cms-product-{i}-cat">{prod.get("cat","")}</p>'
        f'<h3 class="product-name" id="cms-product-{i}-name">{prod.get("name","")}</h3>'
        f'<p class="product-desc" id="cms-product-{i}-desc">{prod.get("desc","")}</p>'
        f'</div></div>'
    )

def make_gallery_html(i, item):
    tile_cls = GALLERY_CLASSES[i % len(GALLERY_CLASSES)]
    return (
        f'<div class="gallery-item" id="cms-gallery-{i}">'
        f'<div class="gallery-tile {tile_cls}"{img_style(item.get("image",""))}>'
        f'<div class="gallery-tile-label" id="cms-gallery-{i}-label">{item.get("label","")}</div>'
        f'</div>'
        f'<div class="gallery-overlay"><span>{item.get("label","")}</span></div>'
        f'</div>'
    )

def make_cert_html(i, cert):
    icon = CERT_ICONS[i % len(CERT_ICONS)]
    delay = REVEAL_DELAYS[min(i, len(REVEAL_DELAYS)-1)]
    delay_cls = f" {delay}" if delay else ""
    return (
        f'<div class="cert-card reveal{delay_cls}" id="cms-cert-{i}">'
        f'<div class="cert-icon">{icon}</div>'
        f'<h3 id="cms-cert-{i}-title">{cert.get("title","")}</h3>'
        f'<p id="cms-cert-{i}-desc">{cert.get("desc","")}</p>'
        f'<div class="cert-badge" id="cms-cert-{i}-badge">{cert.get("badge","")}</div>'
        f'</div>'
    )

def make_about_para_html(i, text):
    delay = REVEAL_DELAYS[min(i+1, len(REVEAL_DELAYS)-1)]
    return f'<p class="reveal {delay}" id="cms-about-p{i+1}">{text}</p>'

def rebuild_grid(soup, grid_id, items, make_fn):
    """Rebuild a grid element's children from items list."""
    grid = soup.find(id=grid_id)
    if not grid:
        return
    for child in list(grid.children):
        if hasattr(child, 'decompose'):
            child.decompose()
    for i, item in enumerate(items):
        html = make_fn(i, item)
        grid.append(BeautifulSoup(html, "html.parser"))

def save_content(content):
    html = read_html()
    soup = BeautifulSoup(html, "html.parser")

    def set_inner(el_id, value):
        el = soup.find(id=el_id)
        if el and value is not None:
            el.clear()
            el.append(BeautifulSoup(value, "html.parser"))

    # Hero
    if "hero" in content:
        h = content["hero"]
        if "eyebrow" in h: set_inner("cms-hero-eyebrow", h["eyebrow"])
        if "title" in h: set_inner("cms-hero-title", h["title"])
        if "tagline" in h: set_inner("cms-hero-tagline", h["tagline"])

    # About title
    if "about" in content:
        a = content["about"]
        if "title" in a: set_inner("cms-about-title", a["title"])

        # About paragraphs – rebuild dynamically
        about_div = soup.find(id="cms-about-content")
        if about_div:
            # Remove existing p-N elements
            for el in list(about_div.find_all(id=lambda x: x and x.startswith("cms-about-p"))):
                el.decompose()
            # Find insertion point: after cms-about-title
            title_el = about_div.find(id="cms-about-title")
            para_idx = 1
            while a.get(f"p{para_idx}") is not None:
                para_html = make_about_para_html(para_idx - 1, a[f"p{para_idx}"])
                parsed = BeautifulSoup(para_html, "html.parser")
                if title_el:
                    title_el.insert_after(parsed)
                    title_el = about_div.find(id=f"cms-about-p{para_idx}")
                else:
                    about_div.append(parsed)
                para_idx += 1

    # Products – rebuild entire grid
    if "products" in content and content["products"]:
        rebuild_grid(soup, "cms-products-grid", content["products"], make_product_html)

    # Gallery – rebuild entire grid
    if "gallery" in content and content["gallery"]:
        rebuild_grid(soup, "cms-gallery-grid", content["gallery"], make_gallery_html)

    # Certificates – rebuild entire grid
    if "certificates" in content and content["certificates"]:
        rebuild_grid(soup, "cms-cert-grid", content["certificates"], make_cert_html)

    # Contact
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


# Contact form proxy
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
