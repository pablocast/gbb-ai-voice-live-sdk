#!/bin/bash
# This script sets environment variables for local development based on Bicep outputs
# Usage: ./scripts/set-env.sh

# Get outputs from azd env get-values (assumes azd deployment)
echo "Getting environment variables from azd..."

# Create .env file with Bicep outputs
cat > .env << EOF
# Environment variables
# Generated from Bicep deployment outputs

# Get azd env values once to avoid multiple calls
AZD_VALUES=$(azd env get-values --output json)

# ---- AOAI/LLM/Embedding Model Variables ----
AZURE_OPENAI_DEPLOYMENT_NAME=$(echo "$AZD_VALUES" | jq -r '.azureOpenAiDeploymentName')
AZURE_OPENAI_EMBEDDING_NAME=$(echo "$AZD_VALUES" | jq -r '.azureEmbeddingDeploymentName')
AZURE_VOICELIVE_API_KEY=$(echo "$AZD_VALUES" | jq -r '.azureVoiceLiveApiKey')
AZURE_VOICELIVE_ENDPOINT=$(echo "$AZD_VALUES" | jq -r '.azureVoiceLiveEndpoint')

# ---- Azure Search Variables ----
AZURE_SEARCH_INDEX=$(echo "$AZD_VALUES" | jq -r '.azureSearchIndex')
AZURE_SEARCH_ENDPOINT=$(echo "$AZD_VALUES" | jq -r '.azureSearchEndpoint')

# ---- Azure OpenAI Additional Variables ----
AZURE_OPENAI_ENDPOINT=$(echo "$AZD_VALUES" | jq -r '.azureOpenAiEndpoint')
AZURE_OPENAI_EMBEDDING_MODEL=$(echo "$AZD_VALUES" | jq -r '.azureOpenAiEmbeddingModel')

# ---- Azure Storage Variables ----
AZURE_STORAGE_ENDPOINT=$(echo "$AZD_VALUES" | jq -r '.azureStorageEndpoint')
AZURE_STORAGE_CONNECTION_STRING=$(echo "$AZD_VALUES" | jq -r '.azureStorageConnectionString')
AZURE_STORAGE_CONTAINER=$(echo "$AZD_VALUES" | jq -r '.azureStorageContainer')
EOF

echo ".env file created successfully with deployment outputs!"
echo "You can now use 'docker-compose up' to test your container locally."