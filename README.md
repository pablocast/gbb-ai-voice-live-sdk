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
      ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
      │   Azure Container App    │◄──►│  Azure Voice     │◄──►│ Azure AI Search     │
      │   (Client App)  │    │  Live API        │    │                     │
      │                 │    │                  │    │                     │
      │ ┌─────────────┐ │    │ ┌──────────────┐ │    │ ┌─────────────────┐ │
      │ │ Microphone  │ │    │ │ GPT-4o       │ │    │ │ Search Index    │ │
      │ │ Input       │ ├────┤ │ Realtime     │ ├────┤ │ & Retrieval     │ │
      │ └─────────────┘ │    │ │ Processing   │ │    │ └─────────────────┘ │
      │                 │    │ └──────────────┘ │    │                     │
      │ ┌─────────────┐ │    │                  │    │ ┌─────────────────┐ │
      │ │ Speaker     │ │    │                  │    │ │ Vector Store    │ │
      │ │ Output      │ │◄───┤                  │◄───┤ │ & Documents     │ │
      │ └─────────────┘ │    │                  │    │ └─────────────────┘ │
      └─────────────────┘    └──────────────────┘    └─────────────────────┘
   ```

## ⚙️ Set Up

This sample uses [`azd`](https://learn.microsoft.com/azure/developer/azure-developer-cli/) and a bicep template to deploy all Azure resources:

1. **Python Environment Setup**
   ```bash
   python3.10 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Create the infrastructure**
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
   ```bash
   source .venv/bin/activate
   python src/voice_assitant.py  
   ```

Ask questions like `Qual a data de vencimento da minha fatura` and `Quais são os beneficios do meu cartao`

## 🌐 Frontend

A Next.js frontend application is available in the `frontend/` directory. See [frontend/README.md](frontend/README.md) for setup and development instructions.

## 💣 **Delete the Resources**
   ```bash
   azd down --purge
   ```