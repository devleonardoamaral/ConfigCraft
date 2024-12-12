from setuptools import setup, find_packages


def read_file(filename):
    with open(filename, encoding="utf-8") as f:
        return f.read()


setup(
    name="configcraft",
    version="0.0.1",
    packages=find_packages(include=["configcraft"]),
    install_requires=[],
    author="Leonardo Amaral",
    author_email="leonardo_amaral98@hotmail.com",
    description=(
        "ConfigCraft é uma biblioteca Python para gerenciar arquivos de"
        " configuração de forma eficiente e intuitiva. Ela permite que você"
        " crie e gerencie diferentes perfis de configuração, além de facilitar"
        " a escrita e leitura dos arquivos com segurança e atomicidade. Ideal"
        " para projetos que exigem flexibilidade no gerenciamento de"
        " configurações."
    ),
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.12",
    license=read_file("LICENSE"),
)
