"""
Este módulo define exceções personalizadas para gerenciamento de erros
específicos relacionados à configuração. As exceções são agrupadas em classes
hierárquicas que permitem capturar e tratar diferentes tipos de erros.
"""

import re
import shutil
from typing import Any, Iterable, Optional, Literal


class ConfigError(Exception):
    """
    Exceção base para todas as exceções relacionadas à configuração.

    Esta é a classe base para todas as exceções que ocorrem no contexto de
    configurações dentro do sistema. Qualquer erro relacionado ao processamento,
    leitura, ou formatação de configurações pode ser derivado dessa classe.
    """

    pass


class ConfigFileError(ConfigError, OSError):
    """
    Exceção base para erros de sistema operacional relacionados a arquivos e
    diretórios de configuração.

    Essa exceção é levantada quando ocorre um erro ao tentar acessar, criar, ou
    manipular arquivos e diretórios de configuração, como falhas ao tentar
    abrir um arquivo de configuração ou acessar diretórios de configuração.
    """

    pass


class ConfigSameFileError(ConfigFileError, shutil.SameFileError):
    """
    Ocorre quando o caminho de destino de uma operação de cópia é o mesmo que o
    de origem.

    Essa exceção é levantada ao tentar copiar um arquivo para si mesmo, ou seja,
    quando o arquivo de destino e o de origem são o mesmo.
    """

    pass


class ConfigIsADirectoryError(ConfigFileError, IsADirectoryError):
    """
    Ocorre quando o caminho de destino é um diretório, mas era esperado um
    arquivo.

    Essa exceção é levantada quando uma operação de arquivo é realizada em um
    diretório quando um arquivo era esperado como destino.
    """

    pass


class ConfigFilePermissionError(ConfigFileError, PermissionError):
    """
    Ocorre quando não há permissões suficientes para a operação em um arquivo
    de configuração.

    Essa exceção é levantada quando uma tentativa de ler, escrever ou
    modificar um arquivo de configuração é impedida devido a permissões
    insuficientes.
    """

    pass


class ConfigFileNotFoundError(ConfigFileError, FileNotFoundError):
    """
    Ocorre quando o arquivo de configuração não é encontrado.

    Essa exceção é levantada quando um arquivo de configuração ou diretório
    necessário não pode ser encontrado no caminho especificado.
    """

    pass


class InvalidConfigError(ConfigError):
    """
    Exceção base para todas as exceções de valor e tipo de configuração
    inválidos.

    Essa classe base é usada para erros relacionados a valores ou tipos de
    dados inválidos dentro da configuração, como quando um valor não
    corresponde ao esperado.
    """

    pass


class InvalidConfigTypeError(InvalidConfigError, TypeError):
    """
    Ocorre quando o tipo de um valor de configuração não é válido.

    Essa exceção é levantada quando um valor fornecido para uma configuração
    não corresponde ao tipo esperado. A mensagem de erro pode incluir a seção e
    opção da configuração, o tipo atual e o tipo esperado.

    Args:
        value_or_msg (Any): O valor fornecido ou uma mensagem de erro.
        section (Optional[str]): A seção onde o erro ocorreu.
        option (Optional[str]): A opção da configuração com erro.
        types (Optional[set[type]]): Os tipos esperados para o valor da
            configuração.
        extra (str): Mensagem extra adicional.
    """

    def __init__(
        self,
        value_or_msg: Any,
        section: Optional[str] = None,
        option: Optional[str] = None,
        types: Optional[set[type]] = None,
        extra: str = "",
        *args,
    ):
        if section is None or option is None or types is None:
            message = (
                "tipo do valor"
                f" inválido{f': {value_or_msg}' if value_or_msg else ''}{f' {extra}' if extra else ''}."
            )
        else:
            expected_types = ",".join(map(lambda t: t.__name__, types))
            message = (
                "tipo do valor inválido para"
                f" {f'{extra} na ' if extra else 'a '}opção {option!r} da"
                f" seção {section!r}. Foi obtido"
                f" {type(value_or_msg).__name__!r}, mas era esperado"
                f" {expected_types!r}."
            )
        super().__init__(message, *args)


class InvalidConfigValueError(InvalidConfigError, ValueError):
    """
    Ocorre quando o valor de uma configuração não é válido.

    Essa exceção é levantada quando um valor fornecido para uma configuração
    não é adequado, podendo ser incorreto ou fora do esperado.
    """

    pass


class ConfigOutOfRangeError(InvalidConfigValueError):
    """
    Ocorre quando um valor de configuração está fora do intervalo esperado.

    Essa exceção é levantada quando o valor de uma configuração está além dos
    limites definidos, como valores que ultrapassam os limites mínimo ou máximo
    permitidos.

    Args:
        value_or_msg (Any): O valor fornecido ou uma mensagem de erro.
        section (Optional[str]): A seção onde o erro ocorreu.
        option (Optional[str]): A opção da configuração com erro.
        limit_name (Optional[Literal["min", "max"]]): O limite (mínimo ou
            máximo) que foi violado.
        range_limit (Optional[int]): O limite de intervalo para a configuração.
    """

    def __init__(
        self,
        value_or_msg: Any,
        section: Optional[str] = None,
        option: Optional[str] = None,
        limit_name: Optional[Literal["min", "max"]] = None,
        range_limit: Optional[int] = None,
        *args,
    ):
        if (
            section is None
            or option is None
            or limit_name is None
            or range_limit is None
        ):
            message = (
                "valor fora do intervalo"
                f" esperado{f': {value_or_msg if value_or_msg else ''}'}."
            )
        else:
            message = (
                f"valor fora do intervalo esperado na opção {option!r} da"
                f" seção {section!r}: o valor {limit_name} é {range_limit!r},"
                f" mas foi definido {value_or_msg!r}."
            )
        super().__init__(message, *args)


class InvalidConfigFormatError(InvalidConfigError, ValueError):
    """
    Ocorre quando o valor de configuração não tem um formato válido.

    Essa exceção é levantada quando um valor fornecido para uma configuração
    não segue o formato esperado, como no caso de padrões de expressão regular
    que não correspondem.

    Args:
        value_or_msg (Any): O valor fornecido ou uma mensagem de erro.
        section (Optional[str]): A seção onde o erro ocorreu.
        option (Optional[str]): A opção da configuração com erro.
        patterns (Optional[Iterable[re.Pattern]]): A lista de padrões de
            expressão regular esperados.
        extra (str): Mensagem extra adicional.
    """

    def __init__(
        self,
        value_or_msg: Any,
        section: Optional[str] = None,
        option: Optional[str] = None,
        patterns: Optional[Iterable[re.Pattern]] = None,
        extra: str = "",
        *args,
    ):
        if section is None or option is None or patterns is None:
            message = (
                "formato"
                f" inválido{f': {value_or_msg if value_or_msg else ''}'}"
                f"{f' {extra}' if extra else ''}."
            )
        else:
            message = (
                f"valor com formato inválido {f'{extra} ' if extra else ''}na"
                f" opção {option!r} da seção {section!r}: era esperado o"
                f" formato '{','.join([str(p.pattern) for p in patterns])!r}',"
                f" mas foi obtido o valor {value_or_msg!r}."
            )
        super().__init__(message, *args)
