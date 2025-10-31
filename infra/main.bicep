// ------------------
//    PARAMETERS
// ------------------

param aiServicesConfig array = []
param modelsConfig array = []
param foundryProjectName string = 'demo-realtime'
param principalId string
param searchIndexName string
param logAnalyticsName string = ''

@allowed(['Consumption', 'D4', 'D8', 'D16', 'D32', 'E4', 'E8', 'E16', 'E32', 'NC24-A100', 'NC48-A100', 'NC96-A100'])
param azureContainerAppsWorkloadProfile string
param environmentName string

@description('Used by azd for containerapps deployment')
param webAppExists bool

// ------------------
//    VARIABLES
// ------------------
param deploymentTimestamp string = utcNow('yyyyMMddHHmmss')
var resourceSuffix = uniqueString(subscription().id, resourceGroup().id, deploymentTimestamp)
var tags = { 'azd-env-name': environmentName }

// ------------------
//    RESOURCES
// ------------------

// 1. Log Analytics Workspace
module lawModule './modules/workspaces.bicep' = {
  name: 'lawModule'
  params: {
    resourceSuffix: resourceSuffix
  }
}

// 2. Application Insights
module appInsightsModule './modules/appinsights.bicep' = {
  name: 'appInsightsModule'
  params: {
    lawId: lawModule.outputs.id
    customMetricsOptedInType: 'WithDimensions'
    resourceSuffix: resourceSuffix
  }
}

// 3. API Management
// module apimModule './modules/apim.bicep' = {
//   name: 'apimModule'
//   params: {
//     apimSku: apimSku
//     apimSubscriptionsConfig: apimSubscriptionsConfig
//     lawId: lawModule.outputs.id
//     appInsightsId: appInsightsModule.outputs.id
//     appInsightsInstrumentationKey: appInsightsModule.outputs.instrumentationKey
//   }
// }

// 3. Cognitive Search for Vector Search
module searchModule './modules/search.bicep' = {
  name: 'searchModule'
  params: {
    name: 'aisearch-${resourceSuffix}'
    location: resourceGroup().location
  }
}


// 4. AI Foundry
var aiSearchName = searchModule.outputs.aiSearchName
var aiSearchServiceResourceGroupName = resourceGroup().name
var aiSearchServiceSubscriptionId = subscription().subscriptionId

module foundryModule './modules/foundry.bicep' = {
    name: 'foundryModule'
    params: {
      resourceSuffix: resourceSuffix
      aiServicesConfig: aiServicesConfig
      modelsConfig: modelsConfig
      foundryProjectName: foundryProjectName
      principalId: principalId
      aiSearchName: aiSearchName
      aiSearchServiceResourceGroupName: aiSearchServiceResourceGroupName
      aiSearchServiceSubscriptionId: aiSearchServiceSubscriptionId
    }
    dependsOn: [
      searchModule
    ]
  }

// 5. Speech Service for Voice Live API
// module speechModule './modules/speech.bicep' = {
//   name: 'speechModule'
//   params: {
//     speechServiceName: 'speech-voicelab-${resourceSuffix}'
//     location: resourceGroup().location
//     tags: {
//       project: 'VoiceLab'
//       environment: 'demo'
//     }
//   }
// }

module searchRoleAssignments './modules/search-role-assignments.bicep' = {
  name: 'ai-search-ra-${resourceSuffix}-deployment'
  scope: resourceGroup(aiSearchServiceSubscriptionId, aiSearchServiceResourceGroupName)
  params: {
    aiSearchName: aiSearchName
    projectPrincipalId: foundryModule.outputs.extendedAIServicesConfig[0].principalId
    userPrincipalId: principalId
    containerAppsIdentityPrincipalId: acaIdentity.outputs.principalId
  }
}

// 6. Storage Account for document storage
module storageModule './modules/storage.bicep' = {
  name: 'storageModule'
  params: {
    storageName: 'stgvoicelab${resourceSuffix}'
    location: resourceGroup().location
    sku: {
      name: 'Standard_LRS'
    }
    docsContainerName: 'documents'
  }
  dependsOn: [
    foundryModule
  ]
}

module storageRoleAssignments './modules/storage-role-assignments.bicep' = {
  name: 'storage-ra-${resourceSuffix}-deployment'
  params: {
    storageAccountName: storageModule.outputs.name
    searchServicePrincipalId: searchModule.outputs.aiSearchPrincipalId
    principalId: principalId
  }
  dependsOn: [
    storageModule
    searchModule
  ]
}

// resource apimService 'Microsoft.ApiManagement/service@2024-06-01-preview' existing = {
//   name: 'apim-${resourceSuffix}'
// }

// 5. APIM OpenAI-RT Websocket API
// https://learn.microsoft.com/azure/templates/microsoft.apimanagement/service/apis
// resource api 'Microsoft.ApiManagement/service/apis@2024-06-01-preview' = {
//   name: 'realtime-audio'
//   parent: apimService
//   properties: {
//     apiType: 'websocket'
//     description: 'Inference API for Azure OpenAI Realtime'
//     displayName: 'InferenceAPI'
//     path: '${inferenceAPIPath}/openai/realtime'
//     serviceUrl: '${replace(foundryModule.outputs.extendedAIServicesConfig[0].endpoint, 'https:', 'wss:')}openai/realtime'
//     type: inferenceAPIType
//     protocols: [
//       'wss'
//     ]
//     subscriptionKeyParameterNames: {
//       header: 'api-key'
//       query: 'api-key'
//     }
//     subscriptionRequired: true
//   }
// }

