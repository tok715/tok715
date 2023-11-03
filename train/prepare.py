import json

import click


@click.command()
@click.option('--input', 'opt_input', help='input text file', type=str)
@click.option('--output', 'opt_output', help='output json file', type=str)
def main(opt_input: str, opt_output: str):
    with open(opt_input) as f:
        content = f.read()

    output = []
    for i, raw_conversation in enumerate(content.split('\n===\n')):
        raw_conversation = raw_conversation.strip()
        if not raw_conversation:
            continue
        conversations = []
        for j, message in enumerate(raw_conversation.split('\n---\n')):
            conversations.append({
                'from': 'user' if j % 2 == 0 else 'assistant',
                'value': message.strip()
            })
        output.append({
            'id': f'conversation_{i}',
            'conversations': conversations,
        })

    with open(opt_output, 'w') as f:
        json.dump(output, f)


if __name__ == '__main__':
    main()
