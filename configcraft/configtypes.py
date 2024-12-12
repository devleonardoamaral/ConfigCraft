"""
Este módulo contém utilitários para manipulação e geração de representações
textuais de dicas de tipos (type hints) em Python. Ele utiliza expressões
regulares para substituir termos técnicos por suas traduções em português e
formata conjuntos de tipos de maneira legível.
"""

import re
from typing import Optional


replace_dict = {
    "dict": "Dicionário",
    "list": "Lista",
    "int": "Inteiro",
    "str": "Texto",
    "bool": "Booleano",
    "float": "Decimal",
    "NoneType": "Nulo",
}
"""Um dicionário que mapeia nomes de tipos em Python (como dict, list, etc.) 
para suas descrições em português (como Dicionário, Lista, etc.)."""


def humanize_technique_type_names(text: str, replace_dict: dict[str, str]):
    """Substitui palavras específicas em um texto com base em um dicionário de
    substituições.

    Args:
        text (str): O texto onde as substituições serão realizadas.
        replace_dict (dict[str, str]): Dicionário contendo os pares de
        substituição.

    Returns:
        str: Uma string com as substituições aplicadas.
    """
    pattern = re.compile(
        "|".join(re.escape(key) for key in replace_dict.keys())
    )
    return pattern.sub(lambda match: replace_dict[match.group(0)], text)


def join_types(types: set[type]):
    """Gera uma string com os nomes dos tipos em um conjunto, separados por
    vírgula e espaço.

    Args:
        types (set[type]): Conjunto de tipos.

    Returns:
        str: Uma string contendo os nomes dos tipos separados por vírgula.
    """
    return ", ".join(map(lambda t: t.__name__, types))


def generate_dict_type_hint(key_type: type, types: set[type]):
    """Gera uma representação de dica de tipo para um dicionário, com base no
    tipo das chaves e no conjunto de tipos dos valores.

    Args:
        key_type (type): O tipo das chaves do dicionário.
        types (set[type]): Conjunto de tipos dos valores do dicionário.

    Returns:
        str: Uma string representando o tipo do dicionário.
    """
    return (
        f"dict[{key_type.__name__},"
        f" {f'[{join_types(types)}]' if len(types) > 1 else join_types(types)}]"
    )


def generate_list_type_hint(types: set[type]):
    """Gera uma representação de dica de tipo para uma lista, com base no
    conjunto de tipos de seus itens.

    Args:
        types (set[type]): Conjunto de tipos dos itens da lista.

    Returns:
        str: Uma string representando o tipo da lista.
    """
    return f"list[{join_types(types)}]"


def generate_type_hint(types: set[type], items_types: Optional[set[type]]):
    """Gera uma string representando dicas de tipo para combinações de tipos,
    incluindo listas e dicionários, com traduções aplicadas usando
    replace_dict.

    Args:
        types (set[type]): Conjunto de tipos primários.
        items_types (Optional[set[type]]): Conjunto de tipos dos itens
            (caso aplicável).

    Returns:
        str: Uma string contendo as dicas de tipos formatadas.
    """
    if items_types is None:
        items_types = set()

    parts = []

    for t in types:
        if t is list:
            if items_types:
                parts.append(generate_list_type_hint(items_types))
            else:
                parts.append("list")
        elif t is dict:
            if items_types:
                parts.append(generate_dict_type_hint(str, items_types))
            else:
                parts.append("dict")
        else:
            parts.append(t.__name__)

    return humanize_technique_type_names(", ".join(parts), replace_dict)
