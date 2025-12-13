# Database Encryption Setup Guide

## Overview

This guide explains how to set up database encryption for the Data Platform:
- **TLS/SSL in transit**: Encrypts data between client and database
- **AES-256 at rest**: Encrypts data stored on disk

## Requirements

- ✅ TLS/SSL encryption for database connections
- ✅ AES-256 encryption at rest

## Part 1: TLS/SSL Encryption (In Transit)

### Step 1: Generate SSL Certificates

Choose one of these methods:

#### Option A: Using Docker (Recommended for Windows)
```bash
bash scripts/generate_ssl_certs_docker.sh
```

#### Option B: Using OpenSSL directly (Linux/Mac/WSL)
```bash
bash scripts/generate_ssl_certs.sh
```

#### Option C: Using PowerShell (Windows with OpenSSL)
```powershell
.\scripts\generate_ssl_certs.ps1
```

This creates:
- `postgres-ssl/ca.crt` - Certificate Authority certificate
- `postgres-ssl/ca.key` - CA private key
- `postgres-ssl/server.crt` - Server certificate
- `postgres-ssl/server.key` - Server private key

### Step 2: Configure Environment Variables

Create or update your `.env` file:

```env
# Database connection
DB_HOST=localhost
DB_PORT=5433
DB_NAME=dataplatform
DB_USER=datauser
DB_PASSWORD=mypassword

# SSL/TLS Configuration
DB_SSL_MODE=require
DB_SSL_CA_PATH=./postgres-ssl/ca.crt
DB_SSL_CERT_PATH=./postgres-ssl/client.crt  # Optional: for client cert auth
DB_SSL_KEY_PATH=./postgres-ssl/client.key   # Optional: for client cert auth
```

**SSL Modes:**
- `disable` - No SSL
- `allow` - Try SSL, fallback to non-SSL
- `prefer` - Try SSL, fallback to non-SSL (default)
- `require` - Require SSL (recommended)
- `verify-ca` - Require SSL and verify CA
- `verify-full` - Require SSL, verify CA and hostname

### Step 3: Start Services

```bash
docker-compose -f docker-compose-airflow.yml up -d
```

PostgreSQL will now:
- Accept only SSL connections
- Use the certificates from `postgres-ssl/` directory
- Encrypt all data in transit

### Step 4: Verify SSL Connection

```python
from pipelines.db_connector import DatabaseConnector

db = DatabaseConnector()
if db.test_connection():
    print("✓ SSL connection successful!")
```

## Part 2: AES-256 Encryption at Rest

PostgreSQL encryption at rest can be achieved through:

### Option A: Filesystem-Level Encryption (Recommended)

Encrypt the Docker volume at the filesystem level:

#### Linux (LUKS)
```bash
# Create encrypted volume
sudo cryptsetup luksFormat /dev/sdX
sudo cryptsetup luksOpen /dev/sdX encrypted_postgres
sudo mkfs.ext4 /dev/mapper/encrypted_postgres

# Mount encrypted volume
sudo mount /dev/mapper/encrypted_postgres /mnt/encrypted_postgres

# Update docker-compose to use this mount
```

#### Windows (BitLocker)
1. Enable BitLocker on the drive
2. Docker volumes on that drive will be encrypted

#### Docker Volume Encryption
Update `docker-compose-airflow.yml` to use an encrypted volume:

```yaml
volumes:
  airflow-postgres-data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /path/to/encrypted/mount  # Encrypted filesystem
```

### Option B: PostgreSQL TDE (Enterprise Only)

PostgreSQL Transparent Data Encryption requires:
- PostgreSQL Enterprise Edition
- Or use extensions like `pgcrypto` for column-level encryption

For development/testing, filesystem encryption is sufficient.

### Option C: Application-Level Encryption

Encrypt sensitive data before storing:

```python
from cryptography.fernet import Fernet
import base64
import os

# Generate key (store securely)
key = Fernet.generate_key()
cipher = Fernet(key)

# Encrypt data
encrypted_data = cipher.encrypt(b"sensitive data")

# Decrypt data
decrypted_data = cipher.decrypt(encrypted_data)
```

## Configuration Files

### Updated Files

1. **docker-compose-airflow.yml**
   - Added SSL configuration to PostgreSQL service
   - Mounted SSL certificates

2. **pipelines/db_connector.py**
   - Added SSL/TLS support
   - Configurable SSL modes
   - Certificate path configuration

3. **Environment Variables**
   - `DB_SSL_MODE` - SSL connection mode
   - `DB_SSL_CA_PATH` - CA certificate path
   - `DB_SSL_CERT_PATH` - Client certificate path (optional)
   - `DB_SSL_KEY_PATH` - Client key path (optional)

## Security Best Practices

1. **Certificate Management**
   - Keep private keys secure (600 permissions)
   - Rotate certificates annually
   - Use strong passphrases for production

2. **SSL Configuration**
   - Use `verify-ca` or `verify-full` in production
   - Disable weak ciphers
   - Keep PostgreSQL updated

3. **Encryption at Rest**
   - Use filesystem-level encryption for best performance
   - Store encryption keys securely (key management service)
   - Regular backups of encrypted volumes

4. **Access Control**
   - Limit database access to necessary services
   - Use strong passwords
   - Implement network isolation

## Testing

### Test SSL Connection

```python
# test_ssl_connection.py
from pipelines.db_connector import DatabaseConnector
import os

# Set SSL mode
os.environ['DB_SSL_MODE'] = 'require'
os.environ['DB_SSL_CA_PATH'] = './postgres-ssl/ca.crt'

db = DatabaseConnector()
if db.test_connection():
    print("✓ SSL connection successful!")
else:
    print("✗ SSL connection failed!")
```

### Verify SSL is Required

Try connecting without SSL (should fail):
```python
os.environ['DB_SSL_MODE'] = 'disable'
db = DatabaseConnector()
# This should fail if PostgreSQL requires SSL
```

## Troubleshooting

### Certificate Errors

**Error**: `SSL connection required`
- **Solution**: Ensure `DB_SSL_MODE=require` is set

**Error**: `certificate verify failed`
- **Solution**: Check `DB_SSL_CA_PATH` points to correct CA certificate

**Error**: `permission denied` for certificate files
- **Solution**: Set proper permissions: `chmod 600 *.key` and `chmod 644 *.crt`

### Connection Issues

**Error**: `Connection refused`
- **Solution**: Check PostgreSQL is running and SSL is configured correctly

**Error**: `SSL handshake failed`
- **Solution**: Verify certificates are valid and not expired

## Production Deployment

For production environments:

1. **Use CA-signed certificates** (not self-signed)
2. **Enable `verify-full` SSL mode**
3. **Implement key rotation** strategy
4. **Use hardware security modules (HSM)** for key storage
5. **Enable audit logging** for database access
6. **Regular security audits**

## Compliance

This implementation helps meet:
- **TLS requirement**: All data encrypted in transit
- **AES-256 requirement**: Data encrypted at rest (via filesystem encryption)

---

*Last Updated: 2025-12-13*

