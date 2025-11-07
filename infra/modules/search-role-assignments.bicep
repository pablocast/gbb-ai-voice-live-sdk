@description('Name of the AI Search resource')
param aiSearchName string

@description('Principal ID of the AI project')
param projectPrincipalId string

@description('Principal ID of User')
param userPrincipalId string

@description('Container Apps Identity Principal ID')
param containerAppsIdentityPrincipalId string

// Reference to existing AI Search service
resource searchService 'Microsoft.Search/searchServices@2024-06-01-preview' existing = {
  name: aiSearchName
}

// Search Service Contributor role assignment
resource searchContributorRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(projectPrincipalId, '8ebe5a00-799e-43f5-93ac-243d3dce84a7', searchService.id)
  scope: searchService
  properties: {
    principalId: projectPrincipalId
    roleDefinitionId: resourceId('Microsoft.Authorization/roleDefinitions', '8ebe5a00-799e-43f5-93ac-243d3dce84a7')
    principalType: 'ServicePrincipal'
  }
}

// Search Index Data Contributor role assignment
resource searchIndexDataContributorRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(projectPrincipalId, '7ca78c08-252a-4471-8644-bb5ff32d4ba0', searchService.id)
  scope: searchService
  properties: {
    principalId: projectPrincipalId
    roleDefinitionId: resourceId('Microsoft.Authorization/roleDefinitions', '7ca78c08-252a-4471-8644-bb5ff32d4ba0')
    principalType: 'ServicePrincipal'
  }
}

// For integrated vectorization access to storage
resource storageRoleSearchService 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: searchService
  name: guid(projectPrincipalId, '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1', searchService.id)
  properties: {
    principalId: projectPrincipalId
    roleDefinitionId: resourceId('Microsoft.Authorization/roleDefinitions', '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1')
    principalType: 'ServicePrincipal'
  }
}

// User
// Search Index Data Contributor
resource userSearchIndexDataContributorRoleAssignment 'Microsoft.Authorization/roleAssignments@2020-04-01-preview' = {
  name: guid(userPrincipalId,  '7ca78c08-252a-4471-8644-bb5ff32d4ba0', searchService.id)
  scope: resourceGroup()
  properties: {
    principalType: 'User'
    principalId: userPrincipalId
    roleDefinitionId: resourceId('Microsoft.Authorization/roleDefinitions', '7ca78c08-252a-4471-8644-bb5ff32d4ba0')
  }
}

// Search Service Contributor
resource userSearchServiceContributorRoleAssignment 'Microsoft.Authorization/roleAssignments@2020-04-01-preview' = {
  name: guid(userPrincipalId,  '8ebe5a00-799e-43f5-93ac-243d3dce84a7', searchService.id)
  scope: resourceGroup()
  properties: {
    principalType: 'User'
    principalId: userPrincipalId
    roleDefinitionId: resourceId('Microsoft.Authorization/roleDefinitions', '8ebe5a00-799e-43f5-93ac-243d3dce84a7')
  }
}

// Search Index Data Reader
resource userSearchIndexDataReader 'Microsoft.Authorization/roleAssignments@2020-04-01-preview' = {
  name: guid(userPrincipalId,  '1407120a-92aa-4202-b7e9-c0e197c71c8f', searchService.id)
  scope: resourceGroup()
  properties: {
    principalType: 'User'
    principalId: userPrincipalId
    roleDefinitionId: resourceId('Microsoft.Authorization/roleDefinitions', '1407120a-92aa-4202-b7e9-c0e197c71c8f')
  }
}


// Necessary for integrated vectorization, for search service to access OpenAI embeddings
resource searchServiceEmbeddingRoleAssignment 'Microsoft.Authorization/roleAssignments@2020-04-01-preview' = {
  name: guid(userPrincipalId,  '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd', searchService.id)
  scope: resourceGroup()
  properties: {
    principalType: 'ServicePrincipal'
    principalId: searchService.identity.principalId
    roleDefinitionId: resourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd')
  }
}


//Add read access to search service for container apps identity
resource containerAppsSearchReaderRoleAssignment 'Microsoft.Authorization/roleAssignments@2020-04-01-preview' = {
  name: guid(containerAppsIdentityPrincipalId,  '1407120a-92aa-4202-b7e9-c0e197c71c8f', searchService.id)
  scope: searchService
  properties: {
    principalType: 'ServicePrincipal'
    principalId: containerAppsIdentityPrincipalId
    roleDefinitionId: resourceId('Microsoft.Authorization/roleDefinitions', '1407120a-92aa-4202-b7e9-c0e197c71c8f')
  }
}
