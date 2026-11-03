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
| Sunshine | Latest | 🔶 Opcional (para streaming de jogos/desktop) |

### Instalar Python
1. Acesse https://www.python.org/downloads/
2. Baixe o instalador para Windows
3. **Importante:** marque a opção "Add Python to PATH"
4. Conclua a instalação

### Instalar Nmap (opcional - para scan de portas preciso)
1. Acesse https://nmap.org/download.html
2. Baixe e instale o Nmap para Windows
3. O scanner de rede funcionará com maior precisão

### Instalar FFmpeg (opcional - para thumbnails de vídeo)
1. Acesse https://ffmpeg.org/download.html
2. Baixe o build para Windows e extraia
3. Adicione a pasta `bin` ao PATH do sistema
4. Thumbnails de vídeo serão gerados automaticamente

### Instalar Sunshine (opcional - para Central de Computação)
1. Acesse https://github.com/LizardByte/Sunshine/releases
2. Baixe o instalador Windows mais recente (`sunshine-windows-installer.exe`)
3. Execute a instalação (pode requerer reinicialização)
4. O Sunshine roda como serviço em segundo plano nas portas 47989 (stream) e 47990 (web UI)

> **Nota:** O Sunshine é um host de streaming de jogos/desktop open-source compatível com clientes Moonlight. Permite jogar seus jogos do PC em outros dispositivos (celular, tablet, TV, outro PC) pela rede local.

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
- Scan de portas/serviços via Nmap em dispositivos autorizados

### Gerenciador de Arquivos (Central de Compartilhamento) ⭐
- **Crie compartilhamentos** apontando para pastas do seu computador
- **Navegue pela estrutura de pastas** pelo navegador (estilo explorador de arquivos)
- **Upload de arquivos** (drag & drop ou seleção, até 2GB por arquivo)
- **Download direto** de qualquer arquivo
- **Criação de pastas**, renomear, mover, copiar, excluir
- **Controle de permissões por dispositivo**: READ (leitura), WRITE (escrita/upload), DELETE (exclusão)
- **Suporte a compartilhamentos de arquivo único** ou pastas inteiras
- **Validação de path traversal** para segurança

#### Como usar a Central de Compartilhamento:
1. Acesse a aba **Arquivos** no menu lateral
2. Clique em **"Novo Compartilhamento"**
3. Dê um **nome** (ex: "Meus Documentos", "Vídeos da Família")
4. Informe o **caminho relativo** à pasta `backend/shares/`:
   - `documentos` → `backend/shares/documentos/`
   - `videos/filmes` → `backend/shares/videos/filmes/`
5. Escolha o tipo: **Pasta** (navegável) ou **Arquivo** (download direto)
6. Clique em **Criar**
7. Para dar acesso a dispositivos: vá em **Dispositivos**, selecione um dispositivo autorizado e configure as permissões no compartilhamento

> 💡 **Dica:** A pasta raiz `backend/shares/` já vem com subpastas criadas: `Videos/`, `Musicas/`, `Documentos/`, `Imagens/`. Use essas ou crie suas próprias.

### Media Center
- Escaneie compartilhamentos para encontrar vídeos e músicas
- Reprodução de vídeos diretamente no navegador (HTML5 video player)
- Streaming com suporte a **range requests** (seek funcional, pular para qualquer posição)
- Thumbnails gerados automaticamente (com FFmpeg)
- Organização automática em **Filmes**, **Séries** e **Música** (detecção por nome de arquivo: S01E01, 1x01, etc.)
- Player com controles de velocidade, tela cheia, legenda (se houver .srt)

### Gerenciador de Dispositivos
- Lista todos os dispositivos detectados na rede
- Autorize/revogue acesso por dispositivo
- **Sistema de pareamento**: dispositivos podem solicitar acesso via QR code ou código
- Bloqueio de dispositivos indesejados
- Detecção automática de tipo (celular, tablet, PC, TV, console, IoT, impressora, NAS, roteador)
- Identificação de fabricante via MAC address (OUI database)

### Central de Segurança
- Índice de segurança calculado automaticamente (0-100%)
- Alertas de dispositivos desconhecidos online
- Registro completo de auditoria (login, uploads, downloads, ações administrativas)
- Histórico de eventos de conexão (online/offline/troca de IP)
- Falhas de login nas últimas 24h
- Novos dispositivos detectados nas últimas 24h

### Configurações
- Alterar senha do usuário atual
- **Gerenciar usuários** (criar, ativar/desativar, excluir, alterar papel: Admin/Usuário/Visualizador)
- Informações do servidor em tempo real (versão, uptime, IP, porta, usuários ativos)

