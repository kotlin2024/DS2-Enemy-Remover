$ErrorActionPreference = 'Stop'
$trainerRoot = $PSScriptRoot
$pythonExe = Join-Path $trainerRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) { throw 'Create .venv and install requirements-build.txt first. See README.md.' }
Push-Location $trainerRoot
try {
    & $pythonExe -m unittest test_removal test_ai_payload test_lockon_payload test_controller -v
    if ($LASTEXITCODE -ne 0) { throw 'Memory tests failed' }
    & $pythonExe -m PyInstaller --noconfirm --clean --onefile --noupx --windowed --name DS2EnemySelector-Comfort --collect-data customtkinter --icon 'assets\app-icon.ico' --add-data 'assets;assets' --add-data 'catalog.json;.' --distpath release --workpath build app.py
    if ($LASTEXITCODE -ne 0) { throw 'Build failed' }
    $releaseRoot = Join-Path $trainerRoot 'release'
    $docs = @('사용안내.md','필터 조사 및 배포 안내.md','THIRD_PARTY_NOTICES.txt','ART_SOURCES.md')
    foreach ($doc in $docs) { Copy-Item -LiteralPath (Join-Path $trainerRoot $doc) -Destination (Join-Path $releaseRoot $doc) -Force }
    $releaseHash = (Get-FileHash -LiteralPath (Join-Path $releaseRoot 'DS2EnemySelector-Comfort.exe') -Algorithm SHA256).Hash
    Set-Content -LiteralPath (Join-Path $releaseRoot 'SHA256-Comfort.txt') -Value "$releaseHash  DS2EnemySelector-Comfort.exe" -Encoding ASCII
    $packageFiles = @('DS2EnemySelector-Comfort.exe','SHA256-Comfort.txt') + $docs
    $packagePaths = $packageFiles | ForEach-Object { Join-Path $releaseRoot $_ }
    Compress-Archive -LiteralPath $packagePaths -DestinationPath (Join-Path $releaseRoot 'DS2EnemySelector-Comfort.zip') -Force
} finally { Pop-Location }
