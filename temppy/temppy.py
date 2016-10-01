import re


def render(data, template):
    return Parser(template).parse().render(data)


# AST:
class Block:
    def __init__(self):
        self.children = []

    def add(self, child):
        self.children.append(child)

    def render(self, data):
        return self.render_children(data)

    def render_children(self, data):
        results = [child.render(data) for child in self.children]
        return '\n'.join([r for r in results if r is not None])


class SimpleLine:
    variable_pattern = re.compile(r'\{([^{}]+)\}')

    def __init__(self, line, line_number):
        self.line = line
        self.line_number = line_number

    def __repr__(self):
        return 'SimpleLine("{}")'.format(self.line)

    def render(self, data):
        result = self.line
        for match in self.variable_pattern.findall(result):
            replacement = str(leval(match, data, self.line_number))
            result = result.replace('{' + match + '}', replacement)
        return result


class WithStatement:
    pattern = re.compile('\s*{with (.*) = (.*)}\s*')

    def __init__(self, line, line_number):
        raw_keys, self.value = self.pattern.match(line).groups()
        self.keys = [k.strip() for k in raw_keys.split(',')]
        self.line_number = line_number

    def render(self, data):
        value = eval(self.value, data)
        insert_value(data, self.keys, value)
        return None


class ForLoop:
    start_pattern = re.compile(r'\s*{for (.*) in (.*)}\s*')
    end_pattern = re.compile(r'\s*{endfor}\s*')

    def __init__(self, line, line_number):
        raw_keys, self.iterator = self.start_pattern.match(line).groups()
        self.keys = [k.strip() for k in raw_keys.split(',')]
        self.child = Block()
        self.line_number = line_number
        self.line = None

    def add(self, child):
        self.child.add(child)

    def render(self, data):
        results = []
        self.save_value(data)
        for value in leval(self.iterator, data, self.line_number):
            self.insert_value(data, value)
            results.append(self.child.render(data))
        self.restore_value(data)
        return '\n'.join(results)

    def save_value(self, data):
        self.prev_values = []
        for k in self.keys:
            self.prev_values.append(data.get(k, None))

    def insert_value(self, data, value):
        insert_value(data, self.keys, value)

    def restore_value(self, data):
        for k, v in zip(self.keys, self.prev_values):
            data[k] = v


class IfStatement:
    start_pattern = re.compile(r'{if (.*)}')
    else_pattern = re.compile(r'\s*{else}\s*')
    elif_pattern = re.compile(r'\s*{elif (.*)}\s*')
    end_pattern = re.compile(r'\s*{endif}\s*')

    def __init__(self, line, line_number):
        self.conditions = [self.start_pattern.match(line).groups()[0]]
        self.children = [Block()]
        self.else_children = Block()
        self.current_child = self.children[-1]
        self.line_numbers = [line_number]
        self.line = None

    def add(self, child):
        if child.line and self.elif_pattern.match(child.line):
            self.children.append(Block())
            self.line_numbers.append(child.line_number)
            self.conditions.append(self.elif_pattern.match(child.line).groups()[0])
            self.current_child = self.children[-1]
        elif child.line and self.else_pattern.match(child.line):
            self.current_child = self.else_children
            return
        else:
            self.current_child.add(child)

    def render(self, data):
        results = []
        some_condition_was_true = False
        for condition, child, line_number in zip(self.conditions, self.children, self.line_numbers):
            if leval(condition, data, line_number):
                results.append(child.render(data))
                some_condition_was_true = True
                break
        if not some_condition_was_true:
            results.append(self.else_children.render(data))
        return '\n'.join(results)


# Parser:
class Parser:
    single_pattern_elements = (WithStatement, )
    start_end_patterns_elements = (ForLoop, IfStatement)

    def __init__(self, template):
        self.template = template
        self.stack = [Block()]

    def parse(self):
        for line_number, line in enumerate(self.template.splitlines()):
            self._parse_line(line, line_number)
        return self.stack[0]

    def _parse_line(self, line, line_number):
        for element in self.single_pattern_elements:
            if element.pattern.match(line):
                self.stack[-1].add(element(line, line_number))
                return
        for element in self.start_end_patterns_elements:
            if element.start_pattern.match(line):
                e = element(line, line_number)
                self.stack[-1].add(e)
                self.stack.append(e)
                return
            elif element.end_pattern.match(line):
                e = self.stack.pop()
                if not isinstance(e, element):
                    raise ControlStructureError(
                        'at [{}]: end of {} doesnt match any start'.format(line_number, element.__name__)
                    )
                return
        self.stack[-1].add(SimpleLine(line, line_number))



# Errors:
class EvaluationError(Exception):
    def __init__(self, message, line_number='?', code='?'):
        message = 'at [{}] - {}: {}'.format(line_number, code, message)
        super(EvaluationError, self).__init__(message)


class ControlStructureError(Exception):
    def __init__(self, message):
        super(ControlStructureError, self).__init__(message)


# Utils:
def leval(code, globals, line_number):
    try:
        return eval(code, globals)
    except Exception as e:
        raise EvaluationError(e, line_number, code)


def insert_value(data, keys, value):
    if len(keys) == 1:
        data[keys[0]] = value
    else:
        for k, v in zip(keys, value):
            data[k] = v
