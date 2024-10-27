from flask import Flask, request, send_file, jsonify, render_template
import subprocess
import io
import time
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'random_string'
app.config['MAX_CONTENT_LENGTH'] = 100000 * 1024 * 1024

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/encrypt', methods=['POST'])
def encrypt_route():
    file = request.files['file']
    delay = request.form.get('time', '10m')  # Default delay if not provided

    # Save uploaded file temporarily
    input_filename = 'temp_input_file'
    output_filename = 'encrypted_file.tenc'
    file.save(input_filename)

    try:
        # Run tle command for encryption
        subprocess.run(
            ['tle', '--encrypt', '-D', delay, '-o', output_filename, input_filename],
            check=True
        )

        # Read the encrypted file to return it
        with open(output_filename, 'rb') as encrypted_file:
            encrypted_data = encrypted_file.read()

        # Send encrypted file with .tenc extension
        return send_file(
            io.BytesIO(encrypted_data),
            as_attachment=True,
            download_name=f'{file.filename}.tenc'
        )

    finally:
        # Clean up temporary files
        os.remove(input_filename)
        os.remove(output_filename)

@app.route('/decrypt', methods=['POST'])
def decrypt_route():
    file = request.files['file']

    # Save uploaded encrypted file temporarily
    input_filename = 'temp_encrypted_file.tenc'
    output_filename = 'decrypted_file'
    file.save(input_filename)

    try:
        # Run tle command for decryption
        result = subprocess.run(
            ['tle', '--decrypt', '-o', output_filename, input_filename],
            capture_output=True,
            text=True
        )

        # Check for errors in decryption process
        if result.returncode != 0:
            return jsonify({"error": result.stderr.strip()}), 403

        # Read the decrypted file to return it
        with open(output_filename, 'rb') as decrypted_file:
            decrypted_data = decrypted_file.read()

        # Determine the original filename and create the new filename
        original_filename = file.filename
        if original_filename.endswith('.tenc'):
            decrypted_filename = f'decrypted_{original_filename[:-5]}'
        else:
            decrypted_filename = f'decrypted_{original_filename}'

        # Send decrypted file
        return send_file(
            io.BytesIO(decrypted_data),
            as_attachment=True,
            download_name=decrypted_filename
        )

    finally:
        # Clean up temporary files
        os.remove(input_filename)
        os.remove(output_filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)