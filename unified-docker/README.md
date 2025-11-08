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

### Nornir Automation
- **URL**: http://192.168.5.9:8082
- **Purpose**: Network configuration validation and automation
- **Features**: NAPALM integration, configuration drift detection, source-of-truth management
- **API Documentation**: http://192.168.5.9:8082/api/docs/

## Quick Start

### Option 1: Unified Setup (Recommended)
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

4. **Start with Nornir Automation**:
   ```bash
   ./start.sh
   ./start-nornir.sh
   ```

### Option 2: Individual Services
If you prefer to run NetBox and Nautobot separately:

**NetBox Only:**
```bash
cd ../netbox-docker
docker compose up -d
# Access: http://192.168.5.9:8080
```

**Nautobot Only:**
```bash
cd ../nautobot-docker  
docker compose up -d
# Access: http://192.168.5.9:8081
```

**⚠️ Important:** If running individual services, be aware of:
- **Port conflicts** - Both use port 8080 by default
- **Database conflicts** - May interfere with unified setup
- **Configuration differences** - Individual setups may have different configs
- **Migration issues** - Individual services may have the same migration race conditions

### Option 3: Nuclear Docker Cleanup
If you want to completely reset your entire Docker environment:

```bash
./nuclear-cleanup.sh
```

**⚠️ WARNING:** This will remove ALL Docker containers, images, volumes, and networks on your system. Use only when you want to start completely fresh.

# create an admin user interactively
docker exec -it nautobot nautobot-server createsuperuser

# interactive superuser creation
docker compose exec netbox /opt/netbox/venv/bin/python /opt/netbox/netbox/manage.py createsuperuser


## Improved Startup Process

The startup script now uses a **sequential approach** to prevent migration conflicts:

### Phase 1: Database Initialization
- Starts PostgreSQL and Redis for both NetBox and Nautobot
- Waits for databases to be ready and healthy
- Uses proper health checks and timeouts

### Phase 2: Web Services (Migrations)
- Starts NetBox and Nautobot web containers
- These containers run database migrations automatically
- Waits for both services to be fully ready before proceeding

### Phase 3: Worker Services
- Starts NetBox worker, Nautobot worker, and Nautobot beat
- Worker containers skip migrations (using `NAUTOBOT_SKIP_STARTUP_MIGRATIONS=true`)
- No race conditions or database conflicts

### Benefits
- ✅ **No more migration conflicts** - only web containers run migrations
- ✅ **Reliable startup** - proper sequencing and health checks
- ✅ **Faster recovery** - no need to manually fix corrupted databases
- ✅ **Better error handling** - clear messages and proper timeouts

### Technical Changes Made
- **Sequential Container Startup**: Databases → Web Services → Workers
- **Environment Variables**: Added `NAUTOBOT_SKIP_STARTUP_MIGRATIONS=true` to worker containers
- **Health Checks**: Improved database readiness detection with proper timeouts
- **Error Handling**: Replaced macOS-incompatible `timeout` command with custom loops
- **Dependency Management**: Workers depend on web services being ready, not just started

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

## Nornir Automation Features

The Nornir automation service provides comprehensive network configuration validation and management capabilities:

### 🔧 Core Features

- **Configuration Validation**: Compare live device configurations against source-of-truth
- **Drift Detection**: Automatically detect configuration changes and drift
- **Multi-Vendor Support**: Support for Cisco, Juniper, Arista, HP, Fortinet, and more via NAPALM
- **Source of Truth Management**: Store and manage reference configurations
- **Web Interface**: Modern, responsive web UI for all operations
- **REST API**: Full REST API for integration with other tools

### 📊 Configuration Validation

- **Live vs Source-of-Truth**: Compare running configurations with stored reference configs
- **Line-by-Line Analysis**: Detailed comparison showing missing and extra lines
- **Bulk Validation**: Validate multiple devices simultaneously
- **Group-based Validation**: Run validation on specific device groups (routers, switches, etc.)
- **Dry Run Mode**: Safe validation without making changes

### 🗂️ Inventory Management

- **Device Discovery**: Automatic device discovery from NetBox and Nautobot
- **Multi-Source Sync**: Sync inventory from multiple sources
- **Group Management**: Organize devices into logical groups
- **Vendor Mapping**: Automatic mapping of vendors to NAPALM drivers
- **Custom Attributes**: Store custom device attributes and metadata

### 📈 Reporting & Analytics

- **Multiple Formats**: Generate reports in JSON, CSV, Excel, and HTML formats
- **Validation History**: Track validation results over time
- **Drift Analytics**: Analyze configuration drift patterns
- **Compliance Reports**: Generate compliance and audit reports
- **Scheduled Reports**: Automated report generation

