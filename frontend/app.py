import streamlit as st
import sys
import os

# Add the project root to the path to import config
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.settings import get_settings

# Backend API base URL
API_BASE = "http://localhost:8001/api/upload"

# Get settings
settings = get_settings()

st.title("📤 File Upload")

st.markdown("""
Upload large files to Azure Blob Storage using chunked uploads.
The file will be split into chunks and uploaded progressively from your browser.
""")

# Load modular components
static_dir = os.path.join(os.path.dirname(__file__), 'static')

# Read CSS
with open(os.path.join(static_dir, 'styles.css'), 'r') as f:
    css_content = f.read()

# Read HTML template
with open(os.path.join(static_dir, 'template.html'), 'r') as f:
    html_template = f.read()

# Read and process JavaScript
with open(os.path.join(static_dir, 'script.js'), 'r') as f:
    js_content = f.read()

# Replace template variables in JavaScript
js_content = js_content.replace('{{API_BASE}}', API_BASE)
js_content = js_content.replace('{{CHUNK_SIZE}}', str(settings.chunk_size))

# Combine everything into final HTML
html_content = f"""
<style>
{css_content}
</style>
{html_template}
<script>
{js_content}
</script>
"""

st.components.v1.html(html_content, height=325)