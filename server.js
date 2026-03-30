const express = require('express');
const nodemailer = require('nodemailer');
const path = require('path');
const fs = require('fs');
const multer = require('multer');
const jwt = require('jsonwebtoken');
const crypto = require('crypto');
const { load } = require('cheerio');

const app = express();
const PORT = process.env.PORT || 3000;

const JWT_SECRET = process.env.JWT_SECRET || crypto.randomBytes(32).toString('hex');
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || 'katyaexim2026';
const INDEX_PATH = path.join(__dirname, 'public', 'index.html');
const IMAGES_DIR = path.join(__dirname, 'public', 'images');

// Ensure images directory exists
if (!fs.existsSync(IMAGES_DIR)) {
  fs.mkdirSync(IMAGES_DIR, { recursive: true });
}

// Multer config for image uploads (5MB limit)
const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, IMAGES_DIR),
  filename: (req, file, cb) => {
    const ext = path.extname(file.originalname).toLowerCase();
    const name = file.originalname
      .replace(ext, '')
      .replace(/[^a-zA-Z0-9_-]/g, '_')
      .substring(0, 50);
    const unique = Date.now().toString(36);
    cb(null, `${name}_${unique}${ext}`);
  }
});
const upload = multer({
  storage,
  limits: { fileSize: 5 * 1024 * 1024 },
  fileFilter: (req, file, cb) => {
    const allowed = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'];
    const ext = path.extname(file.originalname).toLowerCase();
    if (allowed.includes(ext)) cb(null, true);
    else cb(new Error('Only image files (jpg, png, gif, webp, svg) are allowed'));
  }
});

// Middleware
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Auth middleware
function authMiddleware(req, res, next) {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'Unauthorized' });
  }
  try {
    const token = authHeader.split(' ')[1];
    const decoded = jwt.verify(token, JWT_SECRET);
    if (decoded.role !== 'admin') {
      return res.status(403).json({ error: 'Forbidden' });
    }
    req.admin = decoded;
    next();
  } catch (err) {
    return res.status(401).json({ error: 'Invalid or expired token' });
  }
}

// ─── AUTH ROUTES ───
app.post('/api/admin/login', (req, res) => {
  const { password } = req.body;
  if (!password) {
    return res.status(400).json({ error: 'Password is required' });
  }
  if (password !== ADMIN_PASSWORD) {
    return res.status(401).json({ error: 'Incorrect password' });
  }
  const token = jwt.sign({ role: 'admin' }, JWT_SECRET, { expiresIn: '24h' });
  return res.json({ success: true, token });
});

app.get('/api/admin/verify', authMiddleware, (req, res) => {
  res.json({ success: true, message: 'Token is valid' });
});

// ─── CONTENT ROUTES ───

// Helper: read and parse index.html with cheerio
function readContent() {
  const html = fs.readFileSync(INDEX_PATH, 'utf-8');
  const $ = load(html);

  const content = {
    hero: {
      eyebrow: $('#cms-hero-eyebrow').html() || '',
      title: $('#cms-hero-title').html() || '',
      tagline: $('#cms-hero-tagline').html() || '',
    },
    about: {
      title: $('#cms-about-title').html() || '',
      p1: $('#cms-about-p1').html() || '',
      p2: $('#cms-about-p2').html() || '',
      p3: $('#cms-about-p3').html() || '',
    },
    products: [],
    gallery: [],
    certificates: [],
    contact: {
      address: $('#cms-contact-address').html() || '',
      email: $('#cms-contact-email').html() || '',
    }
  };

  for (let i = 0; i < 6; i++) {
    content.products.push({
      cat: $(`#cms-product-${i}-cat`).html() || '',
      name: $(`#cms-product-${i}-name`).html() || '',
      desc: $(`#cms-product-${i}-desc`).html() || '',
    });
  }

  for (let i = 0; i < 5; i++) {
    content.gallery.push({
      label: $(`#cms-gallery-${i}-label`).html() || '',
    });
  }

  for (let i = 0; i < 3; i++) {
    content.certificates.push({
      title: $(`#cms-cert-${i}-title`).html() || '',
      desc: $(`#cms-cert-${i}-desc`).html() || '',
      badge: $(`#cms-cert-${i}-badge`).html() || '',
    });
  }

  return content;
}

