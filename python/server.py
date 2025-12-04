from flask import Flask, jsonify, request, send_from_directory
import os
import json
from datetime import datetime

app = Flask(__name__)

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route('/')
def index():
    """Serve the main HTML viewer"""
    return send_from_directory(BASE_DIR, 'jobs_viewer.html')

@app.route('/list_json_files')
def list_json_files():
    """Return list of all JSON files in the current directory"""
    try:
        # Get all files in the directory
        all_files = os.listdir(BASE_DIR)
        
        # Filter for JSON files, excluding backups
        json_files = [
            f for f in all_files 
            if f.endswith('.json') and not f.endswith('.bak')
        ]
        
        # Sort by modification time (newest first)
        json_files.sort(
            key=lambda f: os.path.getmtime(os.path.join(BASE_DIR, f)), 
            reverse=True
        )
        
        print(f"Found {len(json_files)} JSON files: {json_files}")
        return jsonify(json_files)
    except Exception as e:
        print(f"Error listing files: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/<path:filename>')
def serve_file(filename):
    """Serve static files (JSON, HTML, etc.)"""
    try:
        # Security check: don't allow directory traversal
        if '..' in filename or filename.startswith('/'):
            return jsonify({'error': 'Invalid filename'}), 400
        
        return send_from_directory(BASE_DIR, filename)
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/save_jobs', methods=['POST'])
def save_jobs():
    """Save jobs to linkedin_jobs.json with backup"""
    try:
        jobs = request.json
        
        if not isinstance(jobs, list):
            return jsonify({'ok': False, 'error': 'Expected a list of jobs'}), 400
        
        output_file = os.path.join(BASE_DIR, 'linkedin_jobs.json')
        backup_file = os.path.join(BASE_DIR, 'linkedin_jobs.json.bak')
        
        # Create backup if file exists
        if os.path.exists(output_file):
            # Add timestamp to backup
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_with_time = os.path.join(BASE_DIR, f'linkedin_jobs_{timestamp}.json.bak')
            
            # Copy to both regular backup and timestamped backup
            with open(output_file, 'r', encoding='utf-8') as f:
                backup_data = f.read()
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(backup_data)
            with open(backup_with_time, 'w', encoding='utf-8') as f:
                f.write(backup_data)
            
            print(f"Created backup: {backup_file} and {backup_with_time}")
        
        # Save new data
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(jobs, f, indent=2, ensure_ascii=False)
        
        print(f"Saved {len(jobs)} jobs to {output_file}")
        return jsonify({'ok': True, 'jobs_saved': len(jobs)})
    
    except Exception as e:
        print(f"Error saving jobs: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print(f"Starting server...")
    print(f"Base directory: {BASE_DIR}")
    print(f"Open your browser to: http://localhost:5000")
    print(f"Press Ctrl+C to stop the server")
    app.run(debug=True, port=5000, host='0.0.0.0')