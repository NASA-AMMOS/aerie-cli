import typer
import logging

class TyperLoggingHandler(logging.Handler):
    """A logger that uses typer.echo"""
    def emit(self, record: logging.LogRecord) -> None:
        fg = None
        bg = None
        if record.levelno == logging.WARNING:
            fg = typer.colors.YELLOW
        elif record.levelno == logging.CRITICAL:
            fg = typer.colors.BRIGHT_WHITE
            bg = typer.colors.BRIGHT_RED
        elif record.levelno == logging.ERROR:
            fg = typer.colors.BRIGHT_RED
        typer.secho(self.format(record), bg=bg, fg=fg)