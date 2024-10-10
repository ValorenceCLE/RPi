import os
import datetime
import shutil
import ipaddress
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from core.config import settings

CERT_DIR = settings.CERT_DIR
CERT_FILE = settings.CERT_FILE
KEY_FILE = settings.KEY_FILE

def rotate_old_certs():
    # Make sure the directory exists
    if not os.path.exists(CERT_DIR):
        os.makedirs(CERT_DIR)
    
    # Rotate old certs, keeping a limited number of backups
    max_backups = 5
    cert_files = sorted([f for f in os.listdir(CERT_DIR) if f.startswith("cert_")], reverse=True)
    key_files = sorted([f for f in os.listdir(CERT_DIR) if f.startswith("key_")], reverse=True)
    
    # Remove the oldest files if we have too many
    for old_file in cert_files[max_backups -1:]:
        os.remove(os.path.join(CERT_DIR, old_file))
    for old_file in key_files[max_backups -1:]:
        os.remove(os.path.join(CERT_DIR, old_file))
        
    # Rename the existing files
    if os.path.exists(CERT_FILE):
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        shutil.move(CERT_FILE, os.path.join(CERT_DIR, f"cert_{timestamp}.pem"))
    if os.path.exists(KEY_FILE):
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        shutil.move(KEY_FILE, os.path.join(CERT_DIR, f"key_{timestamp}.pem"))
        
def generate_cert():
    rotate_old_certs()
    
    # Generate a key
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    # Generate a self-signed cert
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, u"US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"Unknown"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, u"Unknown"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Valorence"),
        x509.NameAttribute(NameOID.COMMON_NAME, u"localhost"),
    ])
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow()
    ).not_valid_after(
        datetime.datetime.utcnow() + datetime.timedelta(days=90)
    ).add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName(u"localhost"),
            x509.IPAddress(ipaddress.IPv4Address("192.168.1.2"))
        ]),
        critical=False,
    ).sign(key, hashes.SHA256(), default_backend())
    
    # Write the private key to a file
    with open(KEY_FILE, 'wb') as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))
        
    # Write the cert to a file
    with open(CERT_FILE, 'wb') as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        
def is_certificate_valid():
    if not os.path.exists(CERT_FILE) or not os.path.exists(KEY_FILE):
        return False
    
    with open(CERT_FILE, "rb") as f:
        cert_data = f.read()
        cert = x509.load_pem_x509_certificate(cert_data, default_backend())
        
        # Check if the certificate is expired
        if cert.not_valid_after_utc.replace(tzinfo=datetime.timezone.utc) <= datetime.datetime.now(datetime.timezone.utc):
            return False
    return True