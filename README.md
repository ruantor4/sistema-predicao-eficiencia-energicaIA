# Sistema de Gestão - Django

Aplicação desenvolvida em **[Django](https://docs.djangoproject.com/en/stable/)** para previsão de cargas térmicas (aquecimento e resfriamento) de edificações, utilizando um modelo de **Machine Learning** treinado previamente.  
Possui autenticação completa, registro de logs, dashboard analítico com gráficos e exportação em PDF.

O projeto foi construído seguindo boas práticas de arquitetura com **[Class-Based Views (CBV)](https://docs.djangoproject.com/en/5.2/topics/class-based-views/)**, **[tratamento de exceções](https://docs.djangoproject.com/en/5.2/ref/exceptions/)**, **[type hints](https://peps.python.org/pep-0484/)**, e **[documentação padrão Docstring](https://peps.python.org/pep-0257/)** nos métodos.


---
## Funcionalidades

- ###  Autenticação
  - Login / Logout
  - Recuperação de senha via e-mail
  - Proteção de rotas com `LoginRequiredMixin`

- ### Gerenciamento de Usuários
  - CRUD completo  
  - Proteção ao superusuário  
  - Modelo customizado herdando de `AbstractUser`

- ### Predições (IA)
  - Entrada manual das variáveis
  - Modelo `MultiOutputRegressor + GradientBoostingRegressor`
  - Pré-processamento com `StandardScaler`
  - Resultado imediato da previsão

- ### Dashboard Avançado
  - Estatísticas básicas
  - Gráficos profissionais (Chart.js)
  - **Insights automáticos**
  - **Insights preditivos usando o modelo**
  - Exportação em PDF

- ### Registro de Logs
  - Registro automático via `LogSystem`
  - Guarda usuário, ação, status e mensagem


---

## Stack e Dependências

| Categoria                           | Tecnologia / Lib                                                                                                                         |
|-------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------|
| Linguagem & Frameworks              | **[Python 3.13](https://docs.python.org/pt-br/3.13/contents.html)**, **[Django 5.2.7](https://docs.djangoproject.com/pt-br/5.2/)**       |
| Banco de dados                      | **[PostgreSQL](https://www.postgresql.org/docs/)** via      **[psycopg2 2.9.11](https://www.psycopg.org/docs/)**                         |
| Machine Learning                    | **[scikit-learn](https://scikit-learn.org/stable/)**                                                                                     |
| Configuração(variáveis de ambiente) | **[python-decouple 3.8](https://pypi.org/project/python-decouple/)**, **[python-dotenv 1.1.1](https://pypi.org/project/python-dotenv/)** |
| Ambiente replicável                 | **[Docker](https://docs.docker.com/)**                                                                                                   |
| Geração de PDF                      | **[xhtml2pdf](https://xhtml2pdf.readthedocs.io/en/latest/)**                                                                             | 
| Front-end                           | **[Bootstrap](https://getbootstrap.com/docs/5.3/getting-started/introduction/)**, **[Chart.js](https://www.chartjs.org/docs/latest/)**                                       |

---
## Visão geral da estrutura de diretórios

```
SISTEMA_PREDICAO/
├── autenticacao/               # App de login, logout, reset de senha
│
├── core/                       # Páginas centrais, layout base e logs
│   ├── utils.py                # Função report_log()
│
├── predicao/                   # Aplicação de IA
│   ├── model_loader.py         # Carrega modelo e scaler
│   ├── services/
│   │   └── insights_service.py # Insights automáticos e preditivos
│   ├── templates/predicao/
│   │   ├── criar_predicao.html
│   │   ├── listar_predicoes.html
│   │   ├── dashboard.html
│   │   ├── resultado.html
│
├── usuario/                    # App de gerenciamento de usuários
│
├── project/                    # Configurações globais do Django
├── static/                     # Arquivos estáticos globais
├── staticfiles/                # Pasta coletada
├── manage.py
└── README.md
```


---
## Variáveis de Ambiente

Crie um arquivo `.env` segundo o arquivo `.env.example`:

| Variável          | Descrição                                                        | Exemplo            |
|-------------------|------------------------------------------------------------------|--------------------|
| `DEBUG`           | `True` em dev, `False` em produção                               | `True`             |
| `SECRET_KEY`      | Chave secreta do Django                                          | `SECRET_KEY` |
| `ALLOWED_HOSTS`   | Hosts permitidos                                                 | `'*' Todos` |
| `EMAIL_HOST_USER`       | E-mail usado no SMTP                                | `admin@admin.com`            |
| `EMAIL_HOST_PASSWORD`  | Senha do e-mail                                            | `senha do e-mail`       |
| `DB_NAME`         | Nome do banco                                                  | `estoque_db`         |
| `DB_USER`         | Usuário do banco                                               | `admin`         |
| `DB_PASSWORD`     | Senha do banco                                                 | `admin`         |
| `DB_HOST`         | Host/IP do banco                                               | `localhost`        |
| `DB_PORT`         | Porta (padrão 5432)                                          | `5432`             |

Observação: O nome do container **postgres** é o host interno dentro da rede Docker.


---
## Instalação e Execução

Certifique-se de ter as dependências do sistema instaladas, como **Python 3.11** e **PostgreSQL**.

```bash
  $ sudo apt update && sudo apt install python3.11 python3.11-venv python3-pip
```
Clone este repositório com o git **ou** baixe o `.zip` e extraia-o.

Em um terminal, navegue até a pasta do projeto e prossiga com uma das opções abaixo.

---
### Ambiente virtual

```bash
# Ambiente virtual
    $ python3 -m venv venv   # Windows:  python -m venv venv
    $ source venv/bin/activate  # Windows: .\venv\Scripts\activate

# Dependências Python
    $ pip install --upgrade pip
    $ pip install -r requirements.txt

# Banco de dados & migrations
    $ python manage.py makemigrations /$ python manage.py migrate

# Run!
    $ python manage.py runserver
```

---
### Instalar e configurar Docker

```bash
# Instalação e configuração Docker
    $ sudo apt-get update
    $ sudo apt-get install ca-certificates curl
    $ sudo install -m 0755 -d /etc/apt/keyrings
    $ sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc

# Adicionar repositorios do Docker
    $ echo   "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu   $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" |   sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    $ sudo apt-get update

# Instalar Docker e plugins necessários
    $ sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Iniciar serviço
    $ sudo systemctl start docker
```
A aplicação estará disponível em `http://localhost:8080/`.
```
http://localhost:8080/
````


---
## Container PostgreSQL com PgAdmin
```
# Criar Rede e volumes 
    $ docker network create pg_net
    $ docker volume create pg_data
    $ docker volume create pgadmin_data

# Container PostgreSQL
    $ docker run -d --name postgres --network pg_net -e POSTGRES_USER=admin -e POSTGRES_PASSWORD=admin -e POSTGRES_DB=estoque_db -v pg_data:/var/lib/postgresql/data -p 5432:5432 postgres:17

# Container PgAdmin
    $ docker run -d --name pgadmin --network pg_net -e PGADMIN_DEFAULT_EMAIL=admin@admin.com -e PGADMIN_DEFAULT_PASSWORD=admin -v pgadmin_data:/var/lib/pgadmin -p 5050:80 dpage/pgadmin4
```

