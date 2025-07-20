# Fleet Management PWA - Preview Environment

This document explains how to set up and use the preview environment for safe testing.

## Quick Start

### Option 1: Local Docker Preview

```bash
# Setup and start preview environment
./scripts/setup-preview.sh

# Test the preview environment
python test_preview.py

# Access the application
open http://localhost:5001
```

### Option 2: Render Preview Deploy

1. Create a new Render service using `render-preview.yaml`
2. Set the branch to `preview`
3. Deploy and test

## Preview Environment Features

### Separate Infrastructure
- **Database**: Independent preview database
- **Redis**: Separate Redis instance  
- **Ports**: Different ports (5001, 5433, 6380)
- **Environment**: Development mode with debug enabled

### Relaxed Rate Limiting
```python
# Preview has more generous limits
default_limits=["5000 per day", "1000 per hour", "100 per minute"]
```

### Debug Features
- Flask debug mode enabled
- Detailed error pages
- Development logging
- CORS relaxed for testing

## Commands

### Start Preview Environment
```bash
docker-compose -f docker-compose.preview.yml up -d
```

### View Logs
```bash
docker-compose -f docker-compose.preview.yml logs -f web-preview
```

### Stop Preview Environment
```bash
docker-compose -f docker-compose.preview.yml down
```

### Test Preview Environment
```bash
# Test local preview
python test_preview.py http://localhost:5001

# Test Render preview
python test_preview.py https://your-preview-app.onrender.com
```

### Database Access
```bash
# Connect to preview database
psql postgresql://preview:preview123@localhost:5433/fleet_preview
```

### Shell Access
```bash
# Get shell in preview container
docker-compose -f docker-compose.preview.yml exec web-preview bash
```

## Environment Variables

| Variable | Preview Value | Description |
|----------|---------------|-------------|
| FLASK_ENV | development | Enables debug mode |
| FLASK_DEBUG | 1 | Shows detailed errors |
| PREVIEW_MODE | true | Identifies preview env |
| DATABASE_URL | preview db | Separate database |
| REDIS_URL | preview redis | Separate cache |

## Testing Workflow

1. **Start Preview**: `./scripts/setup-preview.sh`
2. **Test Changes**: Make code changes and test on port 5001
3. **Run Tests**: `python test_preview.py`
4. **Debug**: Check logs with docker-compose logs
5. **Deploy**: When ready, merge to main for production

## Autonomous Testing

The preview environment works with the autonomous testing system:

```bash
# Run autonomous testing against preview
python automated_fix_loop.py --target http://localhost:5001
```

## Benefits

- **Safe Testing**: No impact on production
- **Real Environment**: Full stack including database
- **Easy Reset**: `docker-compose down -v` clears all data
- **Parallel Development**: Multiple developers can have separate previews
- **CI/CD Ready**: Can be integrated into pull request workflows

## Troubleshooting

### Port Conflicts
If ports are already in use, modify `docker-compose.preview.yml`:
```yaml
ports:
  - "5002:5000"  # Change 5001 to 5002
```

### Database Issues
Reset the preview database:
```bash
docker-compose -f docker-compose.preview.yml down -v
docker-compose -f docker-compose.preview.yml up -d
```

### Performance Issues
Increase resource limits in docker-compose.preview.yml:
```yaml
deploy:
  resources:
    limits:
      memory: 1G
      cpus: '0.5'
```