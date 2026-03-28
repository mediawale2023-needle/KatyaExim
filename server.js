const express = require('express');
const nodemailer = require('nodemailer');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'public')));

// Contact form endpoint
app.post('/api/contact', async (req, res) => {
  const { name, email, phone, company, subject, message } = req.body;

  if (!name || !email || !message) {
    return res.status(400).json({ success: false, error: 'Name, email and message are required.' });
  }

  // If SMTP credentials are configured, send email
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
            <h2 style="color: #1a1611; border-bottom: 2px solid #af9f96; padding-bottom: 12px;">New Enquiry – KATYA EXIM</h2>
            <table style="width:100%; border-collapse: collapse; margin-top: 20px;">
              <tr><td style="padding: 8px 0; color: #666; width: 120px;"><strong>Name:</strong></td><td style="padding: 8px 0; color: #1a1611;">${name}</td></tr>
              <tr><td style="padding: 8px 0; color: #666;"><strong>Email:</strong></td><td style="padding: 8px 0; color: #1a1611;">${email}</td></tr>
              <tr><td style="padding: 8px 0; color: #666;"><strong>Phone:</strong></td><td style="padding: 8px 0; color: #1a1611;">${phone || '—'}</td></tr>
              <tr><td style="padding: 8px 0; color: #666;"><strong>Company:</strong></td><td style="padding: 8px 0; color: #1a1611;">${company || '—'}</td></tr>
              <tr><td style="padding: 8px 0; color: #666;"><strong>Subject:</strong></td><td style="padding: 8px 0; color: #1a1611;">${subject || '—'}</td></tr>
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
      // Don't fail the request — still return success to the user
    }
  } else {
    console.log('Contact form submission (no SMTP configured):', { name, email, subject });
  }

  return res.json({ success: true });
});

// SPA fallback — serve index.html for all unmatched routes
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`KATYA EXIM website running on port ${PORT}`);
});
