# Create monitoring structure
Write-Host "Creating monitoring folders..." -ForegroundColor Green
New-Item -Path "pipelines\monitoring" -ItemType Directory -Force | Out-Null
New-Item -Path "pipelines\quality" -ItemType Directory -Force | Out-Null

# Create __init__ files
New-Item -Path "pipelines\monitoring\__init__.py" -ItemType File -Force | Out-Null
New-Item -Path "pipelines\quality\__init__.py" -ItemType File -Force | Out-Null

# Create placeholder files
New-Item -Path "pipelines\monitoring\email_alerts.py" -ItemType File -Force | Out-Null
New-Item -Path "pipelines\quality\data_quality_checker.py" -ItemType File -Force | Out-Null
New-Item -Path "README.md" -ItemType File -Force | Out-Null

Write-Host "✓ Folder structure created!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Open 'pipelines\monitoring\email_alerts.py' and paste the code"
Write-Host "2. Open 'pipelines\quality\data_quality_checker.py' and paste the code"
Write-Host "3. Open 'README.md' and paste the content"
Write-Host ""
Write-Host "Files created:" -ForegroundColor Cyan
Get-ChildItem -Path "pipelines\monitoring\"
Get-ChildItem -Path "pipelines\quality\"