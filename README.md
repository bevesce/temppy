# temppy
Very simple and not that powerful template engine based on eval. In under 200 lines.

## Example:
```
from temppy import render
render({'number': 42}, 'this is a number {number}')
```

## Features
##### Expressions
You can put any valid expression inside curly braces, like this:  `{21 * 2}`.

##### For loops
You can loop over iterators, like this:
```
{for x in [1, 2, 3]}
x equals {x}
{endfor}
```

##### If statements
You can use if-elif-else statements:
```
{if x}
x is true
{elif y}
y is true
{else}
x and y are false
{endif}
```

##### Setting Variable
You can set variable for later usage, like this:
```
{with x = 1}
x equals {x}
```

Notice that *for-loop*, *if-elif-else* and *with* control statements are on separate lines! 