// resource rtOperation 'Microsoft.ApiManagement/service/apis/operations@2024-06-01-preview' existing = {
//   name: 'onHandshake'
//   parent: api
// }

// https://learn.microsoft.com/azure/templates/microsoft.apimanagement/service/apis/policies
// resource rtPolicy 'Microsoft.ApiManagement/service/apis/operations/policies@2024-06-01-preview' = {
//   name: 'policy'
//   parent: rtOperation
//   properties: {
//     format: 'rawxml'
//     value: loadTextContent('policy.xml')
//   }
// }

// resource apiDiagnostics 'Microsoft.ApiManagement/service/apis/diagnostics@2024-06-01-preview' = {
//   parent: api
//   name: 'azuremonitor'
//   properties: {
//     alwaysLog: 'allErrors'
//     verbosity: 'verbose'
//     logClientIp: true
//     loggerId: apimModule.outputs.loggerId
//     sampling: {
//       samplingType: 'fixed'
//       percentage: json('100')
//     }
//     frontend: {
//       request: {
//         headers: []
//         body: {
//           bytes: 0
//         }
//       }
//       response: {
//         headers: []
//         body: {
//           bytes: 0
//         }
//       }
//     }
//     backend: {
//       request: {
//         headers: []
//         body: {
//           bytes: 0
//         }
//       }
//       response: {
//         headers: []
//         body: {
//           bytes: 0
//         }
//       }
//     }
//     largeLanguageModel: {
//       logs: 'enabled'
//       requests: {
//         messages: 'all'
//         maxSizeInBytes: 262144
//       }
//       responses: {
//         messages: 'all'
//         maxSizeInBytes: 262144
//       }
//     }
//   }
// } 

// Azure container apps resources
// User-assigned identity for pulling images from ACR
var acaIdentityName = 'aca-identity-${resourceSuffix}'
module acaIdentity './modules/security/aca-identity.bicep' = {
  name: 'aca-identity'
  scope: resourceGroup()
  params: {
    identityName: acaIdentityName
    location: resourceGroup().location
  }
}

module containerApps './modules/host/container-apps.bicep' = {
  name: 'container-apps'
  scope: resourceGroup()
  params: {
    name: 'app'
    tags: tags
    location: resourceGroup().location
    workloadProfile: azureContainerAppsWorkloadProfile
    containerAppsEnvironmentName: '${environmentName}-aca-env'
    containerRegistryName: 'containerregistry${resourceSuffix}'
    logAnalyticsWorkspaceResourceId: lawModule.outputs.id
  }
}

// Container Apps for the web application (Python Quart app with JS frontend)
module acaBackend './modules/host/container-app-upsert.bicep' = {
  name: 'aca-web'
  scope: resourceGroup()
  dependsOn: [
    containerApps
    acaIdentity
  ]
  params: {
    name: '$webapp-backend-${resourceSuffix}'
    location: resourceGroup().location
    identityName: acaIdentityName
    exists: webAppExists
    workloadProfile: azureContainerAppsWorkloadProfile
    containerRegistryName: containerApps.outputs.registryName
    containerAppsEnvironmentName: containerApps.outputs.environmentName
    identityType: 'UserAssigned'
    tags: union(tags, { 'azd-service-name': 'backend' })
    targetPort: 8000
    containerCpuCoreCount: '1.0'
    containerMemory: '2Gi'
    env: {
      AZURE_VOICELIVE_ENDPOINT: foundryModule.outputs.extendedAIServicesConfig[0].endpoint
      AZURE_VOICELIVE_API_KEY: foundryModule.outputs.extendedAIServicesConfig[0].apiKey
      AZURE_SEARCH_ENDPOINT: searchModule.outputs.aiSearchEndpoint
      AZURE_SEARCH_INDEX: searchIndexName
      RUNNING_IN_PRODUCTION: 'true'
      AZURE_CLIENT_ID: acaIdentity.outputs.clientId
    }
  }
}



// ------------------
//    OUTPUTS
// ------------------

output logAnalyticsWorkspaceId string = lawModule.outputs.customerId
// output apimServiceId string = apimModule.outputs.id
// output apimResourceGatewayURL string = apimModule.outputs.gatewayUrl
// output apiKey string = apimModule.outputs.apimSubscriptions[0].key
// output apimSubscriptions array = apimModule.outputs.apimSubscriptions
output azureOpenAiDeploymentName string = modelsConfig[0].name
output azureEmbeddingDeploymentName string = modelsConfig[1].name
output azureVoiceLiveApiKey string = foundryModule.outputs.extendedAIServicesConfig[0].apiKey
output azureVoiceLiveEndpoint string = foundryModule.outputs.extendedAIServicesConfig[0].endpoint
output azureSearchIndex string = searchIndexName
output azureOpenAiEndpoint string = foundryModule.outputs.extendedAIServicesConfig[0].openAiEndpoint
output azureOpenAiEmbeddingModel string = modelsConfig[1].name
output azureSearchEndpoint string = searchModule.outputs.aiSearchEndpoint
output azureStorageEndpoint string = storageModule.outputs.endpoint
output azureStorageConnectionString string = storageModule.outputs.connectionString
output azureStorageContainer string = storageModule.outputs.containerName
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = containerApps.outputs.registryLoginServer
output WEBSITE_URL string = acaBackend.outputs.uri
