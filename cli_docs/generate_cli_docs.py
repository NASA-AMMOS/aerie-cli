"""
Generates docs for CLI command files to Markdown files in /cli_docs folder
"""

import subprocess
import os
import sys
import typer

path_to_commands = "../src/aerie_cli/commands"

for filename in os.listdir(path_to_commands):
    total_filepath = os.path.join(path_to_commands, filename)
    if os.path.isfile(total_filepath):
        input_name = filename[:-3]

        #skip command_context.py for now
        if(filename != 'command_context.py'):
            try:
                #run typer for all files that uses typer's '@app.command'
                subprocess.run(['typer', total_filepath, 'utils', 'docs', 
                                "--name", 'aerie-cli ' + input_name ,
                                "--output", input_name + '.md'])
            except subprocess.CalledProcessError as e: 
                print(f"Subprocess failed for {filename}: {e}")