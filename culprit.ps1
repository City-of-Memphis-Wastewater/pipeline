Get-ChildItem -Recurse -Include *.py -ErrorAction SilentlyContinue | ForEach-Object {
    try {
        Get-Content $_.FullName -Encoding UTF8 | Out-Null
    } catch {
        Write-Host "Problematic file: $($_.FullName)"
    }
}
