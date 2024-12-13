"""
Esse módulo fornece a classe :class:`configcraft.configblueprint.ConfigBlueprint`.
Que é responsável por definir a estrutura de configuração.
"""

import re
import json
from typing import Union, Optional, Iterable, Final, Mapping, Any

from . import configerrors
from . import configutils
from . import configtypes
from . import configformatters


class ConfigBlueprint:
    """
    Classe responsável por definir a estrutura de cada opção de configuração e
    realizar validações sobre os valores fornecidos.

    Args:
        section (str): Nome da seção à qual a opção pertence.
        option (str): Nome da opção.
        types (Union[set[type], type]): Conjunto de tipos aceitos pela opção.
            Este conjunto será usado para validar os valores atribuídos.
        description (str): Descrição da opção, a ser incluída na documentação
            do arquivo de configuração. Deve ser uma breve explicação do
            propósito da opção.
        default (Any): Valor padrão da opção. Deve ser compatível com os tipos
            especificados em `types` e, se aplicável, em `item_types`.
        item_types (Optional[Union[set[type], type]]): Conjunto de tipos aceitos
            para os itens internos de coleções como listas ou dicionários,
            caso aplicável.
        min_value (Optional[Union[int, float]]): Valor mínimo permitido para a
            opção, se for um número.
        max_value (Optional[Union[int, float]]): Valor máximo permitido para a
            opção, se for um número.
        pattern (Optional[dict[str, Union[re.Pattern, str]]]): Dicionário de
            padrões regex usados para validar valores do tipo string.
            As chaves devem descrever o padrão de forma humanizada, servindo
            como exemplos na documentação do arquivo de configuração.

    Raises:
        configerrors.InvalidConfigTypeError: Se o valor definido em `default`
            não for compatível com os tipos especificados em `types` ou
            `item_types`.
        configerrors.InvalidConfigFormatError: Se o valor definido em `default`
            não atender a nenhum dos padrões regex especificados em `pattern`.
        configerrors.ConfigOutOfRangeError: Se o valor definido em `default`
            estiver fora dos limites especificados por `min_value` e/ou
            `max_value`.
    """

    _SUPPORTED_PRIMITIVE_TYPES: Final[set[type]] = {
        str,
        int,
        float,
        bool,
        type(None),
    }
    """Armazena os tipos primitivos suportados pela configuração."""

    def __init__(
        self,
        section: str,
        option: str,
        types: Union[set[type], type],
        description: str = "",
        default: Any = None,
        *,
        items_types: Optional[Union[set[type], type]] = None,
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        pattern: dict[str, Union[re.Pattern, str]] = None,
    ):
        configutils.validate_type(section, str, "section")
        configutils.validate_type(option, str, "option")
        configutils.validate_type(description, str, "description")
        configutils.validate_type(types, (set, type), "types")

        if isinstance(types, type):
            types = {types}

        for t in types:
            configutils.validate_type(t, type, "tipo em types")

        configutils.validate_type(
            items_types, (set, type(None), type), "items_types"
        )

        if isinstance(items_types, type):
            items_types = {items_types}
        elif items_types is not None:
            for t in items_types:
                configutils.validate_type(
                    t, type, "um dos valores de items_types"
                )
        else:
            items_types = self._SUPPORTED_PRIMITIVE_TYPES

        try:
            configutils.validate_type(default, tuple(types), "default")
        except TypeError:
            raise configerrors.InvalidConfigTypeError(
                default, self.section, self.option, self.types
            )

        configutils.validate_type(pattern, (dict, type(None)), "pattern")
        pattern = pattern or {}

        for k, p in pattern.items():
            configutils.validate_type(k, str, "chave em pattern")
            configutils.validate_type(p, (re.Pattern, str), "item em pattern")

            if isinstance(p, str):
                try:
                    pattern[k] = re.compile(p)
                except re.error as e:
                    raise ValueError(
                        "sequência regex inválida: falha ao compilar padrão"
                        f" para a chave {k!r} com o valor '{p!r}'. Erro:"
                        f" {str(e)}"
                    )

        configutils.validate_type(
            min_value, (type(None), int, float), "min_value"
        )

        configutils.validate_type(
            max_value, (type(None), int, float), "max_value"
        )

        self._section: str = section
        self._option: str = option
        self._description: str = description
        self._types: set[type] = types
        self._items_types: set[type] = items_types
        self._default: Any = default
        self._pattern: dict[str, re.Pattern] = pattern
        self._min_value: Optional[Union[int, float]] = min_value
        self._max_value: Optional[Union[int, float]] = max_value

        self.validate_value(self.default)

    @property
    def section(self):
        """Retorna o nome da seção.

        Returns:
            str: O nome da seção.
        """
        return self._section

    @property
    def option(self):
        """Retorna o nome da opção.

        Returns:
            str: Onome da opção.
        """
        return self._option

    @property
    def types(self):
        """Retorna um conjunto com todos os tipos aceitos pela opção.

        Returns:
            set[type]: O set contendo os tipos.
        """
        return self._types

    @property
    def items_types(self):
        """Retorna um conjunto com todos os sub tipos aceitos pela opção.

        Returns:
            set[type]: O set contendo os tipos.
        """
        return self._items_types

    @property
    def description(self):
        """Retorna o texto de descrição da opção.

        Returns:
            str: O texto de descrição da opção.
        """
        return self._description

    @property
    def required(self):
        """Verifica se a opção é obrigatória. Ou seja, se a opção pode receber
        valores nulos (null/None) ou ficar em branco no arquivo de configuração.

        Returns:
            bool: Retorna True se a opção for obrigatória, caso contrário
                retorna False.
        """
        return type(None) not in self.types

    @property
    def default(self):
        """Retorna o valor padrão da configuração.

        Returns:
            Any: O valor padrão.
        """
        return self._default

    @property
    def pattern(self):
        """Retorna o dicionário contendo os padrões de validação de strings,
        sendo a representação em string da documentação como chave e o
        re.Pattern como valor.

        Returns:
            dict[str, re.Pattern]: O dicionário de padrões.
        """
        return self._pattern

    @property
    def min_value(self):
        """Retorna o numérico mínimo aceito pela opção de configuração.

        Returns:
            Optional[Union[int, float]]: O valor mínimo.
        """
        return self._min_value

    @property
    def max_value(self):
        """Retorna o numérico máximo aceito pela opção de configuração.

        Returns:
            Optional[Union[int, float]]: O valor máximo.
        """
        return self._max_value

    def validate_value(self, value: Any):
        """Valida o valor de acordo com as regras definidas no blueprint.

        Args:
            value (Any): O valor a ser validado.

        Returns:
            Any: O próprio valor, sem alterações. O valor é retornado para
            facilitar a validação e atribuição em uma única operação.

        Raises:
            configerrors.InvalidConfigTypeError: Se o valor definido em
                `default` não for compatível com os tipos especificados em
                `types` ou `item_types`.
            configerrors.InvalidConfigFormatError: Se o valor definido em
                `default` não atender a nenhum dos padrões regex especificados
                em `pattern`.
            configerrors.ConfigOutOfRangeError: Se o valor definido em
                `default` estiver fora dos limites especificados por
                `min_value` e/ou `max_value`.
        """
        self._validate_value_type(value)
        self._validate_value_format(value)
        self._validate_value_rules(value)
        return value

    def _get_formatted_description(self):
        """Retorna o texto de documentação formatada como comentário para o arquivo de configuração.

        Returns:
        str: Texto formatado que pode ser usado como comentário no arquivo de configuração.

        Raises:
            configerrors.InvalidConfigError: Se o valor padrão não for serializável para o formato JSON.
        """

        lines = list(
            configformatters.format_multiline_comment(self.description)
        )

        lines.append(
            configformatters.format_comment_line(
                "Tipo:"
                f" {configtypes.generate_type_hint(self.types, self.items_types)}"
            )
        )

        try:
            lines.append(
                configformatters.format_comment_line(
                    f"Padrão: {json.dumps(self.default, ensure_ascii=False)}"
                )
            )
        except TypeError as e:
            raise configerrors.InvalidConfigError(
                "falha ao construir linha de comentário de configuração: o"
                f" valor {self.default!r} não é serializável para o formato"
                " JSON."
            )

        if self.min_value is not None:
            lines.append(
                configformatters.format_comment_line(
                    f"Mínimo: {self.min_value}"
                )
            )

        if self.max_value is not None:
            lines.append(
                configformatters.format_comment_line(
                    f"Máximo: {self.max_value}"
                )
            )

        if self.pattern:
            lines.append(
                configformatters.format_comment_line(
                    "Formatos:"
                    f" {', '.join(map(lambda k: f'{k}', self.pattern.keys()))}"
                )
            )

        return "".join(lines)

    def _generate_config_line(self, value: Any):
        """Gera e retorna a string que representa a linha de configuração de
        opção utilizando o valor fornecido como valor da opção.

        Args:
            value (Any): O valor a ser codificado e adicionado à opção na linha
                de configuração.

        Raises:
            configerrors.InvalidConfigError: Ocorre quando o processo de
                codificação do valor para JSON falha, indicando que o valor não
                é válido.

        Returns:
            str: Retorna a linha de configuração formatada para escrita no
                arquivo de configuração.
        """
        try:
            return (
                f"{self.option} ="
                f" {json.dumps(value, ensure_ascii=False, indent=4)}\n\n"
            )
        except TypeError:
            raise configerrors.InvalidConfigError(
                "falha ao construir linha do arquivo de configuração: o valor"
                f" {value!r} não é serializável para o formato JSON."
            )

    def _validate_mapping_value_type(self, value: Mapping):
        """Valida se o tipo do valor de cada item do Mapping é um tipo válido.

        Args:
            value (Mapping): O Mapping que terá seus valores validados.

        Raises:
            configerrors.InvalidConfigTypeError: Ocorre quando o tipo do valor não é um tipo válido.
        """
        primitive_types = configutils.get_indexable_iterables_intersection(
            self.items_types, self._SUPPORTED_PRIMITIVE_TYPES
        )

        for k, v in value.items():
            try:
                configutils.validate_type(k, str)
            except TypeError:
                raise configerrors.InvalidConfigTypeError(
                    value,
                    self.section,
                    self.option,
                    {str},
                    f"a chave {k!r} do dicionário",
                )

            try:
                configutils.validate_type(v, tuple(primitive_types))
            except TypeError:
                raise configerrors.InvalidConfigTypeError(
                    value,
                    self.section,
                    self.option,
                    self.items_types,
                    f"o valor da chave {k!r} do dicionário",
                )

    def _validate_indexable_value_type(self, value: Iterable):
        """Valida se o tipo do valor de cada item do iterável é um tipo válido.

        Args:
            value (Iterable[Any]): O Iterável que terá seus valores validados.

        Raises:
            configerrors.InvalidConfigTypeError: Ocorre quando o tipo do valor não é um tipo válido.
        """
        primitive_types = configutils.get_indexable_iterables_intersection(
            self.items_types, self._SUPPORTED_PRIMITIVE_TYPES
        )

        try:
            for i, v in enumerate(value):
                configutils.validate_type(v, tuple(primitive_types))
        except TypeError:
            raise configerrors.InvalidConfigTypeError(
                value,
                self.section,
                self.option,
                self.items_types,
                f"o índice {i!r} da coleção",
            )

    def _validate_value_type(self, value: Any):
        """Valida se o tipo do valor é um tipo válido.

        Args:
            value (Any): O valor a ser validado.

        Raises:
            configerrors.InvalidConfigTypeError: Ocorre quando o tipo do valor não é um tipo válido.
        """

        if self.types & {list, dict}:
            if isinstance(value, list):
                self._validate_indexable_value_type(value)
                return
            if isinstance(value, dict):
                self._validate_mapping_value_type(value)
                return

        try:
            configutils.validate_type(value, tuple(self.types))
        except TypeError:
            raise configerrors.InvalidConfigTypeError(
                value, self.section, self.option, self.types
            )

    def _validate_str_value_format(
        self,
        value: str,
        extra: Optional[str] = None,
    ):
        """Valida se a string corresponde a todos os formatos definidos em 'pattern'."""
        if self.pattern and not any(
            p.fullmatch(value) for p in self.pattern.values()
        ):
            raise configerrors.InvalidConfigFormatError(
                value, self.section, self.option, self.pattern.values(), extra
            )

    def _validate_indexable_value_format(self, value: Iterable[Any]):
        """Valida se todos os valores do tipo string de um iterável indexável correspondem a todos os padrões regex.

        Args:
            value (Iterable[Any]): O valor a ser validado.

        Raises:
            configerrors.ConfigValueFormatError: Ocorre quando um dos valores do iterável não atende aos padrões regex.
        """
        for i, v in enumerate(value):
            if isinstance(v, str):
                self._validate_str_value_format(
                    v, f"o índice {i!r} da coleção"
                )

    def _validate_mapping_value_format(self, value: Mapping[str, Any]):
        """Valida se todos os valores do tipo string de um mapping correspondem a todos os padrões regex.

        Args:
            value (Mapping[str, Any]): O valor a ser validado.

        Raises:
            configerrors.ConfigValueFormatError: Ocorre quando um dos valores do mapping não atende aos padrões regex.
        """
        for k, v in value.items():
            if isinstance(v, str):
                self._validate_str_value_format(
                    v, f"valor da chave {k!r} da coleção"
                )

    def _validate_value_format(self, value: Any):
        """Valida se o valor corresponde corretamente aos formatos definidos em 'pattern'.

        Args:
            value (Any): O valor a ser validado.

        Raises:
            configerrors.ConfigValueFormatError: Ocorre quando o valor é do tipo `str` e não atende aos padrões regex.
        """
        if isinstance(value, str):
            self._validate_str_value_format(value)
        elif isinstance(value, list):
            self._validate_indexable_value_format(value)
        elif isinstance(value, dict):
            self._validate_mapping_value_format(value)

    def _validate_value_rules(self, value: Any):
        """Valida se o valor está dentro dos limites numéricos.

        Args:
            value (Any): O valor a ser validado.

        Raises:
            configerrors.ConfigOutOfRangeError: Ocorre quando o valor é do tipo `int` ou `float` e está fora dos limites
                numéricos mínimo ou máximo.
        """
        if isinstance(value, (int, float)):
            if self.min_value is not None and value < self.min_value:
                raise configerrors.ConfigOutOfRangeError(
                    value, self.section, self.option, "min", self.min_value
                )
            if self.max_value is not None and value > self.max_value:
                raise configerrors.ConfigOutOfRangeError(
                    value, self.section, self.option, "max", self.max_value
                )