### Central de Computação (Sunshine Integration) ⭐
Integração completa com **Sunshine** para streaming de jogos e desktop remoto via **Moonlight**.

#### Funcionalidades:
- **Iniciar/Parar Sunshine** com um clique
- **Status em tempo real**: versão, uptime, sessões ativas, max sessões
- **Descoberta automática de aplicativos/jogos**:
  - Via API do Sunshine (apps configurados no Sunshine)
  - Scan do sistema (Steam, Epic Games, GOG, Battle.net, executáveis em Program Files)
  - Categorização automática: Jogos, Navegadores, Utilitários, Desconhecidos
- **Perfis de qualidade de streaming pré-definidos**:
  | Perfil | Resolução | FPS | Bitrate | Codec | Uso recomendado |
  |--------|-----------|-----|---------|-------|-----------------|
  | **Ultra** | 4K (3840x2160) | 60 | 80 Mbps | HEVC | Rede gigabit, cliente 4K |
  | **Alto** | 1440p (2560x1440) | 120 | 50 Mbps | HEVC | Jogos competitivos, monitores 144Hz |
  | **Equilibrado** | 1080p (1920x1080) | 60 | 25 Mbps | H.264 | **Padrão**, boa qualidade/desempenho |
  | **Econômico** | 720p (1280x720) | 30 | 10 Mbps | H.264 | Wi-Fi fraco, dados móveis |
  | **Mobile** | 720p (1280x720) | 60 | 15 Mbps | HEVC | Celulares/tablets modernos |

- **Gerar link de conexão + QR Code** para cada perfil
- **Sessões ativas** em tempo real
- **Configuração do Sunshine** pela interface (host, portas, usuário, senha, encoder, bitrate, FPS, resolução, GPU, HEVC/AV1)
- **Suporte a múltiplos encoders**: NVIDIA NVENC, AMD AMF, Intel QuickSync, Software (CPU)

#### Como configurar e usar o Sunshine:

##### 1. Instalação do Sunshine
```bash
# Baixe em: https://github.com/LizardByte/Sunshine/releases/latest
# Execute o instalador .exe
# Reinicie o PC se solicitado
```

##### 2. Configuração inicial (pela interface web do Sunshine)
1. Acesse `http://localhost:47990` no navegador (apenas no PC servidor)
2. Crie usuário/senha para o Sunshine (ex: user: `sunshine`, pass: `sua_senha_forte`)
3. Configure:
   - **Video Encoder**: Escolha seu GPU (NVIDIA NVENC / AMD AMF / Intel QSV)
   - **Resolution**: 1920x1080 (ou 3840x2160 se 4K)
   - **FPS**: 60
   - **Bitrate**: 25000 kbps (25 Mbps) para 1080p60
   - **HEVC**: Ativado se cliente suportar (Moonlight moderno suporta)
   - **Audio**: Opus 128kbps

##### 3. Configuração no Home Network Control Center
1. Acesse a aba **Central de Computação** → **Configuração**
2. Preencha:
   - **Host**: `0.0.0.0` (ou IP local)
   - **Porta Stream**: `47989` (padrão Sunshine)
   - **Porta Web UI**: `47990` (padrão Sunshine)
   - **Usuário**: `sunshine` (o que você criou no passo 2)
   - **Senha**: a senha do Sunshine
   - **Encoder**: NVENC / AMF / QSV / Software
   - **Max Bitrate**: ex: 25000 (kbps)
   - **Max FPS**: 60
   - **Resolução**: 1920x1080
   - **GPU Device ID**: (opcional, deixe vazio para auto)
   - **Auto-start**: ☑️ Iniciar Sunshine com o servidor
3. Clique em **Salvar Configuração**

##### 4. Adicionar Jogos/Aplicativos ao Sunshine
**Opção A - Pela interface do Sunshine (recomendado):**
1. Acesse `http://localhost:47990` → aba **Apps**
2. Clique em **Add App**
3. Preencha nome, caminho do executável, argumentos, diretório de trabalho
4. Adicione imagem/capa (opcional)
5. Salve

**Opção B - Descoberta automática pelo HNCC:**
1. Na aba **Central de Computação** → **Aplicativos**
2. Clique em **Atualizar** - fará scan do sistema
3. Apps encontrados aparecerão listados
4. Clique em um app para ver detalhes

