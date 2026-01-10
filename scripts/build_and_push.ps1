$acrName = "int20h2026acrstaging"
$registryUrl = "$acrName.azurecr.io"
$imageName = "backend"
$tag = "latest"
$fullImageName = "$registryUrl/${imageName}:${tag}"

# Ensure we are in the project root
Push-Location "$PSScriptRoot/.."

try {
    Write-Host "Logging into Azure Container Registry ($acrName)..."
    az acr login --name $acrName
    if ($LASTEXITCODE -ne 0) { throw "Login failed" }

    Write-Host "Building Docker image ($fullImageName)..."
    docker build -t $fullImageName .
    if ($LASTEXITCODE -ne 0) { throw "Build failed" }

    Write-Host "Pushing Docker image..."
    docker push $fullImageName
    if ($LASTEXITCODE -ne 0) { throw "Push failed" }

    Write-Host "Successfully built and pushed $fullImageName"
}
catch {
    Write-Error "Error: $_"
}
finally {
    Pop-Location
}
