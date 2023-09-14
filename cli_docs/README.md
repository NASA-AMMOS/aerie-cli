# **Aerie-CLI Documentation**

## **CLI Commands**: 
<!-- - [`command_context`](command_context.md) -->
- [`configurations`](configurations.md)
- [`constraints`](constraints.md)
- [`expansion`](expansion.md)
- [`metadata`](metadata.md)
- [`models`](models.md)
- [`plans`](plans.md)
- [`scheduling`](scheduling.md)

---

## **How to Generate Documentation**
### **Documentation for Individual Command with Typer CLI** 
Usage:
  
```$ typer script.py utils docs --name TEXT --output FILE```

Subcommands:
- `utils`
- `docs`

Options: 
- `--name TEXT` : name of the CLI program to use in docs
    - *Ex: `--name 'aerie-cli plans'`*
- `--output FILE` : output file to write docs to
    - *Ex: `--output 'plans.md'`*

<br>

### **Documentation for All Individual Commands**
Generate documentation for all Aerie-CLI commands using the `generate_cli_docs` script.

Usage: 

```$ python3 generate_cli_docs.py```