# Write requirements-semantic.txt
content = """# Semantic environment requirements for .venv-semantic
# Install alongside requirements.txt in a separate isolated environment.
# These packages require torch and have heavy dependencies; isolate them
# to avoid conflicts with the main application environment.
torch>=2.0.0
scipy>=1.11.0
pyproj>=3.5.0
trimesh>=4.0.0
numpy>=1.23.0
"""
with open('requirements-semantic.txt', 'w') as f:
    f.write(content)
print("Created requirements-semantic.txt")
