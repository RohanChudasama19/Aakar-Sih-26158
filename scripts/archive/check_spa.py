# StaticFiles with html=True serves index.html for directories, but NOT for
# missing paths like /workspace/... because FastAPI matches the path literally.
# The fix is to add a catch-all route that serves index.html for any unmatched path.
# This must be added BEFORE the StaticFiles mount.

# First check if there's already a catch-all
lines = open('app/main.py', encoding='utf-8').read()
has_catchall = 'html=True' in lines
has_spa_route = 'spa' in lines.lower() or 'catch' in lines.lower() or '@app.get("/{full_path' in lines
print(f'StaticFiles html=True: {has_catchall}')
print(f'SPA catch-all: {has_spa_route}')

# Check FastAPI version for static files html behavior
import fastapi, starlette
print(f'FastAPI: {fastapi.__version__}')
print(f'Starlette: {starlette.__version__}')
