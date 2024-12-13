Começando
=========

Este exemplo demonstra como usar o *ConfigCraft* do módulo *configcraft* para 
gerenciar configurações. O código abaixo mostra como adicionar uma 
*ConfigBlueprint* de configuração, que define uma seção, uma opção e o tipo de 
dado esperado, além de permitir valores padrão e descrições.

1. Instanciando o ConfigCraft
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Para instanciar o gerenciador de configurações, é necessário atribuir um nome à 
instância do *ConfigCraft*, uma vez que ele é implementado como um 
*PolySingleton*. Isso garante que, para cada nome fornecido, apenas uma 
instância do gerenciador será criada.

.. code-block:: python
    
    import configcraft

    # Cria uma instância chamada "app"
    cfg = configcraft.ConfigCraft("app")

2. Adicionando ConfigBlueprints
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Depois de instanciar o *ConfigCraft*, o próximo passo é adicionar um 
*ConfigBlueprint* à ele. Um *ConfigBlueprint* define as opções de configuração 
que serão usadas no gerenciador, incluindo a seção, a opção específica dentro 
dessa seção, os tipos de dados esperados, uma descrição da opção e um valor 
padrão, entre outros parâmetros.

No exemplo abaixo, mostramos como adicionar um *ConfigBlueprint* ao 
*ConfigCraft*, onde:

- **section**: Define o nome da seção onde a opção será armazenada.
- **option**: Define o nome da opção dentro da seção.
- **types**: Especifica os tipos de dados aceitos para a opção, podendo incluir tipos como `str` e `type(None)` (que torna a opção opcional).
- **description**: Fornece uma descrição explicativa sobre a opção de configuração.
- **default**: Define o valor padrão para a opção de configuração.

.. code-block:: python

    # Adiciona o blueprint ao gerenciador de configurações
    cfg.add_blueprint(
        configcraft.ConfigBlueprint(
            section="nome_seção",
            option="nome_opção",
            types={str, type(None)},  # type(None) torna a opção opcional
            description="Opção de exemplo 1.",
            default="Valor de Exemplo"
        )
    )


3. Inicializando o gerenciador
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Após adicionar todos os *ConfigBlueprints* necessários, é importante completar 
a inicialização da instância do gerenciador de configurações com o método 
*ìnitialize* para poder utilizar e gerenciar configurações. 

Durante esse processo, o gerenciador carrega as configurações a partir do 
arquivo de configuração - ou gera o arquivo a partir dos ConfigBlueprints com 
os valores padrão definidos, caso o arquivo ainda não exista. 

.. code-block:: python

    cfg.initialize("dev", "config", encoding="utf_8")

.. note::
    O ConfigCraft irá procurar pelo arquivo "dev.ini" dentro do diretório 
    "./config".

    - **Caso seja encontrado:** as configurações são carregadas com a codificação "utf_8" e validados através dos blueprints.
    - **Caso não seja encontrado:** o arquivo será gerado a partir da especificação dos ConfigBlueprints definidos anteriormente.

4. Manipulando valores das opções
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Depois de inicializar o gerenciador, você pode acessar ou alterar os valores 
das opções configuradas. As opções podem ser manipuladas como se fossem chaves 
de um dicionário através de uma tupla, sendo o primeiro valor o nome da seção e
o segundo o nome da opção.

.. code-block:: python

    # Acessa o valor da opção e imprime na tela
    print(cfg["nome_seção", "nome_opção"]) 
    # Saída: 'Valor de Exemplo'

    # Altera o valor da opção
    cfg["nome_seção", "nome_opção"] = "Novo Valor"

    # Acessa o valor da opção e imprime na tela
    print(cfg["nome_seção", "nome_opção"]) 
    # Saída: 'Novo Valor'

5. Arquivo de configuração 
~~~~~~~~~~~~~~~~~~~~~~~~~~

O arquivo de saída é gerado no caminho definido no método *initialize* através
do nome do perfil "dev" - não é necessário incluir a extensão .ini - e o 
diretório de destino "./config".

.. code-block:: ini
    
    # ConfigCraft - Version: 0.0.1

    # COMO PREENCHER OS VALORES:
    # 
    # 1. Texto: 
    #    - Representado por uma sequência de caracteres entre aspas duplas.
    #    - Exemplo: "Exemplo de texto".
    #    
    # 2. Inteiro: 
    #    - Um número inteiro (sem parte decimal).
    #    - Exemplo: 123, -456.
    #    
    # 3. Decimal: 
    #    - Um número que inclui uma parte decimal, sendo a separação feita com ponto (não vírgula).
    #    - Exemplo: 3.14, -0.5.
    #    
    # 4. Booleano: 
    #    - Valor lógico que pode ser true (verdadeiro) ou false (falso).
    #    - Atenção: Os valores são case-sensitive (sensíveis a maiúsculas e minúsculas), ou seja, True e False não são 
    #    válidos.
    #    - Exemplo: true, false.
    #    
    # 5. Lista: 
    #    - Uma coleção de valores entre colchetes, com os itens separados por vírgula.
    #    - Os valores podem ser de qualquer tipo, incluindo texto, inteiros, ou outros tipos.
    #    - Exemplo: [1, 2, 3], ["maçã", "banana", "morango"].
    #    
    # 6. Dicionário: 
    #    - Uma coleção de pares chave-valor, onde cada chave é associada a um valor. Os valores são separados por vírgula e as 
    #    chaves e valores são separados por dois pontos :.
    #    - Exemplo: {"chave1": "valor1", "chave2": 42}.
    #    
    # 7. Nulo: 
    #    - Valor vazio. Para indicar ausência de valor, deixe a configuração sem nenhum valor depois do sinal = ou use a 
    #    palavra-chave null.
    #    - Exemplo: parametro = ou parametro = null.

    [nome_seção]
    # Configuração de teste.
    # Tipo: Texto
    nome_opção = [
        "Novo Valor"
    ]

.. note::

    O texto padrão de documentação padrão após o cabeçalho do arquivo de 
    configuração pode ser alterado através do método *set_description* no 
    ConfigCraft.

    .. code-block:: python

        cfg.set_description("Nova descrição")
