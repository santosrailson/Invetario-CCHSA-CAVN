# NetInventory — CCHSA/CAVN

Sistema de inventário de rede desenvolvido em Django para gerenciamento de ativos de TI da instituição.

## Funcionalidades

- **Switches** — cadastro com portas, VLANs, fabricante e localização
- **Roteadores** — inventário com IP, modelo e localização
- **Access Points** — SSID, canal, frequência (2.4/5GHz/Dual)
- **Computadores** — hostname, IP, MAC, SO, usuário responsável e departamento
- **E-mails Institucionais** — contas por departamento, servidor e cota
- **Sites** — monitoramento de URLs com validade de certificado SSL
- **Subredes** — gerenciamento de CIDRs, gateways e faixas de IP
- **Localizações** — campus, bloco, andar, sala e rack
- **Histórico de Ping** — monitoramento de disponibilidade com latência
- **Dashboard** — visão geral dos ativos e pings do dia
- **Relatório PDF** — exportação geral do inventário
- **Importação/Exportação** — suporte a CSV/Excel via django-import-export

## Stack

- Python 3.12 / Django 5.0
- Interface admin: [django-unfold](https://github.com/unfoldadmin/django-unfold)
- Relatórios: ReportLab
- Monitoramento: ping3
- Deploy: Docker + Gunicorn + Whitenoise

## Como executar

### Com Docker (recomendado)

```bash
docker compose up -d
```

A aplicação estará disponível em `http://localhost:8000`.

Na primeira execução, um superusuário é criado automaticamente:

| Campo | Valor |
|-------|-------|
| Usuário | `admin` |
| Senha | `admin123` |

> Altere a senha após o primeiro acesso.

### Sem Docker

```bash
pip install -r requirements.txt
python manage.py makemigrations inventory
python manage.py migrate
python manage.py collectstatic
python manage.py createsuperuser
python manage.py runserver
```

## Variáveis de ambiente

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `DJANGO_SECRET_KEY` | Chave secreta do Django | — |
| `DEBUG` | Modo debug | `False` |

> Em produção, defina `DJANGO_SECRET_KEY` com um valor longo e aleatório e `DEBUG=False`.

## Estrutura do projeto

```
.
├── inventory/          # App principal (models, views, admin, reports)
├── netinventory/       # Configurações do projeto Django
├── templates/          # Templates HTML
├── static/             # Arquivos estáticos
├── data/               # Banco de dados SQLite (volume Docker)
├── Dockerfile
├── docker-compose.yml
├── entrypoint.sh
└── requirements.txt
```

## Permissões necessárias

O container requer a capability `NET_RAW` para executar pings ICMP (já configurada no `docker-compose.yml`).
