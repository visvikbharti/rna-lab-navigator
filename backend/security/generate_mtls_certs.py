#!/usr/bin/env python
"""
Certificate generation script for mTLS between Django and Weaviate.
This script generates:
1. A Certificate Authority (CA) certificate
2. Server certificate for Weaviate
3. Client certificate for Django

Usage:
    python generate_mtls_certs.py [--output-dir ./certs]

Requirements:
    pip install cryptography

Note: For production, use proper certificate management solutions and securely store private keys.
"""

import argparse
import datetime
import os
import uuid
from pathlib import Path

try:
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID
except ImportError:
    print("Error: This script requires the 'cryptography' package.")
    print("Install it with: pip install cryptography")
    exit(1)


def generate_private_key():
    """Generate an RSA private key."""
    return rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )


def generate_ca_cert(private_key):
    """Generate a self-signed CA certificate."""
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "IN"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Delhi"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "New Delhi"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "RNA Lab Navigator CA"),
        x509.NameAttribute(NameOID.COMMON_NAME, "RNA Lab Navigator Root CA"),
    ])

    return x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow()
    ).not_valid_after(
        # CA certificate valid for 10 years
        datetime.datetime.utcnow() + datetime.timedelta(days=3650)
    ).add_extension(
        x509.BasicConstraints(ca=True, path_length=None), critical=True
    ).add_extension(
        x509.KeyUsage(
            digital_signature=True,
            content_commitment=False,
            key_encipherment=False,
            data_encipherment=False,
            key_agreement=False,
            key_cert_sign=True,
            crl_sign=True,
            encipher_only=False,
            decipher_only=False
        ), critical=True
    ).sign(private_key, hashes.SHA256(), default_backend())


def generate_cert(private_key, ca_cert, ca_key, common_name, is_server=False):
    """Generate a certificate signed by our CA."""
    subject = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "IN"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Delhi"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "New Delhi"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "RNA Lab Navigator"),
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
    ])

    # Certificate is valid for 1 year
    valid_from = datetime.datetime.utcnow()
    valid_to = valid_from + datetime.timedelta(days=365)

    builder = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        ca_cert.subject
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        valid_from
    ).not_valid_after(
        valid_to
    )

    # Add Subject Alternative Names (SANs)
    san = [x509.DNSName("localhost")]
    
    if is_server:
        # For server certificate, add additional SANs
        san.extend([
            x509.DNSName("weaviate"),
            x509.DNSName("weaviate.local"),
            x509.DNSName("weaviate.rna-lab-navigator.internal"),
            x509.IPAddress(x509.IPv4Address("127.0.0.1")),
        ])
    else:
        # For client certificate, add client-specific SANs
        san.extend([
            x509.DNSName("django"),
            x509.DNSName("django.local"),
            x509.DNSName("api"),
            x509.IPAddress(x509.IPv4Address("127.0.0.1")),
        ])
    
    builder = builder.add_extension(
        x509.SubjectAlternativeName(san), critical=False
    )

    # Key usage for both client and server certificates
    builder = builder.add_extension(
        x509.KeyUsage(
            digital_signature=True,
            content_commitment=False,
            key_encipherment=True,
            data_encipherment=False,
            key_agreement=False,
            key_cert_sign=False,
            crl_sign=False,
            encipher_only=False,
            decipher_only=False
        ), critical=True
    )

    # Extended key usage differ between client and server certificates
    extended_usages = []
    if is_server:
        extended_usages.append(x509.oid.ExtendedKeyUsageOID.SERVER_AUTH)
    else:
        extended_usages.append(x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH)
    
    builder = builder.add_extension(
        x509.ExtendedKeyUsage(extended_usages), critical=False
    )

    return builder.sign(ca_key, hashes.SHA256(), default_backend())


def save_private_key(private_key, path):
    """Save a private key to a file."""
    with open(path, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))


def save_certificate(certificate, path):
    """Save a certificate to a file."""
    with open(path, "wb") as f:
        f.write(certificate.public_bytes(serialization.Encoding.PEM))


def create_mtls_certificates(output_dir):
    """Create all necessary mTLS certificates."""
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Generating certificates in {output_dir}...")
    
    # Generate CA
    ca_key = generate_private_key()
    ca_cert = generate_ca_cert(ca_key)
    save_private_key(ca_key, os.path.join(output_dir, "ca-key.pem"))
    save_certificate(ca_cert, os.path.join(output_dir, "ca-cert.pem"))
    print("✅ CA certificate generated")
    
    # Generate server (Weaviate) certificate
    server_key = generate_private_key()
    server_cert = generate_cert(server_key, ca_cert, ca_key, "weaviate", is_server=True)
    save_private_key(server_key, os.path.join(output_dir, "server-key.pem"))
    save_certificate(server_cert, os.path.join(output_dir, "server-cert.pem"))
    print("✅ Server certificate generated")
    
    # Generate client (Django) certificate
    client_key = generate_private_key()
    client_cert = generate_cert(client_key, ca_cert, ca_key, "django-client", is_server=False)
    save_private_key(client_key, os.path.join(output_dir, "client-key.pem"))
    save_certificate(client_cert, os.path.join(output_dir, "client-cert.pem"))
    print("✅ Client certificate generated")
    
    # Generate .env-compatible output for easy configuration
    env_file = os.path.join(output_dir, "mtls.env")
    with open(env_file, "w") as f:
        f.write(f"# mTLS Configuration for RNA Lab Navigator\n")
        f.write(f"# Generated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"WEAVIATE_TLS_ENABLED=True\n")
        f.write(f"WEAVIATE_CLIENT_CERT={os.path.abspath(os.path.join(output_dir, 'client-cert.pem'))}\n")
        f.write(f"WEAVIATE_CLIENT_KEY={os.path.abspath(os.path.join(output_dir, 'client-key.pem'))}\n")
        f.write(f"WEAVIATE_CA_CERT={os.path.abspath(os.path.join(output_dir, 'ca-cert.pem'))}\n")
    
    print(f"✅ Environment variables written to {env_file}")
    print("\nInstructions for Docker Compose:")
    print("1. Add these environment variables to docker-compose.yml for Weaviate:")
    print("```")
    print("  weaviate:")
    print("    environment:")
    print("      - ENABLE_MTLS=true")
    print(f"      - MTLS_CA_FILE=/certs/ca-cert.pem")
    print(f"      - MTLS_SERVER_CERT_FILE=/certs/server-cert.pem")
    print(f"      - MTLS_SERVER_KEY_FILE=/certs/server-key.pem")
    print("    volumes:")
    print(f"      - {os.path.abspath(output_dir)}:/certs")
    print("```")
    print("\n2. Configure your Django application with these environment variables:")
    print("```")
    print(f"WEAVIATE_TLS_ENABLED=True")
    print(f"WEAVIATE_CLIENT_CERT={os.path.abspath(os.path.join(output_dir, 'client-cert.pem'))}")
    print(f"WEAVIATE_CLIENT_KEY={os.path.abspath(os.path.join(output_dir, 'client-key.pem'))}")
    print(f"WEAVIATE_CA_CERT={os.path.abspath(os.path.join(output_dir, 'ca-cert.pem'))}")
    print("```")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate mTLS certificates for RNA Lab Navigator")
    parser.add_argument("--output-dir", default="./certs", help="Directory to save certificates")
    args = parser.parse_args()
    
    create_mtls_certificates(args.output_dir)