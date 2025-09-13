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

1. **Fresh start** (recommended for first run or after issues):
   ```bash
   ./cleanup.sh --db
   # If permission errors occur, manually remove directories:
   sudo rm -rf postgres/ redis/
   ./start.sh --clean
   ```

2. **Regular start**:
   ```bash
   ./start.sh
   ```

3. **Clean start** (removes conflicting containers only):
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

7. **Verify complete setup**:
   ```bash
   ./verify-setup.sh
   ```

8. **View logs**:
   ```bash
   docker compose logs -f
   ```

9. **Stop all services**:
   ```bash
   docker compose down
   ```

10. **Stop and remove volumes** (WARNING: This will delete all data):
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

## Fresh Start Procedure

When you need to completely reset the environment (e.g., after migration conflicts or to start over):

### Step 1: Clean Everything
```bash
./cleanup.sh --db
```

### Step 2: Handle Permission Errors (if any)
If you see permission errors during cleanup:
```bash
sudo rm -rf postgres/ redis/
```

### Step 3: Fresh Start
```bash
./start.sh --clean
```

### Step 4: Verify Success
```bash
# Check that both services are running
docker compose ps

# Test database connections
./test-db-connections.sh

# Test Nautobot environment
./test-nautobot-env.sh

# Access the services
# NetBox: http://192.168.5.9:8080
# Nautobot: http://192.168.5.9:8081
```

### Why This Procedure Works
- **Complete database wipe**: Removes all partial migration state
- **Fresh migrations**: Nautobot runs all migrations from scratch
- **No conflicts**: Eliminates "column already exists" or "duplicate key" errors
- **Clean slate**: Both services start with fresh, consistent state

## Troubleshooting

### Common Issues

1. **Nautobot Migration Conflicts**:
   - **Error**: `UndefinedColumn: column "level" of relation "dcim_inventoryitem" does not exist` or `duplicate key value violates unique constraint`
   - **Cause**: Incomplete database cleanup left partial migration state
   - **Solution**: 
     ```bash
     # Full database reset
     ./cleanup.sh --db
     # If permission errors occur, manually remove directories:
     sudo rm -rf postgres/ redis/
     # Then clean start
     ./start.sh --clean
     ```
   - **Prevention**: Always use `./cleanup.sh --db` before fresh starts

2. **Permission Denied During Cleanup**:
   - **Error**: `Permission denied` when removing `postgres/` or `redis/` directories
   - **Cause**: Directories created by Docker containers running as root
   - **Solution**: 
     ```bash
     sudo rm -rf postgres/ redis/
     ./start.sh --clean
     ```
   - **Note**: The cleanup script will now clearly indicate when manual removal is needed

3. **Nautobot Database Connection Error**:
   - **Error**: `django.db.utils.OperationalError: connection to server at "localhost" (::1), port 5432 failed`
   - **Cause**: Nautobot is trying to connect to localhost instead of the PostgreSQL service
   - **Solution**: Ensure `NAUTOBOT_DB_HOST=postgres` in `env/nautobot.env`
   - **Test**: Run `./test-nautobot-env.sh` to verify environment variables

4. **Container Name Conflicts**:
   - **Error**: `Conflict. The container name "/netbox" is already in use`
   - **Solution**: Run `./cleanup.sh --clean` or `./start.sh --clean`

5. **Database Not Ready Timeout**:
   - **Error**: `PostgreSQL not ready after 30s` on first startup
   - **Cause**: Fresh database initialization takes longer
   - **Solution**: Wait a bit longer and re-run `./start.sh --clean`
   - **Note**: Subsequent starts are faster after initial setup

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
- **`verify-setup.sh`**: Comprehensive setup verification and health checks

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
