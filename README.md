# <img src="img/ai_foundry.png" alt="Azure Foundry" style="width:70px;height:40px;"/>Voice agent with Azure AI Voice Live API

### 📋 Description

This repository exemplifies [Voice Live API](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/voice-live), which enables real-time speech-to-speech conversational experience through a unified API powered by generative AI models. With Voice Live API, developers can easily voice-enable any agent built with the [Azure AI Foundry Agent Service](https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/agent-types/azure-ai-foundry-agent?pivots=programming-language-python).


## 🔧 Prerequisites

+ [azd](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd), used to deploy all Azure resources and assets used in this sample.
+ [PowerShell Core pwsh](https://github.com/PowerShell/powershell/releases) if using Windows
+ [Python 3.10](https://www.python.org/downloads/release/python-3100/)
+  [An Azure Subscription](https://azure.microsoft.com/free/) with Contributor permissions
+  [Sign in to Azure with Azure CLI](https://learn.microsoft.com/cli/azure/authenticate-azure-cli-interactively)
+  [VS Code](https://code.visualstudio.com/) installed with the [Jupyter notebook extension](https://marketplace.visualstudio.com/items?itemName=ms-toolsai.jupyter) enabled

## 🏗️ Architecture

   ```
   ┌─────────────────────────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
   │       Azure Container App           │    │  Azure Voice     │    │ Azure AI Search     │
   │                                     │    │  Live API        │    │                     │
   │  ┌─────────────────────────────────┐│    │                  │    │                     │
   │  │         Frontend Client         ││    │ ┌──────────────┐ │    │ ┌─────────────────┐ │
   │  │      (React/TypeScript)         ││    │ │ GPT-4o       │ │    │ │ Search Index    │ │
   │  │                                 ││    │ │ Realtime     │ │    │ │ & Retrieval     │ │
   │  │ ┌─────────────────────────────┐ ││    │ │ Processing   │ │    │ └─────────────────┘ │
   │  │ │ Microphone Input            │ ││    │ └──────────────┘ │    │                     │
   │  │ │ Speaker Output              │ ││    │                  │    │ ┌─────────────────┐ │
   │  │ │ Tool Call UI Display        │ ││    │                  │    │ │ Vector Store    │ │
   │  │ └─────────────────────────────┘ ││    │                  │    │ │ & Documents     │ │
   │  └─────────────────┬───────────────┘│    │                  │    │ └─────────────────┘ │
   │                    │ WebSocket      │    │                  │    │                     │
   │  ┌─────────────────▼───────────────┐│    │                  │    │                     │
   │  │        Backend API              ││    │                  │    │                     │                 WebSocket  
   │  │        (FastAPI)                ││◄──►│                  │◄──►│                     │
   │  │                                 ││    │                  │    │                     │
   │  │ ┌─────────────────────────────┐ ││    │                  │    │                     │
   │  │ │ WebSocket Handler           │ ││    │                  │    │                     │
   │  │ │ Audio Streaming             │ ││    │                  │    │                     │
   │  │ │ Tool Execution              │ ││    │                  │    │                     │
   │  │ └─────────────────────────────┘ ││    │                  │    │                     │
   │  └─────────────────────────────────┘│    │                  │    │                     │
   └─────────────────────────────────────┘    └──────────────────┘    └─────────────────────┘
            
   ```

   ## ⚙️ Set Up 

This sample uses [`azd`](https://learn.microsoft.com/azure/developer/azure-developer-cli/) and a bicep template to deploy all Azure resources:

1. **Create the infrastructure**
   ```bash
   # Login to Azure (if not already logged in)
   az login

   # Initialize the project (if running for the first time)
   azd init

   # Deploy infrastructure and application to Azure
   azd up
   ```
   
   After running, an `.env` file will be created with all necessary environment variables


## 🎤 Talk to the agent

After the application has been successfully deployed you will see a URL printed to the console. Navigate to that URL to interact with the app in your browser. 

Ask questions like `Qual a data de vencimento da minha fatura` and `Quais são os beneficios do meu cartao`

![Demo Screenshot](img/demo-screenshot.png)


## 💣 **Delete the Resources**
   ```bash
   azd down --purge
   ```