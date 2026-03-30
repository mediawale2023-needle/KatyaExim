# Test Credentials - KatyaExim CMS

## Admin Access
- **URL**: `/admin`
- **Password**: `katyaexim2026`
- **Auth Type**: Simple password-based JWT authentication

## API Endpoints
- **Login**: `POST /api/admin/login` with `{"password": "katyaexim2026"}`
- **Verify**: `GET /api/admin/verify` (Bearer token)
- **Content Read**: `GET /api/admin/content` (Bearer token)
- **Content Save**: `POST /api/admin/content` (Bearer token)
- **Image List**: `GET /api/admin/images` (Bearer token)
- **Image Upload**: `POST /api/admin/upload` (Bearer token, multipart form)
- **Image Delete**: `DELETE /api/admin/images/:name` (Bearer token)
- **Replace Image**: `POST /api/admin/replace-image` (Bearer token)
- **Contact Form**: `POST /api/contact`
