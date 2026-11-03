from typing import List

import typer


def select_from_list(options: List[str], prompt: str = 'Select an option'):
    while True:
        for i, c in enumerate(options):
            print(f"\t{i+1}) {c}")
        choice_id = typer.prompt(prompt)
        try:
            return options[int(choice_id)-1]
        except (KeyError, ValueError):
            pass
