# Setup Email Alerts for alidosimbek9@gmail.com

## Current Status
✅ Email address configured: `alidosimbek9@gmail.com`

## Next Steps to Enable Email Alerts

### Option 1: Enable 2-Step Verification (Recommended)

Since App Passwords are not available, you need to enable 2-Step Verification first:

1. **Go to Google Account Security:**
   - Visit: https://myaccount.google.com/security
   - Or: https://myaccount.google.com/signinoptions/two-step-verification

2. **Enable 2-Step Verification:**
   - Click "Get started"
   - Follow the setup process
   - You can use your phone number or authenticator app

3. **After enabling 2-Step Verification:**
   - Go back to: https://myaccount.google.com/apppasswords
   - You should now be able to create App Passwords

4. **Create App Password:**
   - Select "Mail" as the app
   - Select "Other (Custom name)" as device
   - Enter "Data Platform Alerts"
   - Click "Generate"
   - Copy the 16-character password

5. **Update .env file:**
   ```bash
   ALERT_PASSWORD=xxxx xxxx xxxx xxxx
   ```
   (Remove spaces when adding to .env)

### Option 2: Use "Less Secure App Access" (Not Recommended - Deprecated)

⚠️ **Note:** Google has deprecated this option. It's better to use App Passwords.

### Option 3: Use a Different Email Provider

If you have another email account (Outlook, Yahoo, etc.), you can use that:

**For Outlook/Hotmail:**
```bash
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
ALERT_EMAIL=your-email@outlook.com
ALERT_PASSWORD=your-password
```

**For Yahoo:**
```bash
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
ALERT_EMAIL=your-email@yahoo.com
ALERT_PASSWORD=your-app-password
```

## Testing After Setup

Once you've added your App Password to `.env`, test it:

```bash
python test_email_alerts.py
```

This will send 3 test emails to your inbox.

## Current Configuration

Your `.env` file should have:
```bash
ALERT_EMAIL=alidosimbek9@gmail.com
RECIPIENT_EMAIL=alidosimbek9@gmail.com
ALERT_PASSWORD=your-app-password-here  # ← Add this after creating App Password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

## Quick Setup Checklist

- [x] Email address configured: alidosimbek9@gmail.com
- [ ] Enable 2-Step Verification on Google Account
- [ ] Create App Password for Mail
- [ ] Add App Password to .env file
- [ ] Test with `python test_email_alerts.py`
- [ ] Verify emails received in inbox

## Troubleshooting

**"App passwords not available":**
- Enable 2-Step Verification first
- Wait a few minutes after enabling
- Try accessing App Passwords page again

**"Failed to send email":**
- Verify App Password is correct (no spaces)
- Check 2-Step Verification is enabled
- Make sure SMTP settings are correct

**"Authentication failed":**
- Use App Password, not regular password
- Verify App Password hasn't expired
- Check if account has any security restrictions

## Alternative: Test Without Real Email

If you can't set up email right now, you can still demonstrate the system by:
1. Showing the code that sends emails
2. Showing the HTML email templates
3. Explaining how it works
4. Showing the monitoring system

The email functionality is fully implemented - it just needs the credentials configured.

