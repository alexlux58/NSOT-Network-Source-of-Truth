# NSOT - Network Source of Truth

This repository contains Docker-based deployments for two popular Network Source of Truth (NSOT) platforms: **NetBox** and **Nautobot**. These platforms help network engineers manage and document their network infrastructure, IP addresses, devices, circuits, and more.

## 📋 Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [NetBox](#netbox)
- [Nautobot](#nautobot)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Maintenance](#maintenance)

## 🎯 Overview

This project provides containerized deployments for:

- **NetBox**: An open-source IP address management (IPAM) and data center infrastructure management (DCIM) tool
- **Nautobot**: A Network Source of Truth platform (originally forked from NetBox) with enhanced extensibility and plugin architecture

Both platforms are designed to serve as the single source of truth for network infrastructure documentation and management.

## 📁 Project Structure

```
NSOT-Network-Source-of-Truth/
├── netbox-docker/          # NetBox Docker deployment
│   ├── configuration/      # NetBox configuration files
│   ├── docker/            # Docker-specific configuration
│   ├── env/               # Environment variable files
│   ├── docker-compose.yml # NetBox Docker Compose configuration
│   └── Dockerfile         # Custom NetBox Docker image build
│
└── nautobot-docker/        # Nautobot Docker deployment
    ├── env/               # Environment variable files
    └── docker-compose.yml # Nautobot Docker Compose configuration
```

## 🔧 Prerequisites

Before getting started, ensure you have the following installed:

- **Docker**: Version 20.10.10 or higher
- **Docker Compose**: Version 1.28.0 or higher (or Docker Compose V2)
- **containerd**: Version 1.5.6 or higher (if using containerd)

To check your versions:
```bash
docker --version
docker compose version
```

## 🚀 Quick Start

### NetBox

1. Navigate to the NetBox directory:
   ```bash
   cd netbox-docker
   ```

2. Create a port mapping override (optional, for local access):
   ```bash
   tee docker-compose.override.yml <<EOF
   services:
     netbox:
       ports:
         - 8000:8080
   EOF
   ```

3. Pull the latest images and start the services:
   ```bash
   docker compose pull
   docker compose up -d
   ```

4. Access NetBox at `http://localhost:8000`

5. Create the first admin user:
   ```bash
   docker compose exec netbox /opt/netbox/netbox/manage.py createsuperuser
   ```

### Nautobot

1. Navigate to the Nautobot directory:
   ```bash
   cd nautobot-docker
   ```

2. Create environment file (if not already present):
   ```bash
   mkdir -p env
   # Create env/.env with required configuration
   ```

3. Start the services:
   ```bash
   docker compose up -d
   ```

4. Access Nautobot at `http://localhost:8081`

5. Create the first admin user:
   ```bash
   docker compose exec nautobot nautobot-server createsuperuser
   ```

## ⚙️ Configuration

### NetBox Configuration

NetBox configuration is managed through:

- **Environment files**: Located in `netbox-docker/env/`
  - `netbox.env` - Main NetBox configuration
  - `postgres.env` - PostgreSQL database settings
  - `redis.env` - Redis task queue settings
  - `redis-cache.env` - Redis cache settings

- **Configuration files**: Located in `netbox-docker/configuration/`
  - `configuration.py` - Main configuration (read from environment variables)
  - `extra.py` - Additional custom settings
  - `logging.py` - Logging configuration
  - `plugins.py` - Plugin configuration

Key environment variables to configure:
- `SECRET_KEY` - Django secret key (required)
- `DB_NAME`, `DB_USER`, `DB_PASSWORD` - Database credentials
- `REDIS_PASSWORD` - Redis password
- `ALLOWED_HOSTS` - Allowed hostnames for the application

### Nautobot Configuration

Nautobot configuration is managed through:

- **Environment file**: `nautobot-docker/env/.env`

Required environment variables:
- `NAUTOBOT_SECRET_KEY` - Django secret key
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` - Database credentials
- `NAUTOBOT_ALLOWED_HOSTS` - Allowed hostnames
- Additional Nautobot-specific settings

## 🗄️ Services

### NetBox Services

- **netbox**: Main web application
- **netbox-worker**: Background task worker (RQ)
- **postgres**: PostgreSQL database
- **redis**: Redis for task queue
- **redis-cache**: Redis for caching

### Nautobot Services

- **nautobot**: Main web application
- **nautobot-worker**: Background task worker (RQ)
- **nautobot-beat**: Celery beat scheduler
- **postgres**: PostgreSQL database
- **redis**: Redis for task queue and caching

## 📊 Data Persistence

Both deployments use Docker volumes to persist data:

- **NetBox**: 
  - `netbox-postgres-data` - Database data
  - `netbox-redis-data` - Redis task queue data
  - `netbox-redis-cache-data` - Redis cache data
  - `netbox-media-files` - Uploaded media files
  - `netbox-reports-files` - Report files
  - `netbox-scripts-files` - Custom scripts

- **Nautobot**:
  - `./postgres` - Database data (local directory)
  - `./redis` - Redis data (local directory)
  - `nautobot-media` - Uploaded media files
  - `nautobot-static` - Static files

## 🔄 Updating

### NetBox

1. Pull the latest images:
   ```bash
   cd netbox-docker
   docker compose pull
   ```

2. Stop services:
   ```bash
   docker compose down
   ```

3. Start with new images:
   ```bash
   docker compose up -d
   ```

4. Run database migrations:
   ```bash
   docker compose exec netbox /opt/netbox/netbox/manage.py migrate
   ```

### Nautobot

1. Pull the latest images:
   ```bash
   cd nautobot-docker
   docker compose pull
   ```

2. Stop and restart services:
   ```bash
   docker compose down
   docker compose up -d
   ```

3. Run database migrations:
   ```bash
   docker compose exec nautobot nautobot-server migrate
   ```

## 🛠️ Maintenance

### Viewing Logs

**NetBox:**
```bash
cd netbox-docker
docker compose logs -f netbox
```

**Nautobot:**
```bash
cd nautobot-docker
docker compose logs -f nautobot
```

### Stopping Services

**NetBox:**
```bash
cd netbox-docker
docker compose down
```

**Nautobot:**
```bash
cd nautobot-docker
docker compose down
```

### Backup and Restore

Both platforms store data in PostgreSQL. To backup:

**NetBox:**
```bash
docker compose exec postgres pg_dump -U netbox netbox > backup.sql
```

**Nautobot:**
```bash
docker compose exec postgres pg_dump -U nautobot nautobot > backup.sql
```

## 📚 Additional Resources

### NetBox

- [NetBox Documentation](https://docs.netbox.dev/)
- [NetBox Docker Wiki](https://github.com/netbox-community/netbox-docker/wiki)
- [NetBox Community Slack](https://join.slack.com/t/netdev-community/shared_invite/zt-mtts8g0n-Sm6Wutn62q_M4OdsaIycrQ)

### Nautobot

- [Nautobot Documentation](https://docs.nautobot.com/)
- [Nautobot GitHub](https://github.com/nautobot/nautobot)

## 🔒 Security Notes

- **Never commit secrets**: Ensure `.env` files and secret files are in `.gitignore`
- **Change default passwords**: Always change default database and Redis passwords
- **Use strong SECRET_KEY**: Generate a strong secret key for production deployments
- **Configure ALLOWED_HOSTS**: Set appropriate allowed hosts for production
- **Enable HTTPS**: Use a reverse proxy (nginx, Traefik) with SSL/TLS in production

## 🤝 Contributing

This repository contains configurations for both NetBox and Nautobot. If you're contributing:

- NetBox Docker: See `netbox-docker/README.md` and the [NetBox Docker repository](https://github.com/netbox-community/netbox-docker)
- Nautobot: See `nautobot-docker/README.md` and the [Nautobot repository](https://github.com/nautobot/nautobot)

## 📝 License

- **NetBox Docker**: See `netbox-docker/LICENSE`
- **Nautobot**: See respective Nautobot project license

## ⚠️ Important Notes

- Both platforms should not be run simultaneously on the same ports
- Ensure sufficient system resources (CPU, RAM, disk) for production deployments
- Regular backups are essential for production environments
- Review and customize configuration files according to your environment needs

---

**Note**: This repository provides Docker-based deployments for evaluation and development. For production deployments, consider additional security hardening, monitoring, and backup strategies.

