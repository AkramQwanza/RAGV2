# Installer Chocolatey si ce n'est pas déjà fait
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))

# Installer Tesseract OCR
choco install tesseract -y

# Installer le pack de langue française pour Tesseract
$tesseractPath = "C:\Program Files\Tesseract-OCR"
$langPath = "$tesseractPath\tessdata"

# Créer le dossier tessdata s'il n'existe pas
if (-not (Test-Path $langPath)) {
    New-Item -ItemType Directory -Path $langPath
}

# Télécharger le pack de langue française
$frenchLangUrl = "https://github.com/tesseract-ocr/tessdata/raw/main/fra.traineddata"
$frenchLangFile = "$langPath\fra.traineddata"

if (-not (Test-Path $frenchLangFile)) {
    Invoke-WebRequest -Uri $frenchLangUrl -OutFile $frenchLangFile
}

Write-Host "Installation terminée. Tesseract OCR est prêt à être utilisé." 