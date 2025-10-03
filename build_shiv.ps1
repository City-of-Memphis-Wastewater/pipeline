# build_shiv.ps1 

# Find the most recently created .whl file in the dist directory
$latestWheel = Get-ChildItem -Path "dist/*.whl" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $latestWheel) {
    Write-Host "Error: No wheel file (.whl) found in the 'dist' directory."
    Write-Host "Please run 'poetry build' first."
    exit 1
}

$wheelPath = $latestWheel.FullName
Write-Host "Building .pyz from wheel: $wheelPath"
# Setting bootstrap cache to: $cacheDir (Removed, as --bootstrap-cache flag caused an error.)

# The wheel path is passed as a positional argument.
# We check $LASTEXITCODE after the shiv command to ensure the success message is conditional.
Write-Host "Attempting to build .pyz..."

shiv $wheelPath `
     -e pipeline.cli:app `
     -o dist/pipeline.pyz `
     -p "/usr/bin/env python3"

if ($LASTEXITCODE -eq 0) {
    Write-Host "Successfully created dist/pipeline.pyz"
} else {
    Write-Host "Error: shiv failed to create pipeline.pyz (Exit Code: $LASTEXITCODE). Review the output above for the cause."
    exit 1
}
