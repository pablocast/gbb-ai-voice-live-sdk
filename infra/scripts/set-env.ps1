# PowerShell script to set environment variables for local development based on Bicep outputs
# Usage: .\scripts\set-env.ps1

Write-Host "Getting environment variables from azd..."

# Get outputs from azd env get-values
$azdEnvValues = azd env get-values

# Parse function to extract value from azd output
function Get-AzdValue($envValues, $key) {
    $line = $envValues | Where-Object { $_ -match "^$key=" }
    if ($line) {
        return $line.Split('=', 2)[1].Trim('"')
    }
    return ""
}

# Create .env file content
$envContent = @"
# Environment variables
# Generated from Bicep deployment outputs

# ---- AOAI/LLM/Embedding Model Variables ----
AZURE_OPENAI_DEPLOYMENT_NAME=$(Get-AzdValue $azdEnvValues "azureOpenAiDeploymentName")
AZURE_OPENAI_EMBEDDING_NAME=$(Get-AzdValue $azdEnvValues "azureEmbeddingDeploymentName")
AZURE_VOICELIVE_API_KEY=$(Get-AzdValue $azdEnvValues "azureVoiceLiveApiKey")
AZURE_VOICELIVE_ENDPOINT=$(Get-AzdValue $azdEnvValues "azureVoiceLiveEndpoint")

# ---- Azure Search Variables ----
AZURE_SEARCH_INDEX=$(Get-AzdValue $azdEnvValues "azureSearchIndex")
AZURE_SEARCH_ENDPOINT=$(Get-AzdValue $azdEnvValues "azureSearchEndpoint")

# ---- Azure OpenAI Additional Variables ----
AZURE_OPENAI_ENDPOINT=$(Get-AzdValue $azdEnvValues "azureOpenAiEndpoint")
AZURE_OPENAI_EMBEDDING_MODEL=$(Get-AzdValue $azdEnvValues "azureOpenAiEmbeddingModel")

# ---- Azure Storage Variables ----
AZURE_STORAGE_ENDPOINT=$(Get-AzdValue $azdEnvValues "azureStorageEndpoint")
AZURE_STORAGE_CONNECTION_STRING=$(Get-AzdValue $azdEnvValues "azureStorageConnectionString")
AZURE_STORAGE_CONTAINER=$(Get-AzdValue $azdEnvValues "azureStorageContainer")
"@

# Write .env file
$envContent | Out-File -FilePath ".env" -Encoding UTF8

Write-Host ".env file created successfully with deployment outputs!"
Write-Host "You can now use 'docker-compose up' to test your container locally."