// Helper: save content back to index.html
function saveContent(content) {
  const html = fs.readFileSync(INDEX_PATH, 'utf-8');
  const $ = load(html);

  if (content.hero) {
    if (content.hero.eyebrow !== undefined) $('#cms-hero-eyebrow').html(content.hero.eyebrow);
    if (content.hero.title !== undefined) $('#cms-hero-title').html(content.hero.title);
    if (content.hero.tagline !== undefined) $('#cms-hero-tagline').html(content.hero.tagline);
  }

  if (content.about) {
    if (content.about.title !== undefined) $('#cms-about-title').html(content.about.title);
    if (content.about.p1 !== undefined) $('#cms-about-p1').html(content.about.p1);
    if (content.about.p2 !== undefined) $('#cms-about-p2').html(content.about.p2);
    if (content.about.p3 !== undefined) $('#cms-about-p3').html(content.about.p3);
  }

  if (content.products) {
    content.products.forEach((prod, i) => {
      if (prod.cat !== undefined) $(`#cms-product-${i}-cat`).html(prod.cat);
      if (prod.name !== undefined) $(`#cms-product-${i}-name`).html(prod.name);
      if (prod.desc !== undefined) $(`#cms-product-${i}-desc`).html(prod.desc);
    });
  }

  if (content.gallery) {
    content.gallery.forEach((item, i) => {
      if (item.label !== undefined) $(`#cms-gallery-${i}-label`).html(item.label);
    });
  }

  if (content.certificates) {
    content.certificates.forEach((cert, i) => {
      if (cert.title !== undefined) $(`#cms-cert-${i}-title`).html(cert.title);
      if (cert.desc !== undefined) $(`#cms-cert-${i}-desc`).html(cert.desc);
      if (cert.badge !== undefined) $(`#cms-cert-${i}-badge`).html(cert.badge);
    });
  }

  if (content.contact) {
    if (content.contact.address !== undefined) $('#cms-contact-address').html(content.contact.address);
    if (content.contact.email !== undefined) {
      $('#cms-contact-email').html(content.contact.email);
      $('#cms-contact-email').attr('href', `mailto:${content.contact.email.replace(/<[^>]*>/g, '').trim()}`);
    }
  }

  fs.writeFileSync(INDEX_PATH, $.html());
}

app.get('/api/admin/content', authMiddleware, (req, res) => {
  try {
    const content = readContent();
    res.json({ success: true, content });
  } catch (err) {
    console.error('Error reading content:', err.message);
    res.status(500).json({ error: 'Failed to read content' });
  }
});

app.post('/api/admin/content', authMiddleware, (req, res) => {
  try {
    const { content } = req.body;
    if (!content) {
      return res.status(400).json({ error: 'Content is required' });
    }
    saveContent(content);
    res.json({ success: true, message: 'Content saved successfully' });
  } catch (err) {
    console.error('Error saving content:', err.message);
    res.status(500).json({ error: 'Failed to save content' });
  }
});

// ─── IMAGE ROUTES ───
app.get('/api/admin/images', authMiddleware, (req, res) => {
  try {
    const files = fs.readdirSync(IMAGES_DIR)
      .filter(f => /\.(jpg|jpeg|png|gif|webp|svg)$/i.test(f))
      .map(f => {
        const stat = fs.statSync(path.join(IMAGES_DIR, f));
        return {
          name: f,
          url: `/images/${f}`,
          size: stat.size,
          modified: stat.mtime,
        };
      })
      .sort((a, b) => new Date(b.modified) - new Date(a.modified));
    res.json({ success: true, images: files });
  } catch (err) {
    console.error('Error listing images:', err.message);
    res.status(500).json({ error: 'Failed to list images' });
  }
});

app.post('/api/admin/upload', authMiddleware, upload.single('image'), (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: 'No image file provided' });
  }
  res.json({
    success: true,
    image: {
      name: req.file.filename,
      url: `/images/${req.file.filename}`,
      size: req.file.size,
    }
  });
});

app.delete('/api/admin/images/:name', authMiddleware, (req, res) => {
  const name = req.params.name;
  if (name.includes('..') || name.includes('/')) {
    return res.status(400).json({ error: 'Invalid filename' });
  }
  const filePath = path.join(IMAGES_DIR, name);
  if (!fs.existsSync(filePath)) {
    return res.status(404).json({ error: 'Image not found' });
  }
  // Don't allow deleting logo.png
  if (name === 'logo.png') {
    return res.status(403).json({ error: 'Cannot delete the site logo' });
  }
  try {
    fs.unlinkSync(filePath);
    res.json({ success: true, message: 'Image deleted' });
  } catch (err) {
    console.error('Error deleting image:', err.message);
    res.status(500).json({ error: 'Failed to delete image' });
  }
});

