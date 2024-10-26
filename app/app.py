from flask import Flask, request, send_file, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import secrets
import base64
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import io
import time

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://your_postgres_string'
app.config['SECRET_KEY'] = 'change_me'
app.config['MAX_CONTENT_LENGTH'] = 100000 * 1024 * 1024
db = SQLAlchemy(app)

# Database model
class EncryptionRecord(db.Model):
    __tablename__ = 'encryption_records'
    id = db.Column(db.Integer, primary_key=True)
    file_hash = db.Column(db.String(64), nullable=False, unique=True)
    key = db.Column(db.String(64), nullable=False)
    expiration_time = db.Column(db.BigInteger, nullable=False)

with app.app_context():
    db.create_all()

# Encryption key length
KEY_LENGTH = 32  # AES-256

def generate_key():
    return secrets.token_bytes(KEY_LENGTH)

def encrypt_file(data, key):
    cipher = AES.new(key, AES.MODE_CBC)
    iv = cipher.iv
    encrypted_data = cipher.encrypt(pad(data, AES.block_size))
    return iv + encrypted_data

def decrypt_file(data, key):
    iv = data[:AES.block_size]
    encrypted_data = data[AES.block_size:]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(encrypted_data), AES.block_size)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/encrypt', methods=['POST'])
def encrypt_route():
    file = request.files['file']
    delay = int(request.form.get('time', 0))
    expiration_time_ms = int((time.time() + delay) * 1000)

    # Generate and store encryption key
    key = generate_key()
    file_data = file.read()
    encrypted_data = encrypt_file(file_data, key)

    # Generate hash of encrypted data
    file_hash = hashlib.sha256(encrypted_data).hexdigest()

    # Save record in database
    record = EncryptionRecord(
        file_hash=file_hash,
        key=base64.b64encode(key).decode(),
        expiration_time=expiration_time_ms
    )
    db.session.add(record)
    db.session.commit()

    # Create the new filename with .tenc extension
    new_filename = f'{file.filename}.tenc'

    # Send encrypted file
    return send_file(
        io.BytesIO(encrypted_data),
        as_attachment=True,
        download_name=new_filename
    )

@app.route('/decrypt', methods=['POST'])
def decrypt_route():
    file = request.files['file']
    encrypted_data = file.read()

    # Generate hash of the uploaded encrypted file
    file_hash = hashlib.sha256(encrypted_data).hexdigest()
    record = EncryptionRecord.query.filter_by(file_hash=file_hash).first()

    if not record:
        return jsonify({"error": "Record not found"}), 404

    current_time_ms = int(time.time() * 1000)
    if current_time_ms < record.expiration_time:
        remaining_time_ms = record.expiration_time - current_time_ms
        remaining_seconds = remaining_time_ms // 1000
        return jsonify({"error": f"Cannot decrypt yet. Try again in {remaining_seconds} seconds"}), 403

    # Decrypt file content
    key = base64.b64decode(record.key)
    decrypted_data = decrypt_file(encrypted_data, key)

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)