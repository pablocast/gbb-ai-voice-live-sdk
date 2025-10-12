/**
 * @module workspaces-v1
 * @description This module defines the Azure Log Analytics Workspaces (LAW) resources using Bicep.
 * This is version 1 (v1) of the LAW Bicep module.
 */

// ------------------
//    PARAMETERS
// ------------------

@description('The suffix to append to the Log Analytics name. Defaults to a unique string based on subscription and resource group IDs.')
param resourceSuffix string

@description('Name of the Log Analytics resource. Defaults to "workspace-<resourceSuffix>".')
param logAnalyticsName string = 'workspace-${resourceSuffix}'

@description('Location of the Log Analytics resource')
param logAnalyticsLocation string = resourceGroup().location

@description('Whether to create saved searches for LLM monitoring')
param createSavedSearches bool = true

// ------------------
//    VARIABLES
// ------------------

// ------------------
//    RESOURCES
// ------------------

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsName
  location: logAnalyticsLocation
  properties: any({
    retentionInDays: 30
    features: {
      searchVersion: 1
    }
    sku: {
      name: 'PerGB2018'
    }
  })
  identity: {
    type: 'SystemAssigned'
  }
}

resource modelUsageFunction 'Microsoft.OperationalInsights/workspaces/savedSearches@2025-02-01' = if (createSavedSearches) {
  parent: logAnalytics
  name: '${guid(subscription().subscriptionId, resourceGroup().id)}_model_usage'
  properties: {
    category: 'llm'
    displayName: 'model_usage'
    version: 2
    functionAlias: 'model_usage'
    query: 'let llmHeaderLogs = ApiManagementGatewayLlmLog \r\n| where DeploymentName != \'\'; \r\nlet llmLogsWithSubscriptionId = llmHeaderLogs \r\n| join kind=leftouter ApiManagementGatewayLogs on CorrelationId \r\n| project \r\n    SubscriptionId = ApimSubscriptionId, DeploymentName, PromptTokens, CompletionTokens, TotalTokens; \r\nllmLogsWithSubscriptionId \r\n| summarize \r\n    SumPromptTokens      = sum(PromptTokens), \r\n    SumCompletionTokens      = sum(CompletionTokens), \r\n    SumTotalTokens      = sum(TotalTokens) \r\n  by SubscriptionId, DeploymentName'
  }
}

resource promptsAndCompletionsFunction 'Microsoft.OperationalInsights/workspaces/savedSearches@2025-02-01' = if (createSavedSearches) {
  parent: logAnalytics
  name: '${guid(subscription().subscriptionId, resourceGroup().id)}_prompts_and_completions'
  properties: {
    category: 'llm'
    displayName: 'prompts_and_completions'
    version: 2
    functionAlias: 'prompts_and_completions'
    query: 'ApiManagementGatewayLlmLog\r\n| extend RequestArray = parse_json(RequestMessages)\r\n| extend ResponseArray = parse_json(ResponseMessages)\r\n| mv-expand RequestArray\r\n| mv-expand ResponseArray\r\n| project\r\n    CorrelationId, \r\n    RequestContent = tostring(RequestArray.content), \r\n    ResponseContent = tostring(ResponseArray.content)\r\n| summarize \r\n    Input = strcat_array(make_list(RequestContent), " . "), \r\n    Output = strcat_array(make_list(ResponseContent), " . ")\r\n    by CorrelationId\r\n| where isnotempty(Input) and isnotempty(Output)\r\n'
  }
}

// ------------------
//    OUTPUTS
// ------------------

output id string = logAnalytics.id
output name string = logAnalytics.name
output customerId string = logAnalytics.properties.customerId

#disable-next-line outputs-should-not-contain-secrets
output primarySharedKey string = logAnalytics.listKeys().primarySharedKey
