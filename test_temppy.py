import unittest
from temppy import render
from temppy.temppy import EvaluationError
from temppy.temppy import ControlStructureError


class SimpleLineTestCase(unittest.TestCase):
    def test_single_variable(self):
        result = render({'number': 42}, 'the number is {number}')
        self.assertEqual(result, 'the number is 42')

    def test_nesting(self):
        result = render({'holder': {'number': 42}}, 'the number is {holder["number"]}')
        self.assertEqual(result, 'the number is 42')

    def test_some_math(self):
        result = render({}, 'the number is {21 * 2}')
        self.assertEqual(result, 'the number is 42')

    def test_some_formatting(self):
        result = render({}, "x is {'-'.join(['x'] * 10)}")
        self.assertEqual(result, 'x is x-x-x-x-x-x-x-x-x-x')

    def test_ignore_empty(self):
        result = render({}, "x is {}")
        self.assertEqual(result, 'x is {}')


class ForLoopTestCase(unittest.TestCase):
    def test_single_forloop(self):
        result = render({'xs': [1, 2, 3]}, """{for x in xs}
{x}
{endfor}""")
        self.assertEqual(result, '1\n2\n3')

    def test_single_forloop_with_whitespace(self):
            result = render({'xs': [1, 2, 3]}, """
                {for x in xs}
{x}
    {endfor}""")
            self.assertEqual(result, '\n1\n2\n3')

    def test_two_forloops(self):
        result = render({'xs': [1, 2, 3]}, """{for x in xs}
{x}
{endfor}
---
{for y in ['a', 'b', 'c']}
{y}<
{endfor}""")
        self.assertEqual(result, '1\n2\n3\n---\na<\nb<\nc<')

    def test_nested_forloops(self):
        result = render({'xs': [1, 2]}, """{for x in xs}
{for y in [3, 4]}
{x}-{y}
{endfor}
{endfor}""")
        self.assertEqual(result, '1-3\n1-4\n2-3\n2-4')

    def test_multiassignment(self):
        result = render({'xs': [[1, 2], [3, 4]]}, """{for x, y in xs}
{x}-{y}
{endfor}""")
        self.assertEqual(result, '1-2\n3-4')



class IfStatementTestCase(unittest.TestCase):
    def test_if_statement_true(self):
        result = render({'x': True}, """{if x}
x
{endif}""")
        self.assertEqual(result, 'x')

    def test_if_statement_false(self):
        result = render({'x': False}, """{if x}
x
{endif}""")
        self.assertEqual(result, '')

    def test_if_else_statement_true(self):
        result = render({'x': True}, """{if x}
x
{else}
y
{endif}""")
        self.assertEqual(result, 'x')

    def test_if_else_statement_false(self):
        result = render({'x': False}, """{if x}
x
{else}
y
{endif}""")
        self.assertEqual(result, 'y')

    def test_if_false_elif_true_statement(self):
        result = render({'x': False, 'y': True}, """{if x}
x
{elif y}
y
{endif}""")
        self.assertEqual(result, 'y')

    def test_if_false_elif_false_elif_true_statement(self):
        result = render({'x': False, 'y': False, 'z': True}, """{if x}
x
{elif y}
y
{elif z}
z
{endif}""")
        self.assertEqual(result, 'z')

    def test_if_false_elif_true_elif_true_statement(self):
        result = render({'x': False, 'y': True, 'z': True}, """{if x}
x
{elif y}
y
{elif z}
z
{endif}""")
        self.assertEqual(result, 'y')

    def test_if_false_elif_false_else_statement(self):
        result = render({'x': False, 'y': False}, """{if x}
x
{elif y}
y
{else}
z
{endif}""")
        self.assertEqual(result, 'z')


class WithStatementTestCase(unittest.TestCase):
    def test_with_statement(self):
        result = render({'x': 1}, """{with y = x}
{y}""")
        self.assertEqual(result, '1')

    def test_with_statement_inside_loop(self):
        result = render({'xs': [1, 2]}, """{for x in xs}
{with y = x + 1}
v: {x}-{y}
{endfor}""")
        self.assertEqual(result, 'v: 1-2\nv: 2-3')

    def test_multiassignment(self):
        result = render({'xs': [1, 2]}, """{with x,y = xs}
{x}-{y}""")
        self.assertEqual(result, "1-2")


class ErrorTestCase(unittest.TestCase):
    def test_unknown_variable(self):
        try:
            render({}, '{x}')
        except EvaluationError as e:
            self.assertEqual(str(e), "at [0]: name 'x' is not defined")

    def test_unknow_variable_in_for(self):
        try:
            render({}, '{for x in xs}\n{endfor}')
        except EvaluationError as e:
            self.assertEqual(str(e), "at [0]: name 'xs' is not defined")

    def test_unknow_variable_in_elif(self):
        try:
            render({}, """{if False}
{elif x}
x
{endif}""")
        except EvaluationError as e:
            self.assertEqual(str(e), "at [1]: name 'x' is not defined")

    def test_for_closed_before_if(self):
        try:
            render({}, """{for x in [1]}
{if x}
{endfor}
""")
        except ControlStructureError as e:
            self.assertEqual(str(e), "at [2]: end of ForLoop doesnt match any start")

    def test_if_closed_before_for(self):
        try:
            render({}, """{if True}
{for x in [1]}
{endif}
""")
        except ControlStructureError as e:
            self.assertEqual(str(e), "at [2]: end of IfStatement doesnt match any start")


if __name__ == '__main__':
    unittest.main()
