# Generate Self-Signed SSL Certificate for BOQMate
# This script creates a self-signed certificate for local development

Write-Host "Generating SSL certificates for BOQMate..." -ForegroundColor Green

# Create SSL directory if it doesn't exist
if (!(Test-Path "ssl")) {
    New-Item -ItemType Directory -Path "ssl" -Force
    Write-Host "Created ssl directory" -ForegroundColor Yellow
}

# Generate private key
Write-Host "Generating private key..." -ForegroundColor Yellow
$privateKeyPath = "ssl\private.key"
$certPath = "ssl\certificate.crt"

# Use .NET to generate self-signed certificate
try {
    $cert = New-SelfSignedCertificate -DnsName "localhost", "127.0.0.1" -CertStoreLocation "Cert:\LocalMachine\My" -NotAfter (Get-Date).AddYears(1) -KeyAlgorithm RSA -KeyLength 2048 -KeyUsage DigitalSignature, KeyEncipherment -Type SSLServerAuthentication
    
    # Export private key
    $cert.PrivateKey.ExportCspBlob($true) | Out-File -FilePath $privateKeyPath -Encoding ASCII
    
    # Export certificate
    $cert.Export([System.Security.Cryptography.X509Certificates.X509ContentType]::Cert) | Out-File -FilePath $certPath -Encoding ASCII
    
    Write-Host "SSL certificate generated successfully!" -ForegroundColor Green
    Write-Host "Certificate: $certPath" -ForegroundColor Cyan
    Write-Host "Private Key: $privateKeyPath" -ForegroundColor Cyan
    
} catch {
    Write-Host "Error generating certificate: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Creating placeholder files for development..." -ForegroundColor Yellow
    
    # Create placeholder files
    "-----BEGIN PRIVATE KEY-----" | Out-File -FilePath $privateKeyPath -Encoding ASCII
    "PLACEHOLDER_PRIVATE_KEY_FOR_DEVELOPMENT" | Out-File -FilePath $privateKeyPath -Append -Encoding ASCII
    "-----END PRIVATE KEY-----" | Out-File -FilePath $privateKeyPath -Append -Encoding ASCII
    
    "-----BEGIN CERTIFICATE-----" | Out-File -FilePath $certPath -Encoding ASCII
    "PLACEHOLDER_CERTIFICATE_FOR_DEVELOPMENT" | Out-File -FilePath $certPath -Append -Encoding ASCII
    "-----END CERTIFICATE-----" | Out-File -FilePath $certPath -Append -Encoding ASCII
    
    Write-Host "Placeholder SSL files created for development" -ForegroundColor Green
}

Write-Host "SSL setup complete!" -ForegroundColor Green 