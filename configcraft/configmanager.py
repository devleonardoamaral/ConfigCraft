import os
import re
import json
import shutil
import asyncio
import threading
from pathlib import Path
from typing import Optional, Union, Any, Final
from collections.abc import MutableMapping
from tempfile import NamedTemporaryFile

from .configblueprint import ConfigBlueprint
from . import VERSION
from . import configerrors
from . import configutils
from . import configformatters

_FILEDOC: Final[str] = """COMO PREENCHER OS VALORES:

1. Texto: 
   - Representado por uma sequência de caracteres entre aspas duplas.
   - Exemplo: "Exemplo de texto".
   
2. Inteiro: 
   - Um número inteiro (sem parte decimal).
   - Exemplo: 123, -456.
   
3. Decimal: 
   - Um número que inclui uma parte decimal, sendo a separação feita com ponto (não vírgula).
   - Exemplo: 3.14, -0.5.
   
4. Booleano: 
   - Valor lógico que pode ser true (verdadeiro) ou false (falso).
   - Atenção: Os valores são case-sensitive (sensíveis a maiúsculas e minúsculas), ou seja, True e False não são 
   válidos.
   - Exemplo: true, false.
   
5. Lista: 
   - Uma coleção de valores entre colchetes, com os itens separados por vírgula.
   - Os valores podem ser de qualquer tipo, incluindo texto, inteiros, ou outros tipos.
   - Exemplo: [1, 2, 3], ["maçã", "banana", "morango"].
   
6. Dicionário: 
   - Uma coleção de pares chave-valor, onde cada chave é associada a um valor. Os valores são separados por vírgula e as 
   chaves e valores são separados por dois pontos :.
   - Exemplo: {"chave1": "valor1", "chave2": 42}.
   
7. Nulo: 
   - Valor vazio. Para indicar ausência de valor, deixe a configuração sem nenhum valor depois do sinal = ou use a 
   palavra-chave null.
   - Exemplo: parametro = ou parametro = null."""
"""
Armazena o texto padrão de como utilizar e preencher o arquivo de configuração.
"""


