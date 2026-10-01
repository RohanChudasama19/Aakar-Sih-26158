# The workspace route returns 404 because this is a React SPA with client-side routing.
# Static file serving catches only '/' - hash routes like /#/workspace/... would work.
# Let's check how the app's router is configured.

import requests

# Try with hash routing
r1 = requests.get("http://127.0.0.1:8000/#/workspace/mars_hkairport01_quality")
print(f"/#/workspace/mars_hkairport01_quality: {r1.status_code}")

# Try root - SPA should serve index.html for all unknown paths
r2 = requests.get("http://127.0.0.1:8000/workspace/mars_hkairport01_quality", headers={'Accept': 'text/html'})
print(f"/workspace/mars: {r2.status_code}  content-type: {r2.headers.get('content-type')}")
print("Body:", r2.text[:100])
