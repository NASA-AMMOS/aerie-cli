from typing import List

import typer
import logging

def select_from_list(options: List[str], prompt: str = 'Select an option'):
    while True:
        for i, c in enumerate(options):
            print(f"\t{i+1}) {c}")
        choice_id = typer.prompt(prompt)
        logging.debug(f"Prompt: {prompt}")
        logging.debug(f"Options: {options}")
        logging.debug(f"Selected {choice_id}")
        try:
            return options[int(choice_id)-1]
        except (KeyError, ValueError):
            pass