class ConfigManager(MutableMapping):
    _instances = {}

    def __new__(cls, name: str, *args, **kwargs):
        configutils.validate_type(name, str, "name")

        if name not in cls._instances:
            cls._instances[name] = super().__new__(cls)
            cls._instances[name]._initialized = False

        return cls._instances[name]

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._threading_lock: threading.Lock = threading.Lock()
        self._asyncio_lock: asyncio.Lock = asyncio.Lock()
        self._data: dict[str, dict[Any]] = {}
        self._blueprints: dict[str, dict[str, ConfigBlueprint]] = {}
        self._header = f"ConfigCraft - Version: {VERSION}"
        self._description = _FILEDOC
        self._encoding = "utf_8"
        self._path: Optional[Path] = None

    def __getitem__(self, key: tuple[str, str]):
        configutils.validate_type(key, tuple, "key")
        section, option = key
        try:
            return self._data[section][option]
        except KeyError:
            raise KeyError(
                f"a opção {option!r} da seção {section!r} não existe."
            )

    def __setitem__(self, key: tuple[str, str], value: Any):
        configutils.validate_type(key, tuple, "key")
        section, option = key

        if (
            section not in self._blueprints
            or option not in self._blueprints[section]
        ):
            raise KeyError(
                f"a opção {option!r} da seção {section!r} não existe."
            )

        blueprint = self._blueprints[section][option]
        backup = self._data[section][option]

        try:
            self._data[section][option] = blueprint.validate_value(value)
        except configerrors.InvalidConfigError:
            raise

        try:
            self.save_config()
        except configerrors.ConfigFileError as e:
            self._data[section][option] = backup
            raise configerrors.ConfigFileError(
                "erro ao atualizar valor armazenado no arquivo de"
                f" configuração da opção {option!r} da seção {section!r}."
                f" Erro: {e}"
            )

    def __delitem__(self, key: tuple[str, str]) -> None:
        raise NotImplementedError("excluir itens não é permitido nesta classe")

    def __iter__(self):
        """Retorna um iterador para percorrer as chaves de configuração, onde cada chave é uma tupla contendo o nome da
        seção e o nome da opção correspondente.

        O iterador percorre todas as seções e suas respectivas opções, gerando tuplas no formato (seção, opção).

        Yields:
            tuple[str, str]: Tupla contendo o nome da seção e o nome da opção.

        Returns:
            Generator[tuple[str, str], None, None]: Gerador que itera sobre as tuplas de chaves de configuração.
        """
        for section, options in self._data.items():
            for option in options:
                yield section, option

    def __len__(self):
        """Retorna o número total de opções de configuração em todas as seções. Este método conta quantas opções estão
        disponíveis em cada seção e retorna a soma total delas.

        Returns:
            int: O número total de opções em todas as seções de configuração.
        """
        return sum(len(options) for _, options in self._data.items())

    @property
    def path(self):
        """Propriedade para acessar o caminho do arquivo de configuração do perfil inicializado atualmente. Não deve ser
        chamado enquanto a instância não for inicializada com o método `initialize()`.

        Returns:
            Path: O caminho do arquivo de configuração.
        Raises:
            RuntimeError: Ocorre quando a instância não é inicializada corretamente.
        """
        if self._path is None:
            error_message = (
                "Erro ao obter caminho do perfil de configuração: instância"
                " não foi completamente inicializada"
            )
            raise RuntimeError(error_message)
        return self._path

    @property
    def directory(self):
        """Propriedade para acessar o caminho do diretório onde os perfis de configuração são armazenados. Não deve ser
        chamado enquanto a instância não for inicializada com o método `initialize()`.

        Returns:
            Path: O caminho do diretório de perfis de configuração.
        Raises:
            RuntimeError: Ocorre quando a instância não é inicializada corretamente.
        """
        return self.path.parent

    @property
    def profile(self):
        """Propriedade para acessar o nome do perfil inicializado. Não deve ser chamado enquanto a instância não for
        inicializada com o método `initialize()`.

        Returns:
            str: O nome do perfil atual.
        Raises:
            RuntimeError: Ocorre quando a instância não é inicializada corretamente.
        """
        return self.path.stem

    @property
    def encoding(self):
        """Propriedade para acessar o tipo de codificação que será utilizada em operações de leitura e escrita do
        arquivo de configuração.

        Returns:
            str: O nome do tipo de codificação.
        """
        return self._encoding

    @property
    def header(self):
        """Propriedade para acessar o cabeçalho que é escrito na primeira linha nos arquivos de configuração.

        Returns:
            str: O texto do cabeçalho.
        """
        return self._header

    @property
    def description(self):
        """Propriedade para acessar o texto que é escrito logo abaixo do cabeçalho nos arquivos de configuração. Por
        padrão é definido um texto explicativo de como preencher cada tipo de valor e como utilizar o arquivo de
        configuração de forma simples e intuitiva.

        Returns:
            str: O texto da descrição.
        """
        return self._description

    def set_description(self, value: str):
        """Setter para alterar o texto que é escrito logo abaixo do cabeçalho nos arquivos de configuração.

        Args:
            value (str): O novo texto de descrição.
        """
        configutils.validate_type(value, str, "description")
        self._description = value

    def _validate_directory(
        self, path: Union[str, Path], try_to_fix: bool = False
    ):
        """Valida se o diretório existe, e opcionalmente tenta criá-lo se não existir. Esta função não deve ser
        utilizada para verificar arquivos, apenas diretórios.

        Args:
            path (Union[str, Path]): Caminho para o diretório a ser validado.
            try_to_fix (bool): Indica se a função deve tentar criar o diretório em caso de inexistência.
            logger (logging.Logger): Logger opcional para registrar mensagens. Se não fornecido, usa o logger padrão.

        Raises:
            FileNotFoundError: Se o diretório não existir e `try_to_fix` for False.
            PermissionError: Se não for possível criar o diretório devido a permissões.
            OSError: Para outros erros ao criar o diretório.
        """
        path = Path(path)
        path_str = str(path)

        if path.exists():
            return

        if not try_to_fix:
            raise FileNotFoundError(f"diretório {path_str!r} não encontrado.")

        try:
            path.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            raise PermissionError(
                "permissões insuficientes para criar o diretório"
                f" {path_str!r}."
            )
        except OSError as e:
            raise OSError(
                "erro relacionado ao sistema operacional ao criar o diretório"
                f" {path_str!r}. Erro: {e}"
            )

    def initialize(
        self, profile: str, path: Union[Path, str], encoding: str = "utf_8"
    ):
        """Inicializa o gerenciador de configurações.

        Args:
            profile (str): O nome do perfil que será utilizado pelo gerenciador de configurações.
            path (Union[Path, str]): O diretório onde os perfis de configuração serão armazenados.
            encoding (str): Codificação a ser utilizada nas operações de leitura e escrita do arquivo de configuração.

        Raises:
            RuntimeError: Se não houver nenhum blueprint definido ou se o diretório de configuração não existir e não
                puder ser criado.
            ConfigFileError: Se houver falha ao carregar ou processar dados de configuração.
        """
        configutils.validate_type(profile, str, "profile")
        configutils.validate_type(path, (Path, str), "path")
        configutils.validate_type(encoding, str, "encoding")

        if isinstance(path, str):
            path = Path(os.path.normpath(path))

        if not self._blueprints:
            raise RuntimeError(
                "é necessário definir pelo menos um blueprint antes de"
                " inicializar."
            )

        self._path = path / f"{profile}.ini"
        self._encoding = encoding

        try:
            self._validate_directory(path, try_to_fix=True)
        except Exception as e:
            raise RuntimeError(
                f"não foi possível criar o diretório de configuração: {e}"
            )

        try:
            self.load_config()
        except (configerrors.ConfigFileError, configerrors.InvalidConfigError):
            raise
        except Exception as e:
            raise configerrors.ConfigFileError(
                "ocorreu um erro inesperado ao carregar o arquivo de"
                f" configurações. Erro: {e}"
            )

    def save_config(self):
        """
        Salva os dados de configuração de maneira segura, garantindo
        compatibilidade com ambientes multithread.

        Este método utiliza um bloqueio (`threading.Lock`) para assegurar que
        apenas uma thread possa executar a operação de salvamento por vez,
        evitando condições de corrida que possam corromper o arquivo de
        configuração.

        A lógica de salvamento delega a operação de escrita ao método
        interno `_write_config`, que realiza a escrita atômica no arquivo de
        configuração. Isso é feito utilizando um arquivo temporário, garantindo
        maior segurança e evitando perda de dados em caso de falhas inesperadas.

        Raises:
            configerrors.ConfigSameFileError:
                Levantada se o arquivo temporário e o arquivo de destino forem
                o mesmo, o que indicaria uma falha na lógica de manipulação de
                arquivos temporários.

            configerrors.ConfigIsADirectoryError:
                Levantada se o caminho especificado para o arquivo de
                configuração for um diretório ao invés de um arquivo,
                impossibilitando a escrita.

            configerrors.ConfigFileNotFoundError:
                Levantada quando o caminho especificado para o arquivo de
                configuração não é encontrado, indicando que o caminho de
                destino ainda não existe.

            configerrors.ConfigFilePermissionError:
                Levantada quando a aplicação não possui permissões suficientes
                para escrever no arquivo ou substituir o arquivo de
                configuração existente.

            configerrors.ConfigFileError:
                Levantada para qualquer outro erro inesperado ocorrido durante
                a escrita no arquivo, permitindo uma abordagem genérica para
                tratamento de erros fora dos cenários comuns. As execeções
                específicias citadas acima herdam de *ConfigFileError*.
        """
        with self._threading_lock:
            self._write_config()

    def load_config(self):
        """Lê o arquivo utilizando o Lock de threading para evitar que o arquivo seja sobrescrito durante a leitura."""
        with self._threading_lock:
            self._load_config()

    def add_blueprint(self, blueprint: ConfigBlueprint) -> None:
        """Adiciona um novo blueprint à instância do gerenciador de configurações.

        Args:
            blueprint (ConfigBlueprint): O blueprint a ser adicionado.

        Raises:
            RuntimeError: Ocorre quando a instância já foi inicializada. É importante adicionar todos os blueprints
                antes da inicialização completa da instância.
        """
        configutils.validate_type(blueprint, ConfigBlueprint, "blueprint")

        if self._path is not None:
            raise RuntimeError(
                f"não é possível adicionar novos blueprints após o gerenciador"
                f" de configuração ser inicializado."
            )

        if not self.has_blueprint_section(blueprint.section):
            self._blueprints[blueprint.section] = {}
        self._blueprints[blueprint.section][blueprint.option] = blueprint

    def has_blueprint_section(self, section: str) -> bool:
        """Verifica se a seção fornecida está presente na estrutura interna de blueprints, retornando `True` se a seção
        for encontrada, e `False` caso contrário.

        Args:
            section (str): O nome da seção a ser verificada nos blueprints.

        Returns:
            bool: Retorna `True` se a seção está definida, caso contrário, `False`.
        """
        return section in self._blueprints

    def get_blueprint_options(self, section: str):
        """Retorna todas as opções associadas a uma seção específica nos blueprints, ou `None` se a seção não estiver
        definida.

        Args:
            section (str): O nome da seção cujas opções são solicitadas.

        Returns:
            Optional[dict]: Um dicionário contendo as opções da seção se a seção existir, ou `None` se a seção não
                estiver definida.
        """
        return self._blueprints.get(section)

    def has_blueprint_option(self, section: str, option: str):
        """Verifica se uma opção específica está definida dentro de uma seção nos blueprints. Retorna `True` se a opção
        for encontrada na seção, `False` se a seção existir mas a opção não, e `None` se a seção não existir.

        Args:
            section (str): O nome da seção onde a opção será verificada.
            option (str): O nome da opção a ser verificada dentro da seção.

        Returns:
            Optional[bool]: Retorna `True` se a opção existe na seção, `False` se a opção não existir, ou `None` se a
                seção não existir.
        """
        if options := self.get_blueprint_options(section):
            return option in options
        return None

    def get_blueprint(self, section: str, option: str):
        """Obtém um blueprint específico dentro de uma seção e opção. Se a seção e a opção existirem nos blueprints, o
        método retorna o blueprint associado à opção. Caso contrário, retorna `None`.

        Args:
            section (str): O nome da seção onde o blueprint está definido.
            option (str): O nome da opção dentro da seção cuja blueprint será retornada.

        Returns:
            Optional[ConfigBlueprint]: Retorna o blueprint associado à opção,
                ou `None` se a seção ou a opção não existirem.
        """
        options = self.get_blueprint_options(section)
        if options:
            return options.get(option)
        return None

    def _parse_data_to_file_lines(self):
        """Retorna uma lista de strings contendo cada linha do arquivo de configuração já formatada para escrita.

        Este método gera as linhas de um arquivo de configuração a partir dos dados e blueprints definidos na instância.
        Ele formata as seções, opções, descrições e valores de forma adequada para que o arquivo resultante esteja
        pronto para ser salvo. A formatação inclui a adição de cabeçalhos, descrições e comentários de documentação,
        bem como a linha de configuração para cada opção.

        Returns:
            List[str]: Lista de strings, onde cada string é uma linha do arquivo de configuração formatada para escrita.
        """
        lines = []

        if self.header:
            lines.extend(
                configformatters.format_multiline_comment(self.header)
            )
            lines.append("\n\n")

        if self.description:
            lines.extend(
                configformatters.format_multiline_comment(self.description)
            )
            lines.append("\n\n")

        for blueprint_section, options in self._blueprints.items():
            lines.append(f"\n[{blueprint_section}]\n")

            for blueprint_option, blueprint in options.items():
                value = self._data.get(blueprint_section, {}).get(
                    blueprint_option, blueprint.default
                )
                lines.append(blueprint._get_formatted_description())
                lines.append(blueprint._generate_config_line(value))

        return lines

    def _write_config(self):
        """Escreve os dados de configuração no arquivo especificado no caminho armazenado na instância.

        Este método gera um arquivo de configuração temporário contendo os dados formatados a partir dos blueprints e
        informações armazenadas na instância. O arquivo temporário é usado para garantir que o arquivo original não
        seja corrompido em caso de falhas durante a escrita. Após isso, o método substitui o arquivo de configuração
        existente pelo arquivo temporário de forma segura.

        Raises:
            configerrors.ConfigSameFileError: Caso o arquivo temporário e o arquivo de destino tenham o mesmo nome.
            configerrors.ConfigIsADirectoryError: Caso o caminho de destino seja um diretório.
            configerrors.ConfigFileNotFoundError: Caso o caminho de destino não seja encontrado.
            configerrors.ConfigFilePermissionError: Quando não há permissões suficientes para escrever no arquivo ou
                substituir o arquivo de configuração atual pelo arquivo temporário com as novas configurações.
            configerrors.ConfigFileError: Para outros erros não previstos durante a escrita do arquivo.
        """
        path_str = str(self.path)
        lines = self._parse_data_to_file_lines()

        try:
            with NamedTemporaryFile(
                mode="w",
                dir=self.path.parent,
                encoding=self.encoding,
                delete=False,
            ) as tempf:
                tempf.writelines(lines)
                tempf.flush()
                os.fsync(tempf.fileno())

                try:
                    shutil.copy(tempf.name, self.path)
                except shutil.SameFileError:
                    raise configerrors.ConfigSameFileError(
                        f"o caminho de destino {path_str!r} possuí o mesmo"
                        " nome do arquivo temporário.",
                    )
                except IsADirectoryError:
                    raise configerrors.ConfigIsADirectoryError(
                        f"o caminho de destino {path_str!r} é um diretório.",
                    )
                except FileNotFoundError:
                    raise configerrors.ConfigFileNotFoundError(
                        f"caminho de destino {path_str!r} não encontrado.",
                    )
                except PermissionError:
                    raise configerrors.ConfigFilePermissionError(
                        "permissões insuficientes para realizar a cópia do"
                        f" arquivo temporário {tempf.name!r} no destino"
                        f" {path_str!r}."
                    )
                except Exception as e:
                    raise configerrors.ConfigFileError(
                        "erro inesperado durante a manipulação do arquivo"
                        f" temporário {tempf.name!r}: {e}"
                    )
                finally:
                    Path(tempf.name).unlink(missing_ok=True)

        except configerrors.ConfigFileError:
            raise
        except FileNotFoundError:
            raise configerrors.ConfigFileNotFoundError(
                f"diretório de configuração {path_str!r} não encontrado.",
            )
        except PermissionError:
            raise configerrors.ConfigFilePermissionError(
                "permissões insuficientes para realizar a operação de escrita"
                f" no arquivo de configuração {path_str}."
            )
        except Exception as e:
            raise configerrors.ConfigFileError(
                "erro durante a operação de escrita no arquivo de"
                f" configuração {tempf.name!r}: {e}"
            )

    def _fetch_section_from_line(self, line: str):
        """Retorna o nome da seção caso a linha corresponda com uma seção formatada como linha de arquivo de
        configuração.

        Args:
            line (str): A string onde a seção será buscada.

        Returns:
            Optional[str]: Retorna o nome da seção, ou None caso não seja encontrado uma correspondência.
        """
        if match := re.match(r"^\[(.*)\]$", line):
            return match.group(1).strip()
        return None

    @staticmethod
    def _fetch_option_and_value_from_line(start_index: int, lines: list[str]):
        """Percorre as linhas da lista de linhas iniciando no ídice especificado e retorna uma tupla contendo o nome e o
        valor da opção caso seja encontrada uma correspondência. É retornado imediatamente a partir da primeira
        ocorrência ou se for encontrado um padrão de seção ou comentário, indicando que a procura chegou ao final do
        escopo onde a opção-valor deveriam estar definidos. É retornado uma tupla contendo dois itens com valor None
        caso não haja nenhuma correspondência.

        Args:
            index (int): o índice onde deve ser iniciada a procura na lista de linhas, linhas anteriores ao índice
                especificado serão ignoradas.
            lines (list[str]): linhas onde será procurado o nome da opção e o valor.

        Raises:
            configerrors.InvalidConfigError: Quando não é possível decodificar o dado definido no valor da opção.
        """
        value_parts = []
        option = None
        value = None

        first_line = lines[start_index].strip()
        parts_pattern = re.compile(r"^\[\w*\]$")

        n = len(lines)
        end_index = n

        if first_line.startswith(("#", ";")):
            return None, None

        if match := re.match(r"^(.*)=(.*)$", first_line):
            option = match.group(1).strip()
            value_parts.append(match.group(2).strip())

            for i in range(min(start_index + 1, n), n):
                current_line = lines[i].strip()
                if current_line.startswith(("#", ";")) or parts_pattern.match(
                    current_line
                ):
                    end_index = i
                    break

                value_parts.append(current_line)

        value_raw = "".join(value_parts)
        if value_raw:
            try:
                value = json.loads(value_raw)
            except json.JSONDecodeError:
                raise configerrors.InvalidConfigError(
                    f"não foi possível decodificar valor da opção {option!r},"
                    " encontrada entre as linhas"
                    f" {start_index + 1} a {end_index + 1}."
                )

        return option, value

    def _fix_missing_data(self):
        """Preenche valores de configuração ausentes com os valores padrão definidos nos blueprints.

        Este método verifica as seções e opções de configuração armazenadas e compara com os blueprints definidos.
        Caso encontre uma configuração ausente, a preenche com o valor padrão correspondente do blueprint.
        """
        for blueprint_section, options in self._blueprints.items():
            if blueprint_section not in self._data:
                self._data[blueprint_section] = {}

            for blueprint_option, blueprint in options.items():
                if blueprint_option not in self._data[blueprint_section]:
                    self._data[blueprint_section][
                        blueprint_option
                    ] = blueprint.default

    def _read_file_lines(self):
        """
        Lê todas as linhas de um arquivo de texto e retorna uma lista contendo as linhas lidas.

        Este método encapsula a lógica de leitura de um arquivo e inclui tratamento de exceções para lidar com
        problemas comuns como arquivo inexistente ou permissões insuficientes.

        Returns:
            list[str]: As linhas do arquivo como uma lista de strings. Se o arquivo não existir, retorna uma lista vazia.

        Raises:
            configerrors.ConfigFilePermissionError: Quando não há permissões suficientes para acessar o arquivo.
            configerrors.ConfigFileError: Para outros erros inesperados.
        """
        path_str = str(self.path)

        try:
            with open(self.path, "r", encoding=self.encoding) as f:
                lines = f.readlines()
                return lines
        except FileNotFoundError:
            return []
        except PermissionError:
            raise configerrors.ConfigFilePermissionError(
                "permissões insuficientes para ler arquivo de configuração"
                f" {path_str!r}."
            )
        except Exception as e:
            raise configerrors.ConfigFileError(
                "erro inesperado ao tentar ler o arquivo de configuração"
                f" {path_str!r}. Erro: {e}"
            )

    def _process_config_data(self, lines: list[str]):
        """Processa as linhas de configuração, interpretando seções, opções e valores.

        Este método valida as opções de acordo com os blueprints e aplica os valores padrões
        quando necessário. Ele também ignora seções e opções que não estão definidas nos blueprints.

        Em caso de falha, as configurações serão restauradas para o estado anterior.

        Args:
            lines (list[str]): Linhas do arquivo de configuração.

        Raises:
            configerrors.InvalidConfigError: Erro ao processar dados do arquivo de configuração.
        """
        path_str = str(self.path)
        backup = self._data.copy()
        self._data: dict[str, dict[str, Any]] = {}
        current_section = None

        try:
            for index, line in enumerate(lines):
                # Ignora linhas vazias e comentários
                line = line.strip()
                if not line or line.startswith(("#", ";")):
                    continue

                # Procura uma seção na linha
                if section := self._fetch_section_from_line(line):
                    if not self.has_blueprint_section(section):
                        continue
                    current_section = section
                    self._data[section] = {}
                    continue

                # Procura uma opção-valor na linha
                elif option_value := self._fetch_option_and_value_from_line(
                    index, lines
                ):
                    option, value = option_value

                    # Só é possível carregar opções quando há uma seção selecionada
                    if current_section is None:
                        continue

                    # Recupera o blueprint associado
                    if blueprint := self.get_blueprint(
                        current_section, option
                    ):
                        try:
                            # Valida se o valor é compatível com o blueprint
                            blueprint.validate_value(value)

                        except configerrors.InvalidConfigError:
                            raise

                        self._data[current_section][option] = value

            # Corrige configurações ausentes com valores padrão
            self._fix_missing_data()

        except Exception as e:
            self._data = backup
            raise configerrors.InvalidConfigError(
                "erro ao processar configurações do arquivo"
                f" {str(path_str)!r}: {e}"
            )

    def _load_config(self):
        """Carrega e processa as configurações armazenadas no arquivo de configuração, validando e corrigindo valores
        com base nos blueprints.

        Este método realiza as seguintes etapas:
        1. Lê o arquivo de configuração no caminho especificado na instância do gerenciador de configurações.
        2. Processa cada linha do arquivo, identificando seções e opções com valores associados.
        3. Valida os valores encontrados de acordo com as regras definidas nos blueprints.
        4. Preenche valores ausentes com os valores padrão definidos nos blueprints.
        5. Atualiza o arquivo de configuração com as mudanças realizadas (se houver).

        Em caso de falha no carregamento, processamento ou atualização do arquivo de configuração, o estado anterior das
        configurações é restaurado e uma exceção `ConfigError` é lançada. Durante o processo, mensagens de log detalhadas
        são registradas para fornecer visibilidade sobre o que foi feito e onde ocorreram falhas.

        Raises:
            configerrors.ConfigFileError: Se houver falha ao ler ou escrever no arquivo de configuração.
            configerrors.InvalidConfigError: Se houver falha ao processar ou atualizar o arquivo de configuração.
        """
        path_str = str(self.path)

        try:
            lines = self._read_file_lines()
        except configerrors.ConfigFileError:
            raise

        try:
            self._process_config_data(lines)
        except Exception as e:
            raise configerrors.InvalidConfigError(e)

        try:
            self._write_config()
        except Exception as e:
            raise configerrors.ConfigFileError(
                "erro ao atualizar o arquivo de configuração"
                f" {path_str!r}: {e}"
            )