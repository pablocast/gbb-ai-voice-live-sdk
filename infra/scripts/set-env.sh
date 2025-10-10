#!/bin/bash
# This script sets environment variables for local development based on Bicep outputs
# Usage: ./scripts/set-env.sh

# Get outputs from azd env get-values (assumes azd deployment)
echo "Getting environment variables from azd..."

# Create .env file with Bicep outputs
cat > .env << EOF
# Environment variables
# Generated from Bicep deployment outputs

# ---- AOAI/LLM/Embedding Model Variables ----
AZURE_OPENAI_DEPLOYMENT_NAME=$(azd env get-values --output json | jq -r '.azureOpenAiDeploymentName')
AZURE_OPENAI_EMBEDDING_NAME=$(azd env get-values --output json | jq -r '.azureEmbeddingDeploymentName')
AZURE_VOICELIVE_API_KEY=$(azd env get-values --output json | jq -r '.azureVoiceLiveApiKey')
AZURE_VOICELIVE_ENDPOINT=$(azd env get-values --output json | jq -r '.azureVoiceLiveEndpoint')
EOF

echo ".env file created successfully with deployment outputs!"
echo "You can now use 'docker-compose up' to test your container locally."