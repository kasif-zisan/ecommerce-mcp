# Complete Guide: Setting Up PostgreSQL Database Locally

This guide covers everything from installation to creating and accessing a PostgreSQL database using both psql and pgAdmin.

---

## Table of Contents
1. [Installing PostgreSQL](#1-installing-postgresql)
2. [Verifying Installation](#2-verifying-installation)
3. [Creating Your SQL File](#3-creating-your-sql-file)
4. [Configuring PostgreSQL for Local Access](#4-configuring-postgresql-for-local-access)
5. [Setting Up Password Authentication](#5-setting-up-password-authentication)
6. [Running Your SQL Script](#6-running-your-sql-script)
7. [Connecting with pgAdmin](#7-connecting-with-pgadmin)
8. [Managing PostgreSQL Service](#8-managing-postgresql-service)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Installing PostgreSQL

### On Ubuntu/Debian

```bash
# Update package list
sudo apt update

# Install PostgreSQL and additional tools
sudo apt install postgresql postgresql-contrib

# Install pgAdmin (optional, for GUI access)
sudo apt install pgadmin4
```

---

## 2. Verifying Installation

### Check PostgreSQL Version

```bash
psql --version
```

Expected output:
```
psql (PostgreSQL) 16.x
```

### Check if PostgreSQL is Installed

```bash
# Check service status
sudo systemctl status postgresql
```

### Check PostgreSQL Server Version

```bash
sudo -u postgres psql -c "SELECT version();"
```

---

## 3. Creating Your SQL File

Create a file named `database_setup.sql` with your database schema.

---

## 4. Configuring PostgreSQL for Local Access

### Step 1: Edit postgresql.conf

Find and edit the PostgreSQL configuration file:

```bash
# Find PostgreSQL version
ls /etc/postgresql/

# Edit configuration (replace * with your version number, e.g., 16)
sudo nano /etc/postgresql/*/main/postgresql.conf
```

Find the line with `listen_addresses` and modify it:

```conf
# Before (commented out):
#listen_addresses = 'localhost'

# After (uncommented):
listen_addresses = 'localhost'
```

**Save and exit:** Press `Ctrl+X`, then `Y`, then `Enter`

### Step 2: Edit pg_hba.conf (Authentication Configuration)

```bash
sudo nano /etc/postgresql/*/main/pg_hba.conf
```

Find the section that says `# IPv4 local connections:` and modify the line:

```conf
# Before:
host    all             all             127.0.0.1/32            scram-sha-256

# After (change to md5 for wider compatibility):
host    all             all             127.0.0.1/32            md5
```

**Note:** You can keep `scram-sha-256` if you're using a modern version of pgAdmin. `md5` is more compatible with older tools.

**Save and exit:** Press `Ctrl+X`, then `Y`, then `Enter`

### Step 3: Restart PostgreSQL

```bash
sudo systemctl restart postgresql
```

---

## 5. Setting Up Password Authentication

### Set a Password for the postgres User

```bash
# Connect to PostgreSQL as postgres user
sudo -u postgres psql
```

Inside the psql prompt:

```sql
-- Set password for postgres user
ALTER USER postgres PASSWORD 'your_secure_password';

-- Verify the change
\du

-- Exit psql
\q
```

**Important:** Remember this password - you'll need it for pgAdmin!

---

## 6. Running Your SQL Script

### Method 1: Without Password (Using sudo)

```bash
sudo -u postgres psql -f database_setup.sql
```

### Method 2: With Password (TCP/IP Connection)

```bash
psql -U postgres -h localhost -f database_setup.sql -W
```

It will prompt you for the password you set earlier.

### Method 3: Interactive Mode

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Run the script from within psql
\i /path/to/database_setup.sql

# Or if already in the directory
\i database_setup.sql
```

---

## 7. Connecting with pgAdmin

### Launch pgAdmin

```bash
pgadmin4
# Or launch from your applications menu
```

### Add a New Server

1. **Right-click on "Servers"** → Select **"Register"** → **"Server..."**

2. **General Tab:**
   - Name: `Local PostgreSQL` (or any name you prefer)

3. **Connection Tab:**
   - Host name/address: `localhost` or `127.0.0.1`
   - Port: `5432`
   - Maintenance database: `postgres`
   - Username: `postgres`
   - Password: (the password you set earlier)
   - ☑ Save password (optional)

4. **Click "Save"**

### Navigate to Your Database

```
Servers → Local PostgreSQL → Databases → my_database → Schemas → public → Tables
```

You should now see your tables and can browse/query them!

---

## 8. Managing PostgreSQL Service

### Start PostgreSQL

```bash
sudo systemctl start postgresql
```

### Stop PostgreSQL

```bash
sudo systemctl stop postgresql
```

### Restart PostgreSQL

```bash
sudo systemctl restart postgresql
```

### Check Status

```bash
sudo systemctl status postgresql
```

Expected output when running:
```
● postgresql.service - PostgreSQL RDBMS
     Loaded: loaded
     Active: active (running)
```

### Enable Auto-Start on Boot

```bash
sudo systemctl enable postgresql
```

### Disable Auto-Start on Boot

```bash
sudo systemctl disable postgresql
```

### Check if Auto-Start is Enabled

```bash
sudo systemctl is-enabled postgresql
```

---

## 9. Troubleshooting

### Issue: "psql: error: connection to server on socket failed"

**Solution:** PostgreSQL is not running. Start it:

```bash
sudo systemctl start postgresql
sudo systemctl status postgresql
```

---

### Issue: "fe_sendauth: no password supplied"

**Solution:** Either:
- Remove `-h localhost` to use socket authentication:
  ```bash
  sudo -u postgres psql -f database_setup.sql
  ```
- Or set a password and use `-W` flag:
  ```bash
  psql -U postgres -h localhost -f database_setup.sql -W
  ```

---

### Issue: "FATAL: Peer authentication failed"

**Solution:** Edit `/etc/postgresql/*/main/pg_hba.conf` and change:

```conf
local   all             postgres                                peer
```

To:

```conf
local   all             postgres                                md5
```

Then restart PostgreSQL.

---

### Issue: Can't connect from pgAdmin

**Checklist:**
1. ✓ PostgreSQL is running: `sudo systemctl status postgresql`
2. ✓ Password is set: `sudo -u postgres psql -c "\du"`
3. ✓ `postgresql.conf` has `listen_addresses = 'localhost'`
4. ✓ `pg_hba.conf` has the correct authentication method
5. ✓ PostgreSQL was restarted after config changes
6. ✓ Using correct credentials in pgAdmin

---

### Issue: Port 5432 is already in use

**Check what's using the port:**

```bash
sudo lsof -i :5432
```

**Kill the process if needed:**

```bash
sudo systemctl stop postgresql
```

---

## Quick Reference Commands

### Useful psql Commands

```bash
# Connect to a database
psql -U postgres -d database_name

# List all databases
\l

# Connect to a different database
\c database_name

# List all tables in current database
\dt

# Describe a table structure
\d table_name

# Execute SQL file
\i /path/to/file.sql

# Exit psql
\q
```

### Useful SQL Queries

```sql
-- List all databases
SELECT datname FROM pg_database;

-- List all tables in current database
SELECT tablename FROM pg_tables WHERE schemaname = 'public';

-- Check current user
SELECT current_user;

-- Check current database
SELECT current_database();

-- Show all users
SELECT usename FROM pg_user;
```

---

## Workflow Summary

### Initial Setup (One-time)
1. Install PostgreSQL
2. Configure `postgresql.conf` and `pg_hba.conf`
3. Set password for postgres user
4. Restart PostgreSQL
5. Configure pgAdmin connection

### Daily Usage
1. Start PostgreSQL: `sudo systemctl start postgresql`
2. Run SQL scripts: `sudo -u postgres psql -f script.sql`
3. Access via pgAdmin: Open pgAdmin and connect to your server
4. Stop PostgreSQL (optional): `sudo systemctl stop postgresql`

---

## Additional Resources

- **Official PostgreSQL Documentation:** https://www.postgresql.org/docs/
- **pgAdmin Documentation:** https://www.pgadmin.org/docs/
- **PostgreSQL Tutorial:** https://www.postgresqltutorial.com/
- **SQL Tutorial:** https://www.w3schools.com/sql/

---

## Security Best Practices

1. **Use strong passwords** for the postgres user
2. **Don't expose PostgreSQL** to the internet (keep it on localhost)
3. **Use `scram-sha-256`** instead of `md5` when possible
4. **Regularly backup** your databases
5. **Keep PostgreSQL updated** to the latest stable version

---

**Last Updated:** October 2025  
**PostgreSQL Version:** 16.x  
**Tested On:** Ubuntu 24.04 LTS
