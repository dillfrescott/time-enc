from flask import Flask, request, send_file, jsonify, render_template
import subprocess
import io
import time
import os
import re
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = 'random_string'
app.config['MAX_CONTENT_LENGTH'] = 100000 * 1024 * 1024

# Use current time as reference instead of drand genesis
def get_current_round():
    """Get current round number based on current time"""
    current_time = int(time.time())
    return current_time // 3

def round_to_time(round_number):
    """Convert a round number to Unix timestamp"""
    return round_number * 3

def parse_error_message(error_text):
    """Parse the error message to extract round numbers and convert to time"""
    match = re.search(r'expected round (\d+) > (\d+) current round', error_text)
    if match:
        expected_round = int(match.group(1))
        current_round = int(match.group(2))
        
        # Convert rounds to timestamps based on current time
        current_time = int(time.time())
        base_time = current_time - (current_round * 3)
        
        unlock_time = base_time + (expected_round * 3)
        
        # Calculate time difference
        time_diff = unlock_time - current_time
        
        return {
            "error": "File is time-locked",
            "unlock_timestamp": unlock_time,
            "current_timestamp": current_time,
            "seconds_remaining": time_diff
        }
    return {"error": error_text}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/encrypt', methods=['POST'])
def encrypt_route():
    file = request.files['file']
    delay = request.form.get('time', '10m')
    
    # Convert years to an equivalent duration that tle can understand
    if delay.endswith('y'):
        try:
            years = int(delay[:-1])
            # Convert years to days (approximate, not accounting for leap years)
            days = years * 365
            delay = f"{days}d"
        except ValueError:
            return jsonify({"error": "Invalid year format"}), 400
    
    input_filename = 'temp_input_file'
    output_filename = 'encrypted_file.tenc'
    
    file.save(input_filename)
    try:
        subprocess.run(
            ['tle', '--encrypt', '-D', delay, '-o', output_filename, input_filename],
            check=True
        )
        with open(output_filename, 'rb') as encrypted_file:
            encrypted_data = encrypted_file.read()
        return send_file(
            io.BytesIO(encrypted_data),
            as_attachment=True,
            download_name=f'{file.filename}.tenc'
        )
    except subprocess.CalledProcessError as e:
        return jsonify({"error": "Encryption failed"}), 400
    finally:
        # Clean up temporary files
        if os.path.exists(input_filename):
            os.remove(input_filename)
        if os.path.exists(output_filename):
            os.remove(output_filename)

@app.route('/decrypt', methods=['POST'])
def decrypt_route():
    file = request.files['file']
    input_filename = 'temp_encrypted_file.tenc'
    output_filename = 'decrypted_file'
    
    file.save(input_filename)
    try:
        result = subprocess.run(
            ['tle', '--decrypt', '-o', output_filename, input_filename],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            error_info = parse_error_message(result.stderr.strip())
            return jsonify(error_info), 403
            
        with open(output_filename, 'rb') as decrypted_file:
            decrypted_data = decrypted_file.read()
            
        original_filename = file.filename
        if original_filename.endswith('.tenc'):
            decrypted_filename = f'decrypted_{original_filename[:-5]}'
        else:
            decrypted_filename = f'decrypted_{original_filename}'
            
        return send_file(
            io.BytesIO(decrypted_data),
            as_attachment=True,
            download_name=decrypted_filename
        )
    finally:
        # Clean up temporary files
        if os.path.exists(input_filename):
            os.remove(input_filename)
        if os.path.exists(output_filename):
            os.remove(output_filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)