##### 5. Conectar via Moonlight (Cliente)
**No dispositivo cliente (celular, tablet, TV, outro PC):**
1. Instale **Moonlight** (https://moonlight-stream.org/)
   - Android: Play Store / F-Droid
   - iOS: App Store
   - Windows/macOS/Linux: Site oficial / Flatpak / Scoop / Chocolatey
   - Apple TV / Android TV / Fire TV: Loja respectiva
2. Abra o Moonlight - ele deve detectar automaticamente o Sunshine na rede
3. Se não detectar: adicione manualmente `IP_DO_SERVIDOR:47989`
4. Faça login com usuário/senha do Sunshine

**Via Home Network Control Center (mais fácil):**
1. Na aba **Central de Computação** → **Dashboard**
2. Clique em um botão de **Quick Stream** (Ultra, Alto, Equilibrado, Econômico, Mobile)
3. Ou vá em **Aplicativos**, escolha um jogo, clique em **Iniciar**
4. Será gerado:
   - **Link `moonlight://...`** - clique para abrir direto no Moonlight (se associado)
   - **QR Code** - escaneie com o celular para conectar instantaneamente
   - **Link `sunshine://...`** - alternativo
5. No Moonlight, o stream iniciará automaticamente

##### 6. Streaming de Desktop Completo
1. Na aba **Central de Computação** → **Dashboard**
2. Clique em **Iniciar Desktop** (ou use perfil "Equilibrado" em Quick Stream)
3. Conecte via Moonlight - verá toda a área de trabalho do PC servidor
4. Funciona para: trabalho remoto, suporte técnico, apresentações, apps não-jogos

> ⚠️ **Requisitos de rede para boa experiência:**
> - **Cabeada (Ethernet)**: Melhor latência e estabilidade
> - **Wi-Fi 5/6/6E/7**: 5GHz obrigatório, preferencialmente próximo ao roteador
> - **Latência alvo**: < 20ms na rede local para jogabilidade fluida
> - **Bitrate**: Ajuste conforme sua rede (teste com "Equilibrado" e suba/desça)

> 🔒 **Segurança:** O Sunshine só aceita conexões da rede local por padrão. **Nunca exponha as portas 47989/47990 para a internet** sem VPN (Tailscale, WireGuard) ou túnel seguro.

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
│   │   ├── config.py     ← Configurações (pydantic-settings)
│   │   ├── database.py   ← Banco de dados SQLite (aiosqlite)
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
└── venv/                 ← Ambiente virtual Python (criado pelo instalador, ignorado pelo git)
```

---

## API REST

A documentação interativa da API está disponível em:
- **Swagger UI:** http://localhost:8000/api/docs
- **ReDoc:** http://localhost:8000/api/redoc

### Endpoints principais
```
POST /api/auth/login           — Login (retorna access + refresh token)
POST /api/auth/refresh         — Renovar access token
GET  /api/network/devices      — Listar dispositivos
POST /api/network/scan         — Iniciar varredura de rede
GET  /api/network/devices/{id} — Detalhes do dispositivo
POST /api/network/pair         — Solicitar pareamento
GET  /api/files/shares         — Listar compartilhamentos
POST /api/files/shares         — Criar compartilhamento
GET  /api/files/shares/{id}/contents — Navegar pastas
POST /api/files/shares/{id}/upload   — Upload de arquivo
GET  /api/files/shares/{id}/download — Download de arquivo
GET  /api/media/library        — Biblioteca de mídia (filmes/séries/música)
GET  /api/media/stream         — Stream de vídeo/áudio (range requests)
GET  /api/media/thumbnail      — Thumbnail de vídeo
GET  /api/devices              — Lista de dispositivos
POST /api/devices/{id}/authorize — Autorizar dispositivo
POST /api/devices/{id}/block     — Bloquear dispositivo
GET  /api/security/overview    — Visão geral de segurança
GET  /api/security/alerts      — Alertas de segurança
GET  /api/security/audit       — Log de auditoria
GET  /api/security/events      — Eventos de conexão
GET  /api/computing/status     — Status do Sunshine
POST /api/computing/start      — Iniciar Sunshine
POST /api/computing/stop       — Parar Sunshine
GET  /api/computing/apps       — Apps/jogos descobertos
POST /api/computing/launch     — Iniciar stream (app ou desktop)
GET  /api/computing/stream-url — Gerar URL de conexão + QR Code
WS   /ws?token=...             — WebSocket tempo real (stats, dispositivos, alertas)
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
- Execute o `INICIAR.bat` **como Administrador** (clique direito → "Executar como administrador")
- O Scapy/ARP requer privilégios de rede no Windows
- Instale o **Nmap** para scan de portas/serviços mais preciso

### Thumbnails não aparecem
- Instale o **FFmpeg** e adicione ao PATH
- Os thumbnails são gerados na primeira reprodução do vídeo

### Dispositivos não aparecem no mapa
- Execute uma varredura manual clicando em "Escanear Agora"
- Verifique se o servidor e os dispositivos estão na mesma rede Wi-Fi
- Alguns dispositivos (IoT, impressoras) podem não responder a ARP

### Sunshine não inicia / não conecta
- Verifique se o Sunshine está instalado: `C:\Program Files\Sunshine\sunshine.exe`
- Acesse `http://localhost:47990` para ver se a web UI do Sunshine responde
- Verifique firewall: portas 47989 (TCP/UDP) e 47990 (TCP) devem estar liberadas
- No Windows, o Sunshine pode precisar rodar como serviço - reinicie o PC após instalar
- Logs do Sunshine: `%APPDATA%\Sunshine\logs\`

### Moonlight não detecta o Sunshine
- Mesma rede Wi-Fi (não guest network)
- Firewall do Windows: permitir "Sunshine" nas redes privadas
- Tente conectar manualmente: `IP_DO_PC:47989` no Moonlight
- Verifique se usuário/senha do Sunshine estão corretos na configuração do HNCC

### Performance ruim no streaming
- Use cabo de rede (Ethernet) no PC servidor
- Wi-Fi 5GHz no cliente, próximo ao roteador
- Reduza bitrate/resolução no perfil de qualidade
- Verifique se o encoder de hardware (NVENC/AMF/QSV) está sendo usado (não CPU)
- Feche apps pesados no PC servidor

---

## Segurança

- O servidor funciona **apenas na rede local** por padrão
- Todas as senhas são protegidas com hash **Argon2id** (configurável)
- Autenticação via **JWT** com expiração configurável (access + refresh tokens)
- Registro de auditoria para todas as ações relevantes
- Dispositivos precisam ser explicitamente autorizados
- Validação de path traversal no gerenciador de arquivos
- Rate limiting e proteção contra brute force no login

**Nunca exponha este servidor diretamente para a internet** sem configurar:
1. HTTPS (certificado válido ou self-signed com CA própria)
2. Autenticação adicional (2FA, VPN, Tailscale, WireGuard)
3. Firewall restringindo IPs de origem
4. Reverse proxy (nginx/Traefik) com segurança extra

Para acesso remoto seguro, recomenda-se usar **Tailscale** ou **WireGuard** para criar uma VPN mesh entre seus dispositivos.

---

## Alterando a Configuração

Edite o arquivo `backend/.env` para ajustar:

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `HOST` | Interface de bind | `0.0.0.0` |
| `PORT` | Porta do servidor | `8000` |
| `DEBUG` | Modo debug (auto-reload) | `false` |
| `SECRET_KEY` | Chave JWT (**ALTERE!**) | *(vazio - gere com `python -c "import secrets;print(secrets.token_urlsafe(32))"`)* |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Expiração access token | `1440` (24h) |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Expiração refresh token | `30` |
| `DATABASE_URL` | String de conexão SQLite | `sqlite+aiosqlite:///./data/hncc.db` |
| `SCAN_INTERVAL_MINUTES` | Intervalo scan automático | `5` |
| `ARP_SCAN_TIMEOUT` | Timeout ARP scan (segundos) | `3` |
| `NMAP_PATH` | Caminho do nmap | `nmap` |
| `SHARES_ROOT` | Pasta raiz compartilhamentos | `./shares` |
| `MAX_UPLOAD_SIZE_MB` | Tamanho máximo upload | `2048` (2GB) |
| `FFMPEG_PATH` | Caminho do ffmpeg | `ffmpeg` |
| `THUMBNAIL_CACHE_DIR` | Cache de thumbnails | `./cache/thumbnails` |
| `ARGON2_TIME_COST` | Iterações Argon2 | `3` |
| `ARGON2_MEMORY_COST` | Memória Argon2 (KB) | `65536` |
| `ARGON2_PARALLELISM` | Paralelismo Argon2 | `4` |

Reinicie o servidor após qualquer alteração (`PARAR.bat` → `INICIAR.bat`).

---

## Licença

Este projeto é open-source. Sinta-se livre para usar, modificar e distribuir.

---

## Créditos

- **FastAPI** - Framework web moderno e rápido
- **SQLAlchemy** - ORM assíncrono
- **Chart.js** - Gráficos no dashboard
- **Sunshine** - Host de streaming de jogos (LizardByte)
- **Moonlight** - Cliente de streaming (projeto complementar)
- **FFmpeg** - Processamento de vídeo/áudio
- **Nmap** - Scanner de rede
- **Scapy** - Manipulação de pacotes (ARP scan)
- **Argon2** - Hash de senhas seguro
- **Passlib** - Biblioteca de hashing
- **python-jose** - JWT tokens

---

**Desenvolvido para controle total da sua rede local, com privacidade e performance.** 🏠🌐