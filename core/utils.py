from django.contrib.auth.models import AnonymousUser

from core.models import LogSystem


def report_log(user, action: str, status: str, message: str):
    """
    Registra uma entrada de log no sistema.

    Esta função é responsável por criar registros no modelo LogSystem,
    armazenando informações sobre ações executadas pelos usuários ou pelo
    próprio sistema. Também trata internamente casos onde o usuário é
    anônimo ou não informado, garantindo consistência dos dados e evitando
    falhas durante a gravação dos logs.

    Parâmetros
    ----------
    user : User | AnonymousUser | None
        Objeto representando o usuário que realizou a ação.
        Pode ser:
        - Um usuário autenticado (User)
        - Um usuário não autenticado (AnonymousUser)
        - None, indicando ação do sistema ou evento sem vínculo a usuário

        Caso o valor seja AnonymousUser ou None, o registro será criado
        sem vinculação a um usuário, para evitar inconsistências no banco.

    action : str
        Descrição curta e objetiva da ação realizada.
        Exemplos:
        - "Login"
        - "Logout"
        - "Acessar Página"
        - "Erro Interno"
        - "Reset de Senha"

    status : str
        Indica o status do evento registrado.
        Geralmente utilizado com valores como:
        - "SUCCESS"
        - "ERROR"
        - "WARNING"
        - "INFO"

        Permite categorizar o tipo de log e facilitar auditorias.

    message : str
        Mensagem descritiva contendo detalhes adicionais sobre a ação.
        Pode incluir exceções, explicações, informações complementares
        ou qualquer dado útil para auditoria e diagnóstico.

    Comportamento
    -------------
    - Caso o usuário seja AnonymousUser ou None, o log será salvo com
        o campo user definido como None.
    - Garante que a função nunca quebre por causa de inconsistências
        no parâmetro `user`.
    - Cria no banco um registro contendo:
        - Usuário (ou None)
        - Ação
        - Status
        - Mensagem
        - Timestamp automático

    Retorno
    -------
    None
        A função não retorna nada. O efeito colateral é a criação do
        registro no banco de dados através do modelo LogSystem.
    """

    # Garante que user seja gravado corretamente
    if not user or isinstance(user, AnonymousUser):
        user = None

    LogSystem.objects.create(
        user=user,
        action=action,
        status=status,
        message=message
    )