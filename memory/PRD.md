# KatyaExim CMS - Product Requirements Document

## Original Problem Statement
Build a custom, zero-dependency CMS Dashboard for KatyaExim (katyaexim.in) that allows admin to log in and update the website content dynamically.

## Architecture
- **Production (Railway)**: Node.js/Express server (`server.js`) serving both static files and CMS API routes
- **Preview Environment**: FastAPI backend (`server.py`) on port 8001 for APIs + Express static server on port 3000 for static files
- **Storage**: File system (fs) - index.html is directly modified when content is saved
- **Auth**: Simple password-based JWT (24h expiry)
- **HTML Parsing**: BeautifulSoup (preview) / Cheerio (production)

## Core Requirements (Static)
1. Admin Panel at `/admin` with professional branded UI
2. Content editing via CMS-identifiable IDs on HTML elements
3. Media Manager for image upload/deletion
4. Password protection (default: `katyaexim2026`)
5. Sidebar navigation: General Info, Products, Gallery, Certificates, Image Manager
6. Live Preview via iframe
7. File system persistence (direct HTML modification)

## User Personas
- **Site Admin**: Business owner managing website content (product descriptions, hero text, gallery, certificates)
- **Visitors**: International textile buyers viewing the public website

## What's Been Implemented (March 30, 2026)
- [x] Admin login page with KatyaExim branding (gold/rose/cream theme)
- [x] JWT-based password authentication
- [x] Sidebar navigation with 5 sections
- [x] General Info panel (Hero: eyebrow, title, tagline; About: title + 3 paragraphs; Contact: address, email)
- [x] Products panel (6 product cards with category, name, description)
- [x] Gallery panel (5 gallery labels + image upload zone)
- [x] Certificates panel (3 cert cards with title, desc, badge + certificate doc upload)
- [x] Image Manager (upload, browse, delete, copy URL)
- [x] Live Preview iframe with refresh
- [x] Save Changes functionality (writes to index.html via BeautifulSoup/Cheerio)
- [x] CMS IDs added to all editable elements in index.html
- [x] Toast notifications for feedback
- [x] Drag-and-drop image upload
- [x] server.js with full CMS routes for Railway deployment

## Testing Status
- Backend: 100% (12/12 tests passed)
- Frontend: 95% (minor timing issue resolved)

## Prioritized Backlog
### P0 (Critical)
- None remaining

### P1 (Important)
- Rich text editor for about/description fields (replace raw HTML input)
- Gallery image replacement (replace gradient placeholders with actual images)
- Certificate document image display in the main site

### P2 (Nice to Have)
- Content versioning/history (keep backup of previous versions)
- Multi-admin support (multiple passwords/users)
- SEO meta tag editing from CMS
- Custom CSS injection from CMS

## Next Tasks
1. Add ability to reorder products
2. Add WYSIWYG editor for text fields
3. Add image crop/resize before upload
4. Deploy to Railway with CMS routes
