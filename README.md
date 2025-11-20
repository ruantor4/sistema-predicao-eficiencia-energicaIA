# Documentação de Instalação e Execução do Sistema

> **Autor:** Ruan Torquato  
> **Versão do Documento:** 1.0  
> **Data:** 09/10/2025  
> **Tecnologias Principais:** Python 3.13 · Django 5.2.7 · PostgreSQL · Docker · pgAdmin  

---

##  1. Pré-requisitos

Antes de iniciar a instalação, verifique se seu ambiente atende aos requisitos mínimos:

- **Sistema Operacional:** Ubuntu 22.04 LTS ou Windows 10/11  
- **Python:** versão 3.13 ou superior  
- **Git:** instalado e configurado  
- **Docker e Docker Compose:** instalados e em execução  
- **Navegador Web:** atualizado (para acesso ao pgAdmin e à aplicação)  

---

##  2. Preparando o Ambiente

### 2.1 Instalação do Python e dependências

Instale o Python e verifique a versão:

```bash
python --version
```

### 2.2 Instalação das bibliotecas do projeto

```bash
pip install django==5.2.7
pip install pillow
pip install psycopg2-binary     # para desenvolvimento
# ou
pip install psycopg2             # para produção
```

> 💡 Caso o projeto tenha um arquivo `requirements.txt`, execute:
> ```bash
> pip install -r requirements.txt
> ```

---

##  3. Instalação e Configuração do Docker

### 3.1 Adicionar certificados oficiais

```bash
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
```

### 3.2 Adicionar repositórios do Docker

```bash
echo   "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu   $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" |   sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
```

### 3.3 Instalar Docker e plugins necessários

```bash
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

### 3.4 Verificar e iniciar o serviço

```bash
sudo systemctl status docker
sudo systemctl start docker
```

### 3.5 Testar instalação

```bash
sudo docker run hello-world
```

---

##  4. Criação do Ambiente Virtual

### 4.1 Criar ambiente virtual

**Windows:**
```bash
python -m venv .dev
```

**Linux:**
```bash
python -m venv .venv
```

### 4.2 Ativar ambiente virtual

**Windows (PowerShell):**
```bash
.\.dev\Scripts\activate
```

**Linux:**
```bash
source .venv/bin/activate
```

---

##  5. Estrutura Docker do Banco de Dados

- **Rede Docker:** `pg_net`  
- **Volume do PostgreSQL:** `pg_data`  
- **Volume do pgAdmin:** `pgadmin_data`  
- **Serviços:**
  - `postgres` → Banco de dados  
  - `pgadmin` → Interface web de administração  

---

##  6. Subindo os Containers Manualmente

### 6.1 Criar rede e volumes

```bash
docker network create pg_net
docker volume create pg_data
docker volume create pgadmin_data
```

### 6.2 Subir o container PostgreSQL

```bash
docker run -d   --name postgres   --network pg_net   -e POSTGRES_USER=admin   -e POSTGRES_PASSWORD=admin   -e POSTGRES_DB=estoque_db   -v pg_data:/var/lib/postgresql/data   -p 5432:5432   postgres:17
```

### 6.3 Subir o container pgAdmin

```bash
docker run -d   --name pgadmin   --network pg_net   -e PGADMIN_DEFAULT_EMAIL=admin@admin.com   -e PGADMIN_DEFAULT_PASSWORD=admin   -v pgadmin_data:/var/lib/pgadmin   -p 5050:80   dpage/pgadmin4
```

### 6.4 Reiniciar automaticamente com o sistema

```bash
docker update --restart=always postgres
docker update --restart=always pgadmin
```

---

##  7. Conexão com o Banco de Dados

No **pgAdmin** (após login):

- **URL:** http://localhost:5050  
- **Login:** admin@admin.com  
- **Senha:** admin  

Adicione um novo servidor:

| Campo | Valor |
|--------|--------|
| **Name** | PostgreSQL Local |
| **Host name/address** | postgres |
| **Port** | 5432 |
| **Username** | admin |
| **Password** | admin |

> O nome do container (`postgres`) é o host interno dentro da rede Docker.

---

##  8. Configuração do Banco no Django

No arquivo `settings.py`, configure o banco:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'estoque_db',
        'USER': 'admin',
        'PASSWORD': 'admin',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

---

##  9. Migrações e Execução do Sistema

### 9.1 Criar e aplicar migrações

```bash
python manage.py makemigrations
python manage.py migrate
```

### 9.2 Criar superusuário

```bash
python manage.py createsuperuser
```

### 9.3 Rodar aplicação

```bash
python manage.py runserver
```

Acesse no navegador:
```
http://localhost:8000
```

---

## 10. Comandos úteis do Docker

```bash
docker ps                      # listar containers ativos
docker stop postgres pgadmin   # parar containers
docker start postgres pgadmin  # iniciar containers novamente
docker logs postgres           # ver logs do PostgreSQL
docker rm -f postgres pgadmin  # remover containers
```

---

## 11. Teste e Validação do Sistema

Após subir o servidor:

- Verifique acesso ao Django Admin:  
  **http://localhost:8000/admin**
- Verifique acesso ao pgAdmin:  
  **http://localhost:5050**

Se ambos funcionarem corretamente, o ambiente está pronto 🎉

---

## 12. Manutenção e Atualização

- Para atualizar as dependências:
  ```bash
  pip freeze > requirements.txt
  ```
- Para reconstruir containers:
  ```bash
  docker compose down
  docker compose up -d --build
  ```

---
