import re


def camelcase_to_underscore(name: str) -> str:
    return "_".join(
        word.lower() for word in re.split(r"([A-Z]{1}[a-z]+|[0-9]+)", name) if word
    )
