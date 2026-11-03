# Home Network Control Center

Central de controle da sua rede doméstica — servidor local com HUD futurista.

---

## Início Rápido

### 1. Instalar
Execute o arquivo `INSTALAR.bat`. Ele irá:
- Verificar se Python 3.11+ está instalado
- Criar um ambiente virtual Python isolado
- Instalar todas as dependências
- Preparar pastas e configurações

### 2. Iniciar
Execute `INICIAR.bat`. O servidor irá:
- Detectar automaticamente o IP da sua rede local
- Exibir o endereço para acesso (ex: `http://192.168.1.100:8000`)
- Criar o usuário admin na primeira execução

### 3. Acessar
Abra o navegador em qualquer dispositivo da sua rede e acesse o endereço exibido.

**Credenciais iniciais:**
- Usuário: `admin`
- Senha: `Admin@1234`

> ⚠️ **Altere a senha imediatamente após o primeiro acesso!**
> Vá em Configurações → Alterar Senha.

### 4. Parar
Execute `PARAR.bat` para encerrar o servidor.

---

## Pré-requisitos

| Software | Versão | Obrigatório |
|----------|--------|-------------|
| Python | 3.11 ou superior | ✅ Sim |
| Nmap | Qualquer | 🔶 Recomendado (para scan de portas) |
| FFmpeg | Qualquer | 🔶 Recomendado (para thumbnails de vídeo) |

### Instalar Python
1. Acesse https://www.python.org/downloads/
2. Baixe o instalador para Windows
3. **Importante:** marque a opção "Add Python to PATH"
4. Conclua a instalação

### Instalar Nmap (opcional)
1. Acesse https://nmap.org/download.html
2. Baixe e instale o Nmap para Windows
3. O scanner de rede funcionará com maior precisão

### Instalar FFmpeg (opcional)
1. Acesse https://ffmpeg.org/download.html
2. Baixe o build para Windows e extraia
3. Adicione a pasta `bin` ao PATH do sistema
4. Thumbnails de vídeo serão gerados automaticamente

---

## Funcionalidades

### Dashboard
- Status em tempo real do servidor (CPU, RAM, disco)
- Gráfico de tráfego de rede ao vivo
- Contagem de dispositivos online
- Alertas recentes e últimos dispositivos conectados

### Monitor de Rede
- Mapa visual da rede com todos os dispositivos
- Tabela com IP, MAC, fabricante, tipo e status
- Filtros por status (online/offline/desconhecidos/autorizados)
- Histórico de conexões por dispositivo
- Varredura manual ou automática (a cada 5 minutos)

### Gerenciador de Arquivos
- Crie compartilhamentos apontando para pastas do seu computador
- Navegue pela estrutura de pastas pelo navegador
- Upload de arquivos (drag & drop ou seleção)
- Download direto de qualquer arquivo
- Controle de permissões por dispositivo

### Media Center
- Escaneie compartilhamentos para encontrar vídeos e músicas
- Reprodução de vídeos diretamente no navegador
- Streaming com suporte a range requests (seek funcional)
- Thumbnails gerados automaticamente (com FFmpeg)
- Organização automática em Filmes, Séries e Música

### Gerenciador de Dispositivos
- Lista todos os dispositivos detectados na rede
- Autorize/revogue acesso por dispositivo
- Sistema de pareamento: dispositivos podem solicitar acesso
- Bloqueio de dispositivos indesejados

### Central de Segurança
- Índice de segurança calculado automaticamente
- Alertas de dispositivos desconhecidos online
- Registro completo de auditoria (login, uploads, downloads)
- Histórico de eventos de conexão

### Configurações
- Alterar senha do usuário atual
- Gerenciar usuários (criar, ativar/desativar, excluir)
- Informações do servidor em tempo real

---

## Estrutura de Pastas

```
home-network-control/
├── INSTALAR.bat          ← Execute para instalar
├── INICIAR.bat           ← Execute para iniciar o servidor
├── PARAR.bat             ← Execute para parar o servidor
├── DESINSTALAR.bat       ← Remove o ambiente virtual
├── README.md             ← Esta documentação
│
├── backend/
│   ├── app/
│   │   ├── main.py       ← Aplicação FastAPI principal
│   │   ├── config.py     ← Configurações
│   │   ├── database.py   ← Banco de dados SQLite
│   │   ├── models/       ← Modelos do banco (SQLAlchemy)
│   │   ├── schemas/      ← Schemas de validação (Pydantic)
│   │   ├── routers/      ← Endpoints da API REST
│   │   └── services/     ← Lógica de negócio
│   ├── data/             ← Banco de dados SQLite (criado ao iniciar)
│   ├── shares/           ← Pasta raiz dos compartilhamentos
│   │   ├── Videos/
│   │   ├── Musicas/
│   │   ├── Documentos/
│   │   └── Imagens/
│   ├── cache/thumbnails/ ← Cache de thumbnails de vídeo
│   ├── .env              ← Configuração local (criado pelo instalador)
│   └── requirements.txt  ← Dependências Python
│
├── frontend/
│   ├── index.html        ← HUD principal (SPA)
│   └── static/
│       ├── css/style.css ← Estilos da interface
│       └── js/           ← Módulos JavaScript
│
└── venv/                 ← Ambiente virtual Python (criado pelo instalador)
```

---

## API REST

A documentação interativa da API está disponível em:
- **Swagger UI:** http://localhost:8000/api/docs
- **ReDoc:** http://localhost:8000/api/redoc

### Endpoints principais
```
POST /api/auth/login          — Login
GET  /api/network/devices     — Listar dispositivos
POST /api/network/scan        — Iniciar varredura
GET  /api/files/shares        — Listar compartilhamentos
GET  /api/media/library       — Biblioteca de mídia
GET  /api/media/stream        — Stream de vídeo/áudio
GET  /api/security/overview   — Visão geral de segurança
WS   /ws?token=...            — WebSocket em tempo real
```

---

## Solução de Problemas

### "Python não encontrado"
Instale o Python e marque "Add to PATH" durante a instalação.

### "Porta 8000 em uso"
Mude a porta editando `backend/.env`:
```
PORT=8001
```

### Scan de rede não funciona
- Execute o INICIAR.bat **como Administrador** (clique direito → "Executar como administrador")
- O Scapy/ARP requer privilégios de rede no Windows

### Thumbnails não aparecem
- Instale o FFmpeg e adicione ao PATH
- Os thumbnails são gerados na primeira reprodução

### Dispositivos não aparecem no mapa
- Execute uma varredura manual clicando em "Escanear Agora"
- Verifique se o servidor e os dispositivos estão na mesma rede Wi-Fi

---

## Segurança

- O servidor funciona **apenas na rede local** por padrão
- Todas as senhas são protegidas com hash Argon2
- Autenticação via JWT com expiração configurável
- Registro de auditoria para todas as ações relevantes
- Dispositivos precisam ser explicitamente autorizados

**Nunca exponha este servidor diretamente para a internet** sem configurar HTTPS e autenticação adicional.

---

## Alterando a Configuração

Edite o arquivo `backend/.env` para ajustar:
- Porta do servidor (`PORT`)
- Intervalo de varredura (`SCAN_INTERVAL_MINUTES`)
- Tamanho máximo de upload (`MAX_UPLOAD_SIZE_MB`)
- Pasta raiz dos compartilhamentos (`SHARES_ROOT`)

Reinicie o servidor após qualquer alteração.
