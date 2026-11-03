# Home Network Control Center

<div align="center">

![Home Network Control Center](https://img.shields.io/badge/HNCC-Home%20Network%20Control%20Center-00d4ff?style=for-the-badge&logo=home-assistant&logoColor=white)
![Version](https://img.shields.io/badge/Version-1.0.0-00d4ff?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey?style=for-the-badge)

**Central de controle da sua rede doméstica — servidor local com HUD futurista** 🏠🌐

[![Made by TioYuko](https://img.shields.io/badge/Made%20by-TioYuko-ff6b6b?style=flat-square&logo=github&logoColor=white)](https://github.com/TioYuko)
[![Vibe Coded](https://img.shields.io/badge/Vibe%20Coded-✨-ff6b6b?style=flat-square)](https://github.com/TioYuko)

</div>

---

## 📸 Screenshots

<div align="center">

| Dashboard | Monitor de Rede | Media Center |
|:---------:|:---------------:|:------------:|
| ![Dashboard](docs/screenshots/dashboard.png) | ![Network](docs/screenshots/network.png) | ![Media](docs/screenshots/media.png) |

| Gerenciador de Arquivos | Central de Segurança | Central de Computação |
|:----------------------:|:-------------------:|:---------------------:|
| ![Files](docs/screenshots/files.png) | ![Security](docs/screenshots/security.png) | ![Computing](docs/screenshots/computing.png) |

> 💡 **Dica:** Adicione suas próprias screenshots na pasta `docs/screenshots/` para documentar sua instalação!

</div>

---

## 🚀 Início Rápido

### 1️⃣ Instalar
Execute o arquivo `INSTALAR.bat`. Ele irá:
- ✅ Verificar se Python 3.11+ está instalado
- ✅ Criar um ambiente virtual Python isolado
- ✅ Instalar todas as dependências
- ✅ Preparar pastas e configurações

### 2️⃣ Iniciar
Execute `INICIAR.bat`. O servidor irá:
- 🔍 Detectar automaticamente o IP da sua rede local
- 🌐 Exibir o endereço para acesso (ex: `http://192.168.1.100:8000`)
- 👤 Criar o usuário admin na primeira execução

### 3️⃣ Acessar
Abra o navegador em **qualquer dispositivo** da sua rede e acesse o endereço exibido.

| Credencial | Valor |
|:----------:|:-----:|
| **Usuário** | `admin` |
| **Senha** | `Admin@1234` |

> ⚠️ **ALTERE A SENHA IMEDIATAMENTE APÓS O PRIMEIRO ACESSO!**
> Vá em **Configurações → Alterar Senha**.

### 4️⃣ Parar
Execute `PARAR.bat` para encerrar o servidor.

---

## 📋 Pré-requisitos

| Software | Versão | Status | Descrição |
|:---------|:------:|:------:|:----------|
| ![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white) | 3.11+ | ✅ **Obrigatório** | Runtime principal |
| ![Nmap](https://img.shields.io/badge/Nmap-Latest-4682B4?style=flat&logo=nmap&logoColor=white) | Any | 🔶 Recomendado | Scan de portas/serviços preciso |
| ![FFmpeg](https://img.shields.io/badge/FFmpeg-Latest-00A8E8?style=flat&logo=ffmpeg&logoColor=white) | Any | 🔶 Recomendado | Thumbnails de vídeo |
| ![Sunshine](https://img.shields.io/badge/Sunshine-Latest-FF6B35?style=flat&logo=steam&logoColor=white) | Latest | 🔶 Opcional | Streaming jogos/desktop |

### 🐍 Instalar Python
1. Acesse <https://www.python.org/downloads/>
2. Baixe o instalador para Windows
3. **⚠️ IMPORTANTE:** Marque a opção **"Add Python to PATH"**
4. Conclua a instalação

### 🔍 Instalar Nmap (opcional - scan de portas preciso)
1. Acesse <https://nmap.org/download.html>
2. Baixe e instale o Nmap para Windows
3. O scanner de rede funcionará com maior precisão

### 🎬 Instalar FFmpeg (opcional - thumbnails de vídeo)
1. Acesse <https://ffmpeg.org/download.html>
2. Baixe o build para Windows e extraia
3. Adicione a pasta `bin` ao PATH do sistema
4. Thumbnails de vídeo serão gerados automaticamente

### 🎮 Instalar Sunshine (opcional - Central de Computação)
1. Acesse <https://github.com/LizardByte/Sunshine/releases>
2. Baixe o instalador Windows mais recente (`sunshine-windows-installer.exe`)
3. Execute a instalação (pode requerer reinicialização)
4. O Sunshine roda como serviço nas portas **47989** (stream) e **47990** (web UI)

> **Nota:** O Sunshine é um host de streaming open-source compatível com clientes **Moonlight**. Permite jogar seus jogos do PC em outros dispositivos (celular, tablet, TV, outro PC) pela rede local.

---

## ✨ Funcionalidades

<div align="center">

| Módulo | Descrição | Destaque |
|:------:|:----------|:--------:|
| 📊 **Dashboard** | Status tempo real (CPU, RAM, disco), gráfico tráfego rede, dispositivos online, alertas | Temps real via WebSocket |
| 🌐 **Monitor de Rede** | Mapa visual, tabela IP/MAC/fabricante/tipo/status, filtros, histórico, scan automático 5min | ARP + Nmap |
| 📁 **Central de Compartilhamento** | Shares, navegação explorer-like, upload 2GB, download, permissões por dispositivo (R/W/D) | Path traversal protection |
| 🎬 **Media Center** | Scan mídia, player HTML5 com seek, thumbnails FFmpeg, auto-organização Filmes/Séries/Música | Range requests |
| 📱 **Gerenciador Dispositivos** | Lista, autorizar/revogar, pareamento QR code, bloqueio, detecção tipo, fabricante OUI | Auto device typing |
| 🛡️ **Central de Segurança** | Índice segurança 0-100%, alertas desconhecidos, auditoria completa, eventos conexão, falhas login | Security scoring |
| ⚙️ **Configurações** | Alterar senha, gerenciar usuários (Admin/User/Viewer), info servidor tempo real | Multi-user RBAC |
| 🎮 **Central de Computação** | Sunshine integration, apps discovery, perfis qualidade, QR codes, desktop streaming | Moonlight ready |

</div>

---

## 📁 Central de Compartilhamento (Gerenciador de Arquivos) ⭐

### Principais recursos:
- 📂 **Crie compartilhamentos** apontando para pastas do seu computador
- 🗂️ **Navegue pela estrutura** pelo navegador (estilo explorador de arquivos)
- ⬆️ **Upload drag & drop** ou seleção (até **2GB** por arquivo)
- ⬇️ **Download direto** de qualquer arquivo
- 📝 **Criação de pastas**, renomear, mover, copiar, excluir
- 🔐 **Permissões por dispositivo**: `READ` (leitura), `WRITE` (escrita/upload), `DELETE` (exclusão)
- 📄 Suporte a **compartilhamentos de arquivo único** ou **pastas inteiras**
- 🛡️ **Validação de path traversal** para segurança

### Como usar:

```mermaid
graph LR
    A[Aba Arquivos] --> B[Novo Compartilhamento]
    B --> C[Nome: Meus Documentos]
    C --> D[Caminho: documentos]
    D --> E[Tipo: Pasta]
    E --> F[Criar]
    F --> G[Configurar Permissões]
    G --> H[Dispositivos → Permissões]
```

1. Acesse a aba **📁 Arquivos** no menu lateral
2. Clique em **"+ Novo Compartilhamento"**
3. Dê um **nome** (ex: `"Meus Documentos"`, `"Vídeos da Família"`)
4. Informe o **caminho relativo** à pasta `backend/shares/`:
   - `documentos` → `backend/shares/documentos/`
   - `videos/filmes` → `backend/shares/videos/filmes/`
5. Escolha o tipo: **📁 Pasta** (navegável) ou **📄 Arquivo** (download direto)
6. Clique em **Criar**
7. Para dar acesso: vá em **📱 Dispositivos**, selecione um dispositivo autorizado e configure as permissões no compartilhamento

> 💡 **Dica Pro:** A pasta raiz `backend/shares/` já vem com subpastas criadas:
> - 📹 `Videos/`
> - 🎵 `Musicas/`
> - 📄 `Documentos/`
> - 🖼️ `Imagens/`
> 
> Use essas ou crie suas próprias!

---

## 🎮 Central de Computação (Sunshine Integration) ⭐

Integração completa com **Sunshine** para streaming de jogos e desktop remoto via **Moonlight**.

### 🌟 Funcionalidades

- ▶️ **Iniciar/Parar Sunshine** com um clique
- 📊 **Status em tempo real**: versão, uptime, sessões ativas, max sessões
- 🔍 **Descoberta automática de apps/jogos**:
  - Via API do Sunshine (apps configurados)
  - Scan do sistema (Steam, Epic, GOG, Battle.net, Program Files)
  - Categorização automática: 🎮 Jogos, 🌐 Navegadores, 🔧 Utilitários, ❓ Desconhecidos
- 🎯 **Perfis de qualidade pré-definidos**:

| Perfil | 🎨 Resolução | 🎞️ FPS | 📶 Bitrate | 🎬 Codec | 🎯 Uso Recomendado |
|:------:|:-----------:|:-----:|:---------:|:-------:|:------------------|
| **Ultra** | 4K (3840×2160) | 60 | 80 Mbps | HEVC | Rede gigabit, cliente 4K |
| **Alto** | 1440p (2560×1440) | 120 | 50 Mbps | HEVC | Jogos competitivos, 144Hz |
| **Equilibrado** | 1080p (1920×1080) | 60 | 25 Mbps | H.264 | **Padrão**, qualidade/desempenho |
| **Econômico** | 720p (1280×720) | 30 | 10 Mbps | H.264 | Wi-Fi fraco, dados móveis |
| **Mobile** | 720p (1280×720) | 60 | 15 Mbps | HEVC | Celulares/tablets modernos |

- 📱 **Gerar link + QR Code** para cada perfil
- 👁️ **Sessões ativas** em tempo real
- ⚙️ **Configuração Sunshine** pela interface (host, portas, user, pass, encoder, bitrate, FPS, resolução, GPU, HEVC/AV1)
- 🎮 **Múltiplos encoders**: NVIDIA NVENC, AMD AMF, Intel QuickSync, Software (CPU)

---

### 🛠️ Como configurar e usar o Sunshine

#### 1️⃣ Instalação do Sunshine
```bash
# Baixe em: https://github.com/LizardByte/Sunshine/releases/latest
# Execute o instalador .exe
# Reinicie o PC se solicitado
```

#### 2️⃣ Configuração inicial (Web UI do Sunshine)
1. Acesse `http://localhost:47990` no navegador (apenas no PC servidor)
2. Crie usuário/senha para o Sunshine (ex: `sunshine` / `sua_senha_forte`)
3. Configure:
   - **Video Encoder**: Seu GPU (NVIDIA NVENC / AMD AMF / Intel QSV)
   - **Resolution**: 1920×1080 (ou 3840×2160 se 4K)
   - **FPS**: 60
   - **Bitrate**: 25000 kbps (25 Mbps) para 1080p60
   - **HEVC**: ✅ Ativado (Moonlight moderno suporta)
   - **Audio**: Opus 128kbps

#### 3️⃣ Configuração no HNCC
1. Aba **🎮 Central de Computação** → **⚙️ Configuração**
2. Preencha:
   | Campo | Valor |
   |:------|:------|
   | **Host** | `0.0.0.0` |
   | **Porta Stream** | `47989` |
   | **Porta Web UI** | `47990` |
   | **Usuário** | `sunshine` |
   | **Senha** | *sua senha do Sunshine* |
   | **Encoder** | NVENC / AMF / QSV / Software |
   | **Max Bitrate** | `25000` (kbps) |
   | **Max FPS** | `60` |
   | **Resolução** | `1920x1080` |
   | **GPU Device ID** | *(opcional - auto)* |
   | **Auto-start** | ☑️ Marcado |
3. Clique em **💾 Salvar Configuração**

#### 4️⃣ Adicionar Jogos/Apps

**Opção A - Via Web UI do Sunshine (recomendado):**
1. `http://localhost:47990` → aba **Apps** → **Add App**
2. Preencha: nome, executável, argumentos, diretório de trabalho
3. Adicione imagem/capa (opcional) → **Save**

**Opção B - Descoberta automática pelo HNCC:**
1. Aba **🎮 Central de Computação** → **📱 Aplicativos**
2. Clique **🔄 Atualizar** → scan do sistema
3. Apps encontrados listados → clique para detalhes

#### 5️⃣ Conectar via Moonlight (Cliente)

**No dispositivo cliente (celular, tablet, TV, outro PC):**

| Plataforma | Onde baixar |
|:-----------|:------------|
| 📱 Android | Play Store / F-Droid |
| 🍎 iOS | App Store |
| 💻 Windows/macOS/Linux | <https://moonlight-stream.org/> / Flatpak / Scoop / Chocolatey |
| 📺 Apple TV / Android TV / Fire TV | Loja respectiva |

**Conexão direta:**
1. Instale **Moonlight** → abra → detecta automaticamente o Sunshine
2. Se não detectar: adicione manualmente `IP_DO_SERVIDOR:47989`
3. Login com usuário/senha do Sunshine

**Via HNCC (mais fácil!):**
1. Aba **🎮 Central de Computação** → **📊 Dashboard**
2. Clique botão **Quick Stream** (Ultra, Alto, Equilibrado, Econômico, Mobile)
3. Ou **📱 Aplicativos** → escolha jogo → **▶️ Iniciar**
4. Será gerado:
   - 🔗 **Link `moonlight://...`** → abre direto no Moonlight
   - 📱 **QR Code** → escaneie com celular
   - 🔗 **Link `sunshine://...`** → alternativo
5. No Moonlight, o stream inicia automaticamente!

#### 6️⃣ Streaming de Desktop Completo
1. Aba **🎮 Central de Computação** → **📊 Dashboard**
2. Clique **🖥️ Iniciar Desktop** (ou perfil "Equilibrado" no Quick Stream)
3. Conecte via Moonlight → verá toda a área de trabalho do PC servidor
4. Use para: trabalho remoto, suporte técnico, apresentações, apps não-jogos

---

### 🌐 Requisitos de Rede para Boa Experiência

| Tipo | Recomendação |
|:----|:-------------|
| 🔌 **Cabeada (Ethernet)** | Melhor latência e estabilidade |
| 📶 **Wi-Fi** | 5GHz obrigatório, próximo ao roteador |
| ⚡ **Latência alvo** | **< 20ms** na rede local |
| 📊 **Bitrate** | Ajuste conforme sua rede (teste "Equilibrado") |

> 🔒 **SEGURANÇA:** O Sunshine só aceita conexões da rede local por padrão. **NUNCA exponha as portas 47989/47990 para a internet** sem VPN (Tailscale, WireGuard) ou túnel seguro.

---

## 📂 Estrutura de Pastas

```text
home-network-control/
├── 📄 INSTALAR.bat           ← Execute para instalar
├── 📄 INICIAR.bat            ← Execute para iniciar o servidor
├── 📄 PARAR.bat              ← Execute para parar o servidor
├── 📄 DESINSTALAR.bat        ← Remove o ambiente virtual
├── 📄 README.md              ← Esta documentação
│
├── 📁 backend/
│   ├── 📁 app/
│   │   ├── 📄 main.py        ← FastAPI principal
│   │   ├── 📄 config.py      ← Configurações (pydantic-settings)
│   │   ├── 📄 database.py    ← SQLite (aiosqlite)
│   │   ├── 📁 models/        ← Modelos SQLAlchemy
│   │   ├── 📁 schemas/       ← Schemas Pydantic
│   │   ├── 📁 routers/       ← Endpoints API REST
│   │   └── 📁 services/      ← Lógica de negócio
│   ├── 📁 data/              ← Banco SQLite (criado ao iniciar)
│   ├── 📁 shares/            ← Pasta raiz compartilhamentos
│   │   ├── 📹 Videos/
│   │   ├── 🎵 Musicas/
│   │   ├── 📄 Documentos/
│   │   └── 🖼️ Imagens/
│   ├── 📁 cache/thumbnails/  ← Cache thumbnails vídeo
│   ├── 📄 .env               ← Config local (criado pelo instalador)
│   └── 📄 requirements.txt   ← Dependências Python
│
├── 📁 frontend/
│   ├── 📄 index.html         ← HUD principal (SPA)
│   └── 📁 static/
│       ├── 📄 css/style.css  ← Estilos interface
│       └── 📁 js/            ← Módulos JavaScript
│
└── 📁 venv/                  ← Ambiente virtual (ignorado pelo git)
```

---

## 📡 API REST

Documentação interativa disponível em:

| Interface | URL |
|:---------:|:----|
| **Swagger UI** | `http://localhost:8000/api/docs` |
| **ReDoc** | `http://localhost:8000/api/redoc` |

### Principais Endpoints

<details>
<summary><b>🔐 Autenticação</b></summary>

```http
POST   /api/auth/login           # Login (access + refresh token)
POST   /api/auth/refresh         # Renovar access token
GET    /api/auth/me              # Usuário atual
POST   /api/auth/change-password # Alterar senha
```

</details>

<details>
<summary><b>🌐 Rede</b></summary>

```http
GET    /api/network/devices      # Listar dispositivos
POST   /api/network/scan         # Iniciar varredura
GET    /api/network/devices/{id} # Detalhes dispositivo
POST   /api/network/pair         # Solicitar pareamento
GET    /api/network/devices/{id}/history # Histórico conexões
```

</details>

<details>
<summary><b>📁 Arquivos</b></summary>

```http
GET    /api/files/shares                    # Listar compartilhamentos
POST   /api/files/shares                    # Criar compartilhamento
GET    /api/files/shares/{id}/contents      # Navegar pastas
POST   /api/files/shares/{id}/upload        # Upload arquivo
GET    /api/files/shares/{id}/download      # Download arquivo
DELETE /api/files/shares/{id}/contents      # Excluir arquivo/pasta
POST   /api/files/shares/{id}/permissions   # Conceder permissão
DELETE /api/files/shares/{id}/permissions   # Revogar permissão
```

</details>

<details>
<summary><b>🎬 Mídia</b></summary>

```http
GET /api/media/library        # Biblioteca (filmes/séries/música)
GET /api/media/stream         # Stream vídeo/áudio (range requests)
GET /api/media/thumbnail      # Thumbnail vídeo
POST /api/media/scan          # Escanear compartilhamentos
```

</details>

<details>
<summary><b>📱 Dispositivos</b></summary>

```http
GET  /api/devices                    # Lista dispositivos
POST /api/devices/{id}/authorize     # Autorizar dispositivo
POST /api/devices/{id}/block         # Bloquear dispositivo
POST /api/devices/{id}/unblock       # Desbloquear dispositivo
DELETE /api/devices/{id}             # Remover dispositivo
```

</details>

<details>
<summary><b>🛡️ Segurança</b></summary>

```http
GET /api/security/overview    # Visão geral (score, stats)
GET /api/security/alerts      # Alertas de segurança
GET /api/security/audit       # Log de auditoria
GET /api/security/events      # Eventos de conexão
```

</details>

<details>
<summary><b>🎮 Computação (Sunshine)</b></summary>

```http
GET  /api/computing/status          # Status Sunshine
POST /api/computing/start           # Iniciar Sunshine
POST /api/computing/stop            # Parar Sunshine
GET  /api/computing/apps            # Apps/jogos descobertos
POST /api/computing/launch          # Iniciar stream (app/desktop)
GET  /api/computing/stream-url      # Gerar URL + QR Code
GET  /api/computing/config          # Obter configuração
POST /api/computing/config          # Atualizar configuração
GET  /api/computing/sessions        # Sessões ativas/histórico
```

</details>

<details>
<summary><b>🔌 WebSocket (Tempo Real)</b></summary>

```http
WS /ws?token=<JWT>  # Stats sistema, dispositivos, alertas, sessões
```

</details>

---

## 🔧 Solução de Problemas

<details>
<summary><b>🐍 "Python não encontrado"</b></summary>

Instale o Python e marque **"Add to PATH"** durante a instalação.
</details>

<details>
<summary><b>🔌 "Porta 8000 em uso"</b></summary>

Mude a porta editando `backend/.env`:
```ini
PORT=8001
```
</details>

<details>
<summary><b>🔍 Scan de rede não funciona</b></summary>

- Execute `INICIAR.bat` **como Administrador** (clique direito → "Executar como administrador")
- Scapy/ARP requer privilégios de rede no Windows
- Instale **Nmap** para scan de portas/serviços mais preciso
</details>

<details>
<summary><b>🖼️ Thumbnails não aparecem</b></summary>

- Instale **FFmpeg** e adicione ao PATH
- Thumbnails são gerados na primeira reprodução do vídeo
</details>

<details>
<summary><b>📱 Dispositivos não aparecem no mapa</b></summary>

- Execute varredura manual: "🔍 Escanear Agora"
- Verifique se servidor e dispositivos estão na mesma rede Wi-Fi
- Alguns IoT/impressoras podem não responder a ARP
</details>

<details>
<summary><b>🎮 Sunshine não inicia / não conecta</b></summary>

- Verifique instalação: `C:\Program Files\Sunshine\sunshine.exe`
- Acesse `http://localhost:47990` → ver se Web UI responde
- Firewall: portas **47989** (TCP/UDP) e **47990** (TCP) liberadas
- No Windows, Sunshine pode precisar rodar como serviço → reinicie PC
- Logs: `%APPDATA%\Sunshine\logs\`
</details>

<details>
<summary><b>📱 Moonlight não detecta o Sunshine</b></summary>

- Mesma rede Wi-Fi (não guest network)
- Firewall Windows: permitir "Sunshine" em redes privadas
- Conecte manualmente: `IP_DO_PC:47989` no Moonlight
- Verifique usuário/senha do Sunshine na configuração do HNCC
</details>

<details>
<summary><b>📉 Performance ruim no streaming</b></summary>

- Use cabo de rede (Ethernet) no PC servidor
- Wi-Fi 5GHz no cliente, próximo ao roteador
- Reduza bitrate/resolução no perfil de qualidade
- Verifique se encoder hardware (NVENC/AMF/QSV) está ativo (não CPU)
- Feche apps pesados no PC servidor
</details>

---

## 🔒 Segurança

- 🏠 **Apenas rede local** por padrão
- 🔐 Senhas com hash **Argon2id** (configurável)
- 🎫 Autenticação **JWT** (access + refresh tokens)
- 📋 Auditoria completa para ações relevantes
- ✅ Dispositivos precisam autorização explícita
- 🛡️ Validação path traversal no gerenciador de arquivos
- ⏱️ Rate limiting e proteção brute force no login

> **⚠️ NUNCA exponha este servidor diretamente para a internet** sem configurar:
> 1. 🔐 HTTPS (certificado válido ou self-signed com CA própria)
> 2. 🔑 Autenticação adicional (2FA, VPN, Tailscale, WireGuard)
> 3. 🛡️ Firewall restringindo IPs de origem
> 4. 🔀 Reverse proxy (nginx/Traefik) com segurança extra
>
> Para acesso remoto seguro, use **Tailscale** ou **WireGuard** (VPN mesh).

---

## ⚙️ Configuração (.env)

Edite `backend/.env` para ajustar:

| Variável | Descrição | Padrão |
|:---------|:----------|:-------|
| `HOST` | Interface bind | `0.0.0.0` |
| `PORT` | Porta servidor | `8000` |
| `DEBUG` | Modo debug (auto-reload) | `false` |
| `SECRET_KEY` | Chave JWT (**ALTERE!**) | *gere: `python -c "import secrets;print(secrets.token_urlsafe(32))"`* |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Expiração access token | `1440` (24h) |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Expiração refresh token | `30` |
| `DATABASE_URL` | String conexão SQLite | `sqlite+aiosqlite:///./data/hncc.db` |
| `SCAN_INTERVAL_MINUTES` | Intervalo scan automático | `5` |
| `ARP_SCAN_TIMEOUT` | Timeout ARP scan (seg) | `3` |
| `NMAP_PATH` | Caminho nmap | `nmap` |
| `SHARES_ROOT` | Pasta raiz compartilhamentos | `./shares` |
| `MAX_UPLOAD_SIZE_MB` | Tamanho máximo upload | `2048` (2GB) |
| `FFMPEG_PATH` | Caminho ffmpeg | `ffmpeg` |
| `THUMBNAIL_CACHE_DIR` | Cache thumbnails | `./cache/thumbnails` |
| `ARGON2_TIME_COST` | Iterações Argon2 | `3` |
| `ARGON2_MEMORY_COST` | Memória Argon2 (KB) | `65536` |
| `ARGON2_PARALLELISM` | Paralelismo Argon2 | `4` |

> Reinicie após alterações: `PARAR.bat` → `INICIAR.bat`

---

## 📄 Licença

Este projeto é **open-source** (MIT). Sinta-se livre para usar, modificar e distribuir.

---

## 👨‍💻 Créditos

<div align="center">

### Desenvolvido com ❤️ por **TioYuko** — *Vibe Coder* ✨

[![GitHub](https://img.shields.io/badge/GitHub-TioYuko-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/TioYuko)

</div>

### Tecnologias Utilizadas

| Tecnologia | Descrição |
|:-----------|:----------|
| ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white) | Framework web moderno e rápido |
| ![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=flat&logo=sqlalchemy&logoColor=white) | ORM assíncrono |
| ![Chart.js](https://img.shields.io/badge/Chart.js-FF6384?style=flat&logo=chartdotjs&logoColor=white) | Gráficos no dashboard |
| ![Sunshine](https://img.shields.io/badge/Sunshine-FF6B35?style=flat&logo=steam&logoColor=white) | Host streaming jogos (LizardByte) |
| ![Moonlight](https://img.shields.io/badge/Moonlight-00A8E8?style=flat&logo=moonlight&logoColor=white) | Cliente streaming |
| ![FFmpeg](https://img.shields.io/badge/FFmpeg-00A8E8?style=flat&logo=ffmpeg&logoColor=white) | Processamento vídeo/áudio |
| ![Nmap](https://img.shields.io/badge/Nmap-4682B4?style=flat&logo=nmap&logoColor=white) | Scanner de rede |
| ![Scapy](https://img.shields.io/badge/Scapy-00BFFF?style=flat&logo=python&logoColor=white) | Manipulação pacotes (ARP) |
| ![Argon2](https://img.shields.io/badge/Argon2-FF6B6B?style=flat&logo=lock&logoColor=white) | Hash senhas seguro |
| ![Passlib](https://img.shields.io/badge/Passlib-4CAF50?style=flat&logo=python&logoColor=white) | Biblioteca hashing |
| ![python-jose](https://img.shields.io/badge/python--jose-000000?style=flat&logo=jsonwebtokens&logoColor=white) | JWT tokens |
| ![Pydantic](https://img.shields.io/badge/Pydantic-E92063?style=flat&logo=pydantic&logoColor=white) | Validação dados |
| ![Uvicorn](https://img.shields.io/badge/Uvicorn-000000?style=flat&logo=uvicorn&logoColor=white) | Servidor ASGI |

---

<div align="center">

**🏠 Home Network Control Center — Controle total da sua rede local, com privacidade e performance** 🌐

*Made with ☕ and ✨ by TioYuko*

</div>