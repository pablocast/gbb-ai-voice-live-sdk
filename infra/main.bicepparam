using './main.bicep'

param aiServicesConfig = [
  {
    name: 'foundry1'
    location: 'eastus2'
  }
]

param modelsConfig = [
  {
    name: 'gpt-4.1'
    format: 'OpenAI'
    version: '2025-04-14'
    skuName: 'GlobalStandard'
    capacity: 1000
  }
  {
    name: 'text-embedding-3-large'
    format: 'OpenAI'
    version: '1'
    skuName: 'Standard'
    capacity: 350
  }
]

param principalId = readEnvironmentVariable('AZURE_PRINCIPAL_ID', 'principalId')
param searchIndexName = 'voicerag-intvect'
param azureContainerAppsWorkloadProfile = 'Consumption'
param environmentName = readEnvironmentVariable('ACA_ENV_NAME', 'voicerag-aca-env')
param webAppExists = false 