### 🔌 Integrations

- **NetBox Integration**: Sync device inventory and metadata
- **Nautobot Integration**: Sync device inventory and metadata
- **API Integration**: RESTful API for external tool integration
- **Webhook Support**: Send notifications on validation results

### 🚀 Getting Started with Nornir Automation

1. **Access the Web Interface**:
   ```bash
   # Open in browser
   http://localhost:8082
   ```

2. **Set up Device Inventory**:
   ```bash
   # Create sample inventory
   docker compose exec nornir-automation python scripts/setup_inventory.py --sample
   
   # Sync from NetBox
   docker compose exec nornir-automation python scripts/setup_inventory.py --netbox YOUR_API_TOKEN
   
   # Sync from Nautobot
   docker compose exec nornir-automation python scripts/setup_inventory.py --nautobot YOUR_API_TOKEN
   ```

3. **Run Configuration Validation**:
   ```bash
   # Validate all devices
   docker compose exec nornir-automation python scripts/validate_configs.py validate --device-group all
   
   # Validate specific group
   docker compose exec nornir-automation python scripts/validate_configs.py validate --device-group routers
   
   # Compare specific device
   docker compose exec nornir-automation python scripts/validate_configs.py compare rtr-01
   ```

4. **Save Source of Truth**:
   ```bash
   # Save current config as source of truth
   docker compose exec nornir-automation python scripts/validate_configs.py save-sot rtr-01 --config-type running
   ```

### 📚 API Usage

The Nornir automation service provides a comprehensive REST API:

```bash
# Health check
curl http://localhost:8082/api/health

# Get device inventory
curl http://localhost:8082/api/inventory

# Run validation
curl -X POST http://localhost:8082/api/validate \
  -H "Content-Type: application/json" \
  -d '{"device_group": "all", "config_type": "running", "dry_run": true}'

# Get reports
curl http://localhost:8082/api/reports
```

### 🔧 Configuration

Key configuration files and directories:

- **Inventory**: `./nornir-automation/inventory/` - Device inventory files
- **Configs**: `./nornir-automation/configs/` - Source-of-truth configurations
- **Reports**: `./nornir-automation/reports/` - Generated reports
- **Logs**: `./nornir-automation/logs/` - Application logs

### 🛠️ Troubleshooting

Common issues and solutions:

1. **Service not starting**:
   ```bash
   # Check logs
   docker compose logs nornir-automation
   
   # Restart service
   docker compose restart nornir-automation
   ```

2. **Device connection issues**:
   - Verify device credentials in inventory files
   - Check network connectivity to devices
   - Ensure NAPALM drivers are installed for your device type

3. **Validation failures**:
   - Check device connectivity
   - Verify device credentials
   - Review validation logs for specific error messages

### 📖 Additional Resources

- **API Documentation**: http://localhost:8082/api/docs/
- **Nornir Documentation**: https://nornir.readthedocs.io/
- **NAPALM Documentation**: https://napalm.readthedocs.io/
- **Source Code**: Available in `./nornir-automation/` directory

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

## Migration Race Condition Fix

**IMPORTANT**: This setup has been fixed to prevent concurrent migration conflicts that were causing database corruption.

### What Was Fixed
- **Sequential Startup**: Databases start first, then web services, then workers
- **Migration Isolation**: Only web containers run migrations; workers skip them
- **Proper Dependencies**: Workers wait for web services to complete migrations
- **Environment Variables**: Added `NAUTOBOT_SKIP_STARTUP_MIGRATIONS=true` to worker containers

### How It Works Now
1. **Phase 1**: Start databases and Redis
2. **Phase 2**: Start web services (NetBox + Nautobot) - these run migrations
3. **Phase 3**: Wait for web services to be ready (migrations complete)
4. **Phase 4**: Start worker services (no migration conflicts)

## Troubleshooting

### Common Issues

1. **Nautobot Migration Conflicts** (FIXED):
   - **Error**: `duplicate key value violates unique constraint` or `column already exists`
   - **Cause**: Multiple containers running migrations simultaneously (RACE CONDITION)
   - **Solution**: This is now fixed with sequential startup - no manual intervention needed
   - **If you still see this**: Run `./cleanup.sh --db` and `./start.sh --clean`

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
- **`cleanup.sh`**: Comprehensive cleanup utility with multiple options (project-specific)
- **`nuclear-cleanup.sh`**: Complete Docker system cleanup (removes ALL Docker resources)
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
