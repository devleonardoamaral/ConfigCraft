"""
Este módulo fornece funções utilitárias. As funções deste módulo ão utilizadas
por outros módulos para simplificar e garantir a consistência do código.
"""

from abc import ABCMeta
from typing import Union, Optional, Iterable, Any


def validate_type(
    value: Any,
    expected: Union[type, tuple[type, ...]],
    name: Optional[str] = None,
    custom_error: Optional[Exception] = None,
):
    """Valida se o valor é do tipo informado, levantando TypeError se não for.

    Esta função verifica se o valor fornecido é do tipo esperado, e, caso
    contrário, levanta um erro do tipo `TypeError`. O erro gerado inclui
    informações detalhadas sobre o tipo esperado e o tipo real do valor.
    O nome do valor e um erro customizado podem ser fornecidos, caso desejado.

    Args:
        value (Any): O valor a ser validado.
        expected (Union[type, tuple[type, ...]]): O tipo ou tupla de tipos
            esperados para o valor. Pode ser um único tipo ou uma tupla contendo
            múltiplos tipos.
        name (Optional[str], opcional): O nome do valor, usado na mensagem de erro.
            Se não fornecido, a mensagem de erro não incluirá um nome.
        custom_error (Optional[Exception], opcional): Uma exceção customizada
            para ser levantada caso o tipo seja inválido. Se não fornecido, um
            `TypeError` padrão será levantado.

    Raises:
        TypeError: Se o valor não for do tipo esperado e nenhum erro customizado
            for fornecido.
        custom_error (Exception): Se o erro customizado for fornecido, ele será
            levantado em vez do `TypeError`.

    Examples:
        >>> validate_type(42, int)
        # Nenhum erro, pois 42 é do tipo int.

        >>> validate_type("texto", (int, float))
        Traceback (most recent call last):
            ...
        TypeError: tipo inválido: era esperado 'int, float', mas foi obtido 'str'.

        >>> validate_type("nome", str, name="variável")
        Traceback (most recent call last):
            ...
        TypeError: tipo inválido para 'variável': era esperado 'str', mas foi obtido 'str'.

        >>> validate_type(42.2, int, custom_error=ValueError)
        Traceback (most recent call last):
            ...
        ValueError: tipo inválido: era esperado 'int', mas foi obtido 'float'.
    """
    if not isinstance(expected, (type, tuple)):
        raise TypeError(
            "argumento 'expected' deve ser um tipo ou uma tupla de tipos."
        )

    if isinstance(value, expected):
        return

    types_str = ", ".join(
        t.__name__
        for t in (expected if isinstance(expected, tuple) else (expected,))
    )

    message = (
        f"tipo inválido{f' para {name!r}' if name else ''}: "
        f"era esperado {types_str!r}, mas foi obtido {type(value).__name__!r}."
    )

    if custom_error is not None:
        raise custom_error(message)
    else:
        raise TypeError(message)


def get_indexable_iterables_intersection(
    source: Iterable[Any], candidates: Iterable[Any]
):
    """Filtra e retorna um conjunto contendo apenas os valores presentes em
    ambos os objetos iteráveis.

    Esta função realiza a interseção entre dois iteráveis, retornando um conjunto
    com os elementos que estão presentes tanto no iterável `source` quanto no
    iterável `candidates`.

    Args:
        source (Iterable[Any]): O iterável de origem a ser comparado.
        candidates (Iterable[Any]): O iterável de candidatos para comparar com
            o `source`.

    Returns:
        set: Um conjunto contendo os valores presentes em ambos os iteráveis.

    >>> get_indexable_iterables_intersection([1, 2, 3], [2, 3, 4])
    {2, 3}
    """
    return set(source) & set(candidates)


def check_if_indexed_iterables_intersect(
    source: Iterable[Any], candidates: Iterable[Any]
):
    """Checa se o iterável de origem contém algum dos itens candidatos.

    Esta função verifica se existe alguma interseção entre os elementos de
    dois iteráveis. Retorna `True` se ao menos um item do iterável `candidates`
    estiver presente no iterável `source`; caso contrário, retorna `False`.

    Args:
        source (Iterable[Any]): O iterável de origem a ser verificado.
        candidates (Iterable[Any]): O iterável contendo os itens candidatos a
            serem verificados no `source`.

    Returns:
        bool: `True` se existir ao menos uma interseção entre os iteráveis,
            `False` caso contrário.

    >>> check_if_indexed_iterables_intersect([1, 2, 3], [2, 3, 4])
    True
    """
    return bool(get_indexable_iterables_intersection(source, candidates))


class PolySingleton(ABCMeta):
    def __call__(cls, name: str = "", *args: Any, **kwargs: Any) -> Any:
        validate_type(name, str, "name")

        if not hasattr(cls, "_instances"):
            cls._instances = {}

        if name not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[name] = instance

        return cls._instances[name]
