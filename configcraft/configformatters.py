"""
Este módulo fornece funções utilitárias para formatar textos como comentários,
facilitando a criação de comentários de uma linha ou múltiplas linhas em código.
"""


def format_comment_line(text: str):
    """
    Retorna o texto formatado como um comentário de uma linha.

    Esta função adiciona o caractere '#' no início da linha, transformando o
    texto fornecido em um comentário válido para código. A função inclui uma
    quebra de linha após o comentário.

    Args:
        text (str): O texto que será formatado como um comentário.

    Returns:
        str: O texto formatado como comentário, precedido pelo caractere '#' e
            seguido por uma quebra de linha.
    """
    return f"# {text}\n"


def format_multiline_comment(text: str):
    """
    Divide o texto através das quebras de linha e devolve cada linha como um
    comentário formatado.

    Esta função divide o texto em múltiplas linhas usando a quebra de linha
    e chama a função `format_comment_line` para cada linha. O resultado é um
    iterável contendo as linhas de comentário formatadas.

    Parâmetros:
        text (str): O texto a ser dividido e formatado.

    Retorna:
        map: Um objeto `map` contendo as linhas de comentário formatadas, cada
            uma precedida pelo caractere '#'.
    """
    return map(format_comment_line, text.split("\n"))
