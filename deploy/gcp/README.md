# Deploy no Google Cloud Run

Este diretório contém os arquivos necessários para fazer o deploy da aplicação Copo do Mundo no Google Cloud Run.

## Pré-requisitos

1. Conta no Google Cloud Platform
2. Google Cloud SDK instalado
3. Docker instalado
4. Projeto criado no Google Cloud Console

## Configuração Inicial

1. Faça login no Google Cloud:
```bash
gcloud auth login
```

2. Configure o projeto:
```bash
gcloud config set project [SEU-PROJETO-ID]
```

3. Habilite as APIs necessárias:
```bash
gcloud services enable \
  run.googleapis.com \
  containerregistry.googleapis.com \
  cloudbuild.googleapis.com
```

## Deploy

### 1. Build e Push da Imagem

```bash
# Navegue até o diretório do projeto
cd /caminho/para/copo-do-mundo

# Build e push da imagem
gcloud builds submit --config deploy/gcp/cloudbuild.yaml
```

### 2. Verificação do Deploy

Após o deploy, você pode verificar o status e acessar a aplicação:

```bash
# Verifique o status do serviço
gcloud run services describe copo-do-mundo --region us-central1

# Obtenha a URL do serviço
gcloud run services describe copo-do-mundo --region us-central1 --format='value(status.url)'
```

## Configurações do Serviço

O serviço está configurado com os seguintes parâmetros:

- **Região**: us-central1
- **Memória**: 1GB
- **CPU**: 1 core
- **Instâncias mínimas**: 1
- **Instâncias máximas**: 10
- **Porta**: 8080

## Monitoramento

1. Acesse o Console do Google Cloud
2. Navegue até Cloud Run
3. Selecione o serviço "copo-do-mundo"
4. Use as ferramentas de monitoramento disponíveis

## Logs

Para ver os logs do serviço:

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=copo-do-mundo" --limit 50
```

## Troubleshooting

### Problemas Comuns

1. **Erro de permissão**
   - Verifique se você tem as permissões necessárias
   - Execute `gcloud auth login` novamente

2. **Erro de build**
   - Verifique os logs do Cloud Build
   - Confirme se o Dockerfile está correto

3. **Erro de deploy**
   - Verifique os logs do serviço
   - Confirme se as APIs estão habilitadas

### Soluções

1. **Reiniciar o serviço**
```bash
gcloud run services update-traffic copo-do-mundo --to-revisions=LATEST=100
```

2. **Verificar status**
```bash
gcloud run services describe copo-do-mundo --region us-central1
```

3. **Rollback**
```bash
gcloud run services update-traffic copo-do-mundo --to-revisions=[REVISION-ID]=100
```

## Manutenção

### Atualização do Serviço

Para atualizar o serviço com novas alterações:

```bash
gcloud builds submit --config deploy/gcp/cloudbuild.yaml
```

### Limpeza

Para remover recursos não utilizados:

```bash
# Remover imagens antigas
gcloud container images list-tags gcr.io/[PROJECT-ID]/copo-do-mundo --format="get(digest)" | while read digest; do gcloud container images delete "gcr.io/[PROJECT-ID]/copo-do-mundo@$digest" --quiet; done
``` 