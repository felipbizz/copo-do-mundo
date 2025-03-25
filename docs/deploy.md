# Guia de Deploy

Este documento descreve as opções de deploy disponíveis para o projeto Copo do Mundo.

## Google Cloud Run

O projeto está configurado para ser deployado no Google Cloud Run, uma plataforma serverless que permite executar containers de forma escalável.

### Requisitos

1. Conta no Google Cloud Platform
2. Google Cloud SDK instalado
3. Docker instalado
4. Projeto criado no Google Cloud Console

### Configuração

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

### Deploy

1. Execute o comando de deploy:
```bash
gcloud builds submit --config deploy/gcp/cloudbuild.yaml
```

2. Verifique o status:
```bash
gcloud run services describe copo-do-mundo --region us-central1
```

3. Acesse a aplicação:
```bash
gcloud run services describe copo-do-mundo --region us-central1 --format='value(status.url)'
```

### Configurações do Serviço

- **Região**: us-central1
- **Memória**: 1GB
- **CPU**: 1 core
- **Instâncias mínimas**: 1
- **Instâncias máximas**: 10
- **Porta**: 8080

### Monitoramento

1. Acesse o Console do Google Cloud
2. Navegue até Cloud Run
3. Selecione o serviço "copo-do-mundo"
4. Use as ferramentas de monitoramento disponíveis

### Logs

Para ver os logs do serviço:
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=copo-do-mundo" --limit 50
```

### Manutenção

#### Atualização
```bash
gcloud builds submit --config deploy/gcp/cloudbuild.yaml
```

#### Rollback
```bash
gcloud run services update-traffic copo-do-mundo --to-revisions=[REVISION-ID]=100
```

#### Limpeza
```bash
# Remover imagens antigas
gcloud container images list-tags gcr.io/[PROJECT-ID]/copo-do-mundo --format="get(digest)" | while read digest; do gcloud container images delete "gcr.io/[PROJECT-ID]/copo-do-mundo@$digest" --quiet; done
```

### Troubleshooting

#### Problemas Comuns

1. **Erro de permissão**
   - Verifique se você tem as permissões necessárias
   - Execute `gcloud auth login` novamente

2. **Erro de build**
   - Verifique os logs do Cloud Build
   - Confirme se o Dockerfile está correto

3. **Erro de deploy**
   - Verifique os logs do serviço
   - Confirme se as APIs estão habilitadas

#### Soluções

1. **Reiniciar o serviço**
```bash
gcloud run services update-traffic copo-do-mundo --to-revisions=LATEST=100
```

2. **Verificar status**
```bash
gcloud run services describe copo-do-mundo --region us-central1
```

## Outras Opções de Deploy

### Docker Local

Para executar localmente usando Docker:

```bash
# Build da imagem
docker build -t copo-do-mundo -f deploy/gcp/Dockerfile .

# Executar o container
docker run -p 8080:8080 copo-do-mundo
```

### Docker Compose

Para desenvolvimento local com Docker Compose:

```bash
# Iniciar os serviços
docker-compose up

# Parar os serviços
docker-compose down
```

## Considerações de Segurança

### Variáveis de Ambiente

1. Crie um arquivo `.env` na raiz do projeto
2. Adicione as variáveis necessárias:
```env
DEBUG=False
SECRET_KEY=seu-secret-key
DATABASE_URL=sua-url-do-banco
```

### SSL/TLS

O Google Cloud Run já fornece HTTPS por padrão. Para desenvolvimento local:

1. Gere certificados SSL:
```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout private.key -out certificate.crt
```

2. Configure o Streamlit para usar HTTPS:
```bash
streamlit run main.py --server.sslCertFile=certificate.crt --server.sslKeyFile=private.key
```

## Backup e Recuperação

### Backup de Dados

1. Configure backup automático no Google Cloud Storage
2. Mantenha cópias dos dados em local seguro
3. Teste a recuperação periodicamente

### Recuperação

1. Restaure os dados do backup
2. Verifique a integridade dos dados
3. Teste a aplicação após a recuperação 