// Replace image in HTML (update src attribute)
app.post('/api/admin/replace-image', authMiddleware, (req, res) => {
  try {
    const { selector, newSrc } = req.body;
    if (!selector || !newSrc) {
      return res.status(400).json({ error: 'selector and newSrc are required' });
    }
    const html = fs.readFileSync(INDEX_PATH, 'utf-8');
    const $ = load(html);
    const el = $(selector);
    if (el.length === 0) {
      return res.status(404).json({ error: 'Element not found' });
    }
    el.attr('src', newSrc);
    fs.writeFileSync(INDEX_PATH, $.html());
    res.json({ success: true, message: 'Image replaced' });
  } catch (err) {
    console.error('Error replacing image:', err.message);
    res.status(500).json({ error: 'Failed to replace image' });
  }
});

// ─── CONTACT FORM ───
app.post('/api/contact', async (req, res) => {
  const { name, email, phone, company, subject, message } = req.body;

  if (!name || !email || !message) {
    return res.status(400).json({ success: false, error: 'Name, email and message are required.' });
  }

  if (process.env.SMTP_HOST && process.env.SMTP_USER && process.env.SMTP_PASS) {
    try {
      const transporter = nodemailer.createTransport({
        host: process.env.SMTP_HOST,
        port: parseInt(process.env.SMTP_PORT || '587'),
        secure: process.env.SMTP_SECURE === 'true',
        auth: {
          user: process.env.SMTP_USER,
          pass: process.env.SMTP_PASS,
        },
      });

      await transporter.sendMail({
        from: `"${name}" <${process.env.SMTP_USER}>`,
        to: process.env.CONTACT_EMAIL || 'katyayaniexim@gmail.com',
        replyTo: email,
        subject: subject || `New Enquiry from ${name}`,
        html: `
          <div style="font-family: Georgia, serif; max-width: 600px; margin: 0 auto; padding: 32px; background: #f5f0eb;">
            <h2 style="color: #1a1611; border-bottom: 2px solid #af9f96; padding-bottom: 12px;">New Enquiry - KATYA EXIM</h2>
            <table style="width:100%; border-collapse: collapse; margin-top: 20px;">
              <tr><td style="padding: 8px 0; color: #666; width: 120px;"><strong>Name:</strong></td><td style="padding: 8px 0; color: #1a1611;">${name}</td></tr>
              <tr><td style="padding: 8px 0; color: #666;"><strong>Email:</strong></td><td style="padding: 8px 0; color: #1a1611;">${email}</td></tr>
              <tr><td style="padding: 8px 0; color: #666;"><strong>Phone:</strong></td><td style="padding: 8px 0; color: #1a1611;">${phone || '-'}</td></tr>
              <tr><td style="padding: 8px 0; color: #666;"><strong>Company:</strong></td><td style="padding: 8px 0; color: #1a1611;">${company || '-'}</td></tr>
              <tr><td style="padding: 8px 0; color: #666;"><strong>Subject:</strong></td><td style="padding: 8px 0; color: #1a1611;">${subject || '-'}</td></tr>
            </table>
            <div style="margin-top: 20px; padding: 20px; background: white; border-left: 3px solid #af9f96; border-radius: 4px;">
              <strong style="color: #666;">Message:</strong>
              <p style="color: #1a1611; margin-top: 8px; line-height: 1.7;">${message}</p>
            </div>
          </div>
        `,
      });
    } catch (err) {
      console.error('Email error:', err.message);
    }
  } else {
    console.log('Contact form submission (no SMTP configured):', { name, email, subject });
  }

  return res.json({ success: true });
});

// Serve static files
app.use(express.static(path.join(__dirname, 'public')));

// Admin page route
app.get('/admin', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'admin.html'));
});

// SPA fallback
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Error handling for multer
app.use((err, req, res, next) => {
  if (err instanceof multer.MulterError) {
    if (err.code === 'LIMIT_FILE_SIZE') {
      return res.status(400).json({ error: 'File too large. Maximum size is 5MB.' });
    }
    return res.status(400).json({ error: err.message });
  }
  if (err) {
    return res.status(400).json({ error: err.message });
  }
  next();
});

app.listen(PORT, () => {
  console.log(`KATYA EXIM website running on port ${PORT}`);
  console.log(`CMS Admin: http://localhost:${PORT}/admin`);
});
