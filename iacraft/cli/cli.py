import click
import openai
from markdown_it.main import MarkdownIt


@click.group()
def cli():
    pass


@click.command()
@click.option('--software', required=True, prompt=True)
@click.option('--save', type=click.Path())
@click.option('-c', '--context', type=click.Path(exists=True, dir_okay=False, resolve_path=True), multiple=True)
@click.option('-t', '--target', default="code")
@click.argument('what', nargs=-1)
def get(what, software, save, context, target):
    retrying = True

    while retrying:
        click.echo('Getting result...')

        # add system messages
        messages = [{
            "role": "system",
            "content": f"You are a CLI tool that generates IaC, database query, CLI command, devops script, config files. "
                       f"You output {target} for {software}. You output error messages if necessary."
        }]

        # add context
        user_message = ""
        if context and len(context) > 0:
            user_message += "Given the existing files:\n"
            for ctx_file in context:
                with open(ctx_file) as f:
                    lines = f.readlines()
                    user_message += f"{ctx_file}:\n```\n{lines}\n```\n"

        # add user message
        user_message += f"The generated result will be saved as {save}. Generate {target} for {software} based on the instruction:\n{''.join(list(what))}"
        messages.append({
            "role": "user",
            "content": user_message,
        })

        completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages, temperature=0.5)
        assistant_message = completion["choices"][0]["message"]["content"]
        markdown_parsed = MarkdownIt().parse(assistant_message)
        code_blocks = [item for item in markdown_parsed if item.tag == "code"]
        if len(code_blocks) == 0:
            print(assistant_message)
        else:
            print(code_blocks[0].content)

        if save:
            choice = click.prompt("Please choose one of", type=click.Choice(['save', 's', 'retry', 'r', 'exit', 'e']))
            if choice == 'save' or choice == 's':
                retrying = False
                with open(save, 'w') as f:
                    f.write(code_blocks[0].content)
                    click.echo(f"Saved the result to {save}.")
            elif choice == 'retry' or choice == 'r':
                retrying = True
            else:
                retrying = False
                click.echo("Bye!")


cli.add_command(get)

if __name__ == '__main__':
    cli()
