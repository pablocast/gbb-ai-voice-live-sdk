param speechServiceName string
param location string
param tags object = {}

resource speechService 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: speechServiceName
  location: location
  tags: tags
  kind: 'SpeechServices'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: speechServiceName
    publicNetworkAccess: 'Enabled'
  }
}

output key1 string = speechService.listKeys().key1
output speechEndpoint string = speechService.properties.endpoint
