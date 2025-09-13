# Unified NetBox and Nautobot Docker Setup

This directory contains a unified docker-compose setup that runs both NetBox and Nautobot simultaneously with isolated networks and preserved configurations.

## Services

### NetBox
- **URL**: http://localhost:8080
- **Database**: PostgreSQL 17 (isolated)
- **Cache**: Redis/Valkey (isolated)
- **Configuration**: Uses existing `../netbox-docker/configuration/` and `../netbox-docker/env/` files
- **Credentials**: Preserved from existing setup

### Nautobot
- **URL**: http://localhost:8081
- **Database**: PostgreSQL 15 (isolated)
- **Cache**: Redis 7 (isolated)
- **Configuration**: Uses local `./env/` files
- **Default Credentials**: nautobot/nautobot (change in production)

## Quick Start

1. **Start all services**:
   ```bash
   docker compose up -d --build
   ```

2. **View logs**:
   ```bash
   docker compose logs -f
   ```

3. **Stop all services**:
   ```bash
   docker compose down
   ```

4. **Stop and remove volumes** (WARNING: This will delete all data):
   ```bash
   docker compose down -v
   ```

## Configuration

### NetBox
- All existing configurations and credentials are preserved
- Uses the original `netbox-docker` configuration files
- No changes needed to existing setup

### Nautobot
- Environment variables are in `./env/nautobot.env`
- Database configuration is in `./env/nautobot-postgres.env`
- **IMPORTANT**: Change the `SECRET_KEY` in `./env/nautobot.env` for production use

## Network Isolation

Each service runs in its own isolated network:
- `netbox-net`: NetBox and its dependencies
- `nautobot-net`: Nautobot and its dependencies

This prevents conflicts while maintaining the hostname expectations from the original configurations.

## Data Persistence

- **NetBox**: Uses Docker volumes for data persistence
- **Nautobot**: Uses local directories (`./postgres/`, `./redis/`) for data persistence

## Troubleshooting

1. **Check service status**:
   ```bash
   docker compose ps
   ```

2. **View specific service logs**:
   ```bash
   docker compose logs netbox
   docker compose logs nautobot
   ```

3. **Restart a specific service**:
   ```bash
   docker compose restart netbox
   docker compose restart nautobot
   ```

4. **Access service shells**:
   ```bash
   docker compose exec netbox bash
   docker compose exec nautobot bash
   ```

## Security Notes

- NetBox uses existing credentials and configurations
- Nautobot uses default credentials (change for production)
- Both services are isolated and cannot communicate with each other
- All services run on localhost only (not exposed externally)
