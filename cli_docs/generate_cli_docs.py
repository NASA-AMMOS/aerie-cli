"""
Generates docs for CLI command files to Markdown files in /cli_docs folder
    ** Note - run while in `cli_docs/` directory so files generate in correct spot
"""

import subprocess
import os
import sys
import typer

path_to_commands = "../src/aerie_cli/commands"

#app commands from /commands directory
for filename in os.listdir(path_to_commands):
    total_filepath = os.path.join(path_to_commands, filename)
    if os.path.isfile(total_filepath):
        input_name = filename[:-3]

        #skip command_context.py for now
        if(filename != 'command_context.py'):
            #create a new file if doesn't exist 
            output_file = open(input_name + ".md", "w")

            try:
                #run typer for all files that uses typer's '@app.command'
                subprocess.run(['typer', total_filepath, 'utils', 'docs', 
                                "--name", 'aerie-cli ' + input_name ,
                                "--output", input_name + ".md"])
            except subprocess.CalledProcessError as e: 
                print(f"Subprocess failed for {filename}: {e}")

#generate docs for app.py
path_to_app = "../src/aerie_cli/app.py"

try:
    output_file = open("app.md", "w")
    #run typer for all files that uses typer's '@app.command'
    subprocess.run(['typer', path_to_app, 'utils', 'docs', 
                    "--name", 'aerie-cli' ,
                    "--output", "app.md"])
except subprocess.CalledProcessError as e: 
    print(f"Subprocess failed for {filename}: {e}")