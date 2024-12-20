# ConfigCraft

ConfigCraft é uma biblioteca Python para gerenciar arquivos de configuração de forma eficiente e intuitiva. Ela permite que você crie e gerencie diferentes perfis de configuração, além de facilitar a escrita e leitura dos arquivos com segurança e atomicidade. Ideal para projetos que exigem flexibilidade no gerenciamento de configurações.

## Funcionalidades

- **Perfis de Configuração**: Crie diferentes perfis de configuração e alterne entre eles facilmente apenas trocando o nome do perfil a ser carregado. Isso facilita a gestão de várias configurações em um único arquivo.
  
- **Documentação Automática**: A biblioteca gera automaticamente uma documentação sobre como preencher e utilizar cada opção de configuração. Isso ajuda o usuário final a compreender rapidamente como interagir com o arquivo de configuração.

- **Escrita e Leitura Seguras com Locking**: Utiliza threading Lock para garantir que as operações de leitura e escrita no arquivo de configuração sejam seguras e atômicas. Isso evita inconsistências nos dados durante operações concorrentes.

- **Configurações Salvas Automaticamente**: As configurações são salvas automaticamente no arquivo assim que são alteradas. Isso garante que as modificações sejam persistidas imediatamente sem a necessidade de chamar um método de "salvamento" manual.

- **Suporte a Diferentes Tipos de Dados**: Suporta vários tipos de dados, incluindo:
  - Strings
  - Números Inteiros
  - Números Decimais
  - Booleanos
  - Listas e dicionários

## Instalação
Você pode instalar a versão mais recente do ConfigCraft usando o pip:
```bash
pip install git+https://github.com/devleonardoamaral/ConfigCraft.git
```

Ou, se preferir, uma versão específica do ConfigCraft:
```bash
pip install git+https://github.com/devleonardoamaral/ConfigCraft.git@{branch-name}
```
```bash
pip install git+https://github.com/devleonardoamaral/ConfigCraft.git@{commit-hash}
```

## Documentação

[Clique aqui para acessar a documentação](https://devleonardoamaral.github.io/ConfigCraft/index.html)

## Licença

Este projeto está licenciado sob a Licença MIT. Se você tiver dúvidas ou quiser saber mais sobre os termos da licença, consulte o arquivo [LICENSE](./LICENSE).