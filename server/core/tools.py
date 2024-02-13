import re

counter_pattern = re.compile(r'(({})|({same}))')


def set_counters(text, counter=1, **kwargs):
    if not isinstance(text, str):
        return text
    for key, value in kwargs.items():
        text = text.replace(('{%s}' % key), f'{value}')

    bracket_conflict = text.count('\'{}\'')
    if bracket_conflict:
        replace_str = '__EMPTY_JSON__' if text.count('__JSON_EMPTY__') else '__JSON_EMPTY__'
        text = text.replace('\'{}\'', replace_str)

    args = []
    for (counter_place, _, _) in re.findall(counter_pattern, text):
        args.append(f'${counter}')
        if counter_place != '{same}':
            counter += 1

    text = text.replace('{same}', '{}')
    text = text.format(*args)

    if bracket_conflict:
        text = text.replace(replace_str, '\'{}\'')

    return text, counter
