# Unified NetBox and Nautobot Docker Setup

This directory contains a unified docker-compose setup that runs both NetBox and Nautobot simultaneously with isolated networks and preserved configurations.

## Services

### NetBox
- **URL**: http://192.168.5.9:8080
- **Database**: PostgreSQL 17 (isolated)
- **Cache**: Redis/Valkey (isolated)
- **Configuration**: Uses existing `../netbox-docker/configuration/` and `../netbox-docker/env/` files
- **Credentials**: Preserved from existing setup

### Nautobot
- **URL**: http://192.168.5.9:8081
- **Database**: PostgreSQL 15 (isolated)
- **Cache**: Redis 7 (isolated)
- **Configuration**: Uses local `./env/` files
- **Default Credentials**: nautobot/nautobot (change in production)

## Quick Start

1. **Clean start** (recommended for first run):
   ```bash
   ./cleanup.sh --db
   ./start.sh
   ```

2. **Regular start**:
   ```bash
   ./start.sh
   ```

3. **Clean start** (removes conflicting containers):
   ```bash
   ./start.sh --clean
   ```

4. **Create users** (interactive):
   ```bash
   ./create-users.sh
   ```

5. **Test database connections**:
   ```bash
   ./test-db-connections.sh
   ```

6. **Test Nautobot environment**:
   ```bash
   ./test-nautobot-env.sh
   ```

7. **View logs**:
   ```bash
   docker compose logs -f
   ```

8. **Stop all services**:
   ```bash
   docker compose down
   ```

9. **Stop and remove volumes** (WARNING: This will delete all data):
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

### Common Issues

1. **Nautobot Database Connection Error**:
   - **Error**: `django.db.utils.OperationalError: connection to server at "localhost" (::1), port 5432 failed`
   - **Cause**: Nautobot is trying to connect to localhost instead of the PostgreSQL service
   - **Solution**: Ensure `NAUTOBOT_DB_HOST=postgres` in `env/nautobot.env`
   - **Test**: Run `./test-nautobot-env.sh` to verify environment variables

2. **Container Name Conflicts**:
   - **Error**: `Conflict. The container name "/netbox" is already in use`
   - **Solution**: Run `./cleanup.sh --clean` or `./start.sh --clean`

3. **Database Not Ready**:
   - **Error**: Services fail to start due to database connectivity
   - **Solution**: Wait for databases to be ready, or restart with `./start.sh`

### Debugging Commands

1. **Check service status**:
   ```bash
   docker compose ps
   ```

2. **View specific service logs**:
   ```bash
   docker compose logs netbox
   docker compose logs nautobot
   ```

3. **Test database connections**:
   ```bash
   ./test-db-connections.sh
   ```

4. **Test Nautobot environment**:
   ```bash
   ./test-nautobot-env.sh
   ```

5. **Restart a specific service**:
   ```bash
   docker compose restart netbox
   docker compose restart nautobot
   ```

6. **Access service shells**:
   ```bash
   docker compose exec netbox bash
   docker compose exec nautobot bash
   ```

## Scripts

### Core Scripts
- **`start.sh`**: Main startup script with database wait logic and auto-initialization
- **`cleanup.sh`**: Comprehensive cleanup utility with multiple options
- **`create-users.sh`**: Interactive user creation for both services
- **`test-db-connections.sh`**: Test database connectivity
- **`test-nautobot-env.sh`**: Test Nautobot environment variables

### Script Options
```bash
# Get help for any script
./start.sh --help
./cleanup.sh --help
./create-users.sh --help
./test-db-connections.sh --help

# Cleanup options
./cleanup.sh                 # Fast clean (keep DBs)
./cleanup.sh --db            # Fast clean + wipe both DBs
./cleanup.sh --nautobot-only # Only Nautobot cleanup
./cleanup.sh --netbox-only   # Only NetBox cleanup
./cleanup.sh --all --images  # Both stacks + prune images
./cleanup.sh --hard          # Also remove networks and volumes
```

## Security Notes

- NetBox uses existing credentials and configurations
- Nautobot uses default credentials (change for production)
- Both services are isolated and cannot communicate with each other
- All services run on localhost only (not exposed externally)
