# LaxyFile Chocolatey Install Script

$ErrorActionPreference = 'Stop'

$packageName = 'laxyfile'
$toolsDir = "$(Split-Path -parent $MyInvocation.MyCommand.Definition)"
$url = 'https://github.com/swadhinbiswas/laxyfile/releases/download/v1.0.0/laxyfile-1.0.0-windows-standalone.exe'
$checksum = 'PLACEHOLDER_CHECKSUM'
$checksumType = 'sha256'

# Download and install the standalone executable
$packageArgs = @{
  packageName   = $packageName
  unzipLocation = $toolsDir
  fileType      = 'exe'
  url           = $url
  silentArgs    = '/S'
  validExitCodes= @(0)
  softwareName  = 'LaxyFile*'
  checksum      = $checksum
  checksumType  = $checksumType
}

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python found: $pythonVersion"

    # Install via pip if Python is available
    Write-Host "Installing LaxyFile via pip..."
    & python -m pip install laxyfile

    if ($LASTEXITCODE -eq 0) {
        Write-Host "LaxyFile installed successfully via pip!"

        # Create a batch file for easy access
        $batchContent = @"
@echo off
python -m laxyfile %*
"@
        $batchPath = Join-Path $env:ChocolateyInstall "bin\laxyfile.bat"
        Set-Content -Path $batchPath -Value $batchContent

        Write-Host "Created launcher at: $batchPath"
    } else {
        Write-Warning "pip installation failed, falling back to standalone executable"
        Install-ChocolateyPackage @packageArgs
    }

} catch {
    Write-Warning "Python not found, installing standalone executable"
    Install-ChocolateyPackage @packageArgs
}

# Post-installation message
Write-Host ""
Write-Host "🎉 LaxyFile has been installed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "To get started:" -ForegroundColor Yellow
Write-Host "  1. Open a new terminal/command prompt"
Write-Host "  2. Run 'laxyfile' to start the file manager"
Write-Host ""
Write-Host "For AI features:" -ForegroundColor Yellow
Write-Host "  1. Get a free API key from https://openrouter.ai/"
Write-Host "  2. Set environment variable: set OPENROUTER_API_KEY=your-key"
Write-Host "  3. Restart your terminal and run 'laxyfile'"
Write-Host ""
Write-Host "Documentation: https://github.com/swadhinbiswas/laxyfile/wiki" -ForegroundColor Cyan
Write-Host "Issues: https://github.com/swadhinbiswas/laxyfile/issues" -ForegroundColor Cyan