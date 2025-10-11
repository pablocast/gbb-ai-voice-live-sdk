param location string 
param name string 

resource aiSearch 'Microsoft.Search/searchServices@2024-06-01-preview' =  {
  name: name
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    disableLocalAuth: false
    authOptions: {
      aadOrApiKey: {
        aadAuthFailureMode: 'http401WithBearerChallenge'
      }
    }
    encryptionWithCmk: {
      enforcement: 'Unspecified'
    }
    hostingMode: 'default'
    partitionCount: 1
    publicNetworkAccess: 'enabled'
    replicaCount: 1
    semanticSearch: 'standard'
  }
  sku: {
    name: 'standard'
  }
}


output aiSearchName string = aiSearch.name
output aiSearchPrincipalId string = aiSearch.identity.principalId
output aiSearchEndpoint string = 'https://${aiSearch.name}.search.windows.net'
