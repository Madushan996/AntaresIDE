"""The help panel's reference. Made by tools/make_help.py from the Antares
manual (version 0.5.0); don't edit by hand."""

VERSION = '0.5.0'

BUILTINS = {
    "zeros": {
        "group": "Making tensors",
        "sig": "zeros(d1, d2, ...)",
        "desc": "Tensor of the given shape filled with 0. Sizes may also be one list"
    },
    "ones": {
        "group": "Making tensors",
        "sig": "ones(d1, d2, ...)",
        "desc": "Tensor filled with 1"
    },
    "rand": {
        "group": "Making tensors",
        "sig": "rand(d1, ...)",
        "desc": "Uniform random numbers in 0..1. rand() gives one number"
    },
    "randn": {
        "group": "Making tensors",
        "sig": "randn(d1, ...)",
        "desc": "Normally distributed random numbers (mean 0, standard deviation 1)"
    },
    "range": {
        "group": "Making tensors",
        "sig": "range(end)  /  range(start, end [, step])",
        "desc": "Evenly spaced numbers, end not included"
    },
    "onehot": {
        "group": "Making tensors",
        "sig": "onehot(labels, n)",
        "desc": "Each label becomes a row of n with a 1 at its position"
    },
    "seed": {
        "group": "Making tensors",
        "sig": "seed(n)",
        "desc": "Sets the random seed so results repeat"
    },
    "shape": {
        "group": "Shape",
        "sig": "shape(x)",
        "desc": "Sizes of each dimension, as a tensor"
    },
    "reshape": {
        "group": "Shape",
        "sig": "reshape(x, d1, d2, ...)",
        "desc": "Same numbers, new shape"
    },
    "t": {
        "group": "Shape",
        "sig": "t(m)",
        "desc": "Transpose of a matrix"
    },
    "len": {
        "group": "Shape",
        "sig": "len(x)",
        "desc": "Length of a list, text, map, integer row, or first dimension of a tensor"
    },
    "sum": {
        "group": "Reductions",
        "sig": "sum(x [, dim])",
        "desc": "Sum of all numbers, or along one dimension"
    },
    "mean": {
        "group": "Reductions",
        "sig": "mean(x [, dim])",
        "desc": "Average of all numbers, or along one dimension"
    },
    "max": {
        "group": "Reductions",
        "sig": "max(a, ...)",
        "desc": "Largest number among all inputs"
    },
    "min": {
        "group": "Reductions",
        "sig": "min(a, ...)",
        "desc": "Smallest number among all inputs"
    },
    "argmax": {
        "group": "Reductions",
        "sig": "argmax(x)  /  argmax(row, first, last)",
        "desc": "Position of the largest value along the last dimension. Position of the first largest number from first up to (not including) last; -1 for an empty range"
    },
    "exp": {
        "group": "Maths (element by element)",
        "sig": "exp(x)",
        "desc": "Exponential and natural logarithm"
    },
    "log": {
        "group": "Maths (element by element)",
        "sig": "log(x)",
        "desc": "Exponential and natural logarithm"
    },
    "sqrt": {
        "group": "Maths (element by element)",
        "sig": "sqrt(x)",
        "desc": "Square root and absolute value"
    },
    "abs": {
        "group": "Maths (element by element)",
        "sig": "abs(x)",
        "desc": "Square root and absolute value"
    },
    "sin": {
        "group": "Maths (element by element)",
        "sig": "sin(x)",
        "desc": "Trigonometry (radians)"
    },
    "cos": {
        "group": "Maths (element by element)",
        "sig": "cos(x)",
        "desc": "Trigonometry (radians)"
    },
    "tanh": {
        "group": "Maths (element by element)",
        "sig": "tanh(x)",
        "desc": "Activation functions"
    },
    "sigmoid": {
        "group": "Maths (element by element)",
        "sig": "sigmoid(x)",
        "desc": "Activation functions"
    },
    "relu": {
        "group": "Maths (element by element)",
        "sig": "relu(x)",
        "desc": "Activation functions"
    },
    "softmax": {
        "group": "Maths (element by element)",
        "sig": "softmax(x)",
        "desc": "Probabilities along the last dimension"
    },
    "floor": {
        "group": "Maths (element by element)",
        "sig": "floor(x)",
        "desc": "Rounding down, to nearest, toward zero"
    },
    "round": {
        "group": "Maths (element by element)",
        "sig": "round(x)",
        "desc": "Rounding down, to nearest, toward zero"
    },
    "trunc": {
        "group": "Maths (element by element)",
        "sig": "trunc(x)",
        "desc": "Rounding down, to nearest, toward zero"
    },
    "clip": {
        "group": "Maths (element by element)",
        "sig": "clip(x, low, high)",
        "desc": "Forces every number into low..high"
    },
    "rows": {
        "group": "Fast row arithmetic",
        "sig": "rows(matrix)",
        "desc": "The rows as a list, without copying"
    },
    "sum_rows": {
        "group": "Fast row arithmetic",
        "sig": "sum_rows(matrix, rows [, count])",
        "desc": "Sum of the chosen rows"
    },
    "update_rows": {
        "group": "Fast row arithmetic",
        "sig": "update_rows(base, m, add, n_add, rem, n_rem [, old])",
        "desc": "Base plus some rows minus others"
    },
    "sum_product": {
        "group": "Fast row arithmetic",
        "sig": "sum_product(a, b, ...)",
        "desc": "Position-by-position product, all added up"
    },
    "screlu": {
        "group": "Fast row arithmetic",
        "sig": "screlu(x, cap)",
        "desc": "Clamp to 0..cap, then square"
    },
    "screlu_dot": {
        "group": "Fast row arithmetic",
        "sig": "screlu_dot(x, w, cap)",
        "desc": "sum_product(screlu(x, cap), w) in one step"
    },
    "compact": {
        "group": "Fast row arithmetic",
        "sig": "compact(x [, rows, cols])",
        "desc": "16-bit storage of whole numbers; m[r] is a row of a compact matrix"
    },
    "expand": {
        "group": "Fast row arithmetic",
        "sig": "expand(c)",
        "desc": "Compact numbers back to an ordinary tensor"
    },
    "int": {
        "group": "Integers",
        "sig": "int(x)",
        "desc": "x as a 64-bit integer"
    },
    "ints": {
        "group": "Integers",
        "sig": "ints(n)  /  ints(list)",
        "desc": "An integer row of n zeros, or from a list"
    },
    "popcount": {
        "group": "Integers",
        "sig": "popcount(x)",
        "desc": "Number of set bits"
    },
    "lowest_bit": {
        "group": "Integers",
        "sig": "lowest_bit(x)",
        "desc": "Position of the lowest set bit (64 if none)"
    },
    "highest_bit": {
        "group": "Integers",
        "sig": "highest_bit(x)",
        "desc": "Position of the highest set bit (-1 if none)"
    },
    "within": {
        "group": "Integers",
        "sig": "within(x, lo, hi [, name])",
        "desc": "x, if it (or every number in it) is from lo to hi; a problem otherwise"
    },
    "div": {
        "group": "Integers",
        "sig": "div(a, b)",
        "desc": "Division dropping the remainder"
    },
    "rand_bits": {
        "group": "Integers",
        "sig": "rand_bits()",
        "desc": "64 random bits"
    },
    "grad": {
        "group": "Learning",
        "sig": "grad(loss, w)",
        "desc": "Gradient of loss with respect to the learnable value w"
    },
    "push": {
        "group": "Lists and maps",
        "sig": "push(list, item)",
        "desc": "A new list with item added at the end"
    },
    "map": {
        "group": "Lists and maps",
        "sig": "map(list, f)",
        "desc": "f applied to every item"
    },
    "filter": {
        "group": "Lists and maps",
        "sig": "filter(list, f)",
        "desc": "The items for which f answers yes"
    },
    "reduce": {
        "group": "Lists and maps",
        "sig": "reduce(list, f, start)",
        "desc": "Combines items: f(f(start, a), b) ..."
    },
    "sort": {
        "group": "Lists and maps",
        "sig": "sort(list)",
        "desc": "Sorted copy; all numbers or all text"
    },
    "reverse": {
        "group": "Lists and maps",
        "sig": "reverse(x)",
        "desc": "Reversed list or text"
    },
    "slice": {
        "group": "Lists and maps",
        "sig": "slice(x, start [, end])",
        "desc": "Part of a list or text"
    },
    "has": {
        "group": "Lists and maps",
        "sig": "has(x, item)",
        "desc": "Whether a list contains an item, a map has a key, or a text contains a text"
    },
    "find": {
        "group": "Lists and maps",
        "sig": "find(x, item)",
        "desc": "Position of the first equal item in a list, or of a text in a text; -1 if not there"
    },
    "insert": {
        "group": "Lists and maps",
        "sig": "insert(list, pos, item)",
        "desc": "A new list with item put in at pos"
    },
    "remove": {
        "group": "Lists and maps",
        "sig": "remove(list, pos)",
        "desc": "A new list without the item at pos (negative counts from the end)"
    },
    "unique": {
        "group": "Lists and maps",
        "sig": "unique(list)",
        "desc": "The items without repeats, in the order they first appear"
    },
    "sort_by": {
        "group": "Lists and maps",
        "sig": "sort_by(list, f)",
        "desc": "Sorted copy, by the number or text f gives for each item"
    },
    "keys": {
        "group": "Lists and maps",
        "sig": "keys(map)",
        "desc": "Field names and field values"
    },
    "values": {
        "group": "Lists and maps",
        "sig": "values(map)",
        "desc": "Field names and field values"
    },
    "join": {
        "group": "Lists and maps",
        "sig": "join(list [, sep])",
        "desc": "Items joined into text"
    },
    "upper": {
        "group": "Text",
        "sig": "upper(t)",
        "desc": "Change case"
    },
    "lower": {
        "group": "Text",
        "sig": "lower(t)",
        "desc": "Change case"
    },
    "trim": {
        "group": "Text",
        "sig": "trim(t)",
        "desc": "Remove spaces from both ends"
    },
    "split": {
        "group": "Text",
        "sig": "split(t [, sep])",
        "desc": "Split on spaces, or on a separator"
    },
    "lines": {
        "group": "Text",
        "sig": "lines(t)",
        "desc": "Split into lines"
    },
    "replace": {
        "group": "Text",
        "sig": "replace(t, from, to)",
        "desc": "Replace every occurrence"
    },
    "text": {
        "group": "Text",
        "sig": "text(v)",
        "desc": "Any value as text"
    },
    "number": {
        "group": "Text",
        "sig": "number(v)",
        "desc": "Text, yes/no or integer as an ordinary number"
    },
    "fixed": {
        "group": "Text",
        "sig": "fixed(x, places)",
        "desc": "A number as text with exactly that many digits after the point"
    },
    "pad": {
        "group": "Text",
        "sig": "pad(v, width [, side [, fill]])",
        "desc": "Text padded to a width with spaces (or fill); numbers on the right, text on the left"
    },
    "code": {
        "group": "Text",
        "sig": "code(t)",
        "desc": "The number of a character, and the character with a number"
    },
    "char": {
        "group": "Text",
        "sig": "char(n)",
        "desc": "The number of a character, and the character with a number"
    },
    "save": {
        "group": "Data and files",
        "sig": "save(value, file)",
        "desc": "Store and restore any value as JSON"
    },
    "load": {
        "group": "Data and files",
        "sig": "load(file)",
        "desc": "Store and restore any value as JSON"
    },
    "exists": {
        "group": "Data and files",
        "sig": "exists(file)",
        "desc": "Whether a file (or embedded file) exists"
    },
    "read": {
        "group": "Data and files",
        "sig": "read(file)",
        "desc": "Whole-file text input and output"
    },
    "write": {
        "group": "Data and files",
        "sig": "write(file, value)",
        "desc": "Whole-file text input and output"
    },
    "read_binary": {
        "group": "Data and files",
        "sig": "read_binary(file, kind, start, count)",
        "desc": "Whole numbers from a binary file"
    },
    "json": {
        "group": "Data and files",
        "sig": "json(t)",
        "desc": "Parse and produce JSON"
    },
    "to_json": {
        "group": "Data and files",
        "sig": "to_json(v)",
        "desc": "Parse and produce JSON"
    },
    "program_folder": {
        "group": "Data and files",
        "sig": "program_folder()",
        "desc": "Folder of the running program"
    },
    "append": {
        "group": "Data and files",
        "sig": "append(file, value)",
        "desc": "Add to the end of a file; remove a file"
    },
    "delete": {
        "group": "Data and files",
        "sig": "delete(file)",
        "desc": "Add to the end of a file; remove a file"
    },
    "files": {
        "group": "Data and files",
        "sig": "files([folder])",
        "desc": "Names in a folder"
    },
    "args": {
        "group": "Data and files",
        "sig": "args()",
        "desc": "What was typed after the program's name"
    },
    "env": {
        "group": "Data and files",
        "sig": "env(name)",
        "desc": "A setting of the computer, or nothing"
    },
    "input": {
        "group": "Data and files",
        "sig": "input([prompt])",
        "desc": "Read a line from the user"
    },
    "input_waiting": {
        "group": "Data and files",
        "sig": "input_waiting()",
        "desc": "Whether input is waiting"
    },
    "key": {
        "group": "Live screens",
        "sig": "key()",
        "desc": "The pressed key, or nothing"
    },
    "wait": {
        "group": "Live screens",
        "sig": "wait(seconds)",
        "desc": "Pause"
    },
    "draw": {
        "group": "Live screens",
        "sig": "draw(text)",
        "desc": "Redraw the screen in place"
    },
    "clear": {
        "group": "Live screens",
        "sig": "clear()",
        "desc": "Clear the screen"
    },
    "kind": {
        "group": "Other",
        "sig": "kind(v)",
        "desc": "The kind of a value, as text"
    },
    "clock": {
        "group": "Other",
        "sig": "clock()",
        "desc": "Current time in seconds"
    },
    "now": {
        "group": "Other",
        "sig": "now()",
        "desc": "The local date and time, as a map"
    },
    "check": {
        "group": "Other",
        "sig": "check(cond [, message])",
        "desc": "Raise a problem when cond is no"
    },
    "fail": {
        "group": "Other",
        "sig": "fail([message])",
        "desc": "Raise a problem"
    }
}

STATEMENTS = {
    "show": {
        "sig": "show a, b",
        "desc": "Prints values on one line, separated by spaces."
    },
    "when": {
        "sig": "when cond { } else when cond { } else { }",
        "desc": "Runs a block only when a condition is yes; else when and else handle the other cases."
    },
    "else": {
        "sig": "else { }",
        "desc": "The block a when (or try) runs otherwise."
    },
    "repeat": {
        "sig": "repeat n { }  /  repeat n as i { }",
        "desc": "Runs a block n times; with as i, i counts 1, 2, ... n."
    },
    "each": {
        "sig": "each x in list { }",
        "desc": "Runs a block once for every item of a list, letter of a text or field of a map."
    },
    "while": {
        "sig": "while cond { }",
        "desc": "Repeats a block while a condition stays yes."
    },
    "stop": {
        "sig": "stop",
        "desc": "Leaves the loop it is in, at once."
    },
    "skip": {
        "sig": "skip",
        "desc": "Jumps to the next round of the loop it is in."
    },
    "to": {
        "sig": "to name(a, b) = expr  /  to name(a) { }",
        "desc": "Defines a function. A block function gives back its last line."
    },
    "give": {
        "sig": "give value",
        "desc": "Leaves a function at once, giving back the value."
    },
    "change": {
        "sig": "change name = value",
        "desc": "Changes a variable that lives outside the function (also change name += value)."
    },
    "try": {
        "sig": "try { } else problem { }",
        "desc": "Runs a block; if anything in it fails, runs the else block instead, with the message."
    },
    "use": {
        "sig": "use \"file\"",
        "desc": "Runs another file (file.ant, next to this one) once, making its functions available."
    },
    "learn": {
        "sig": "learn w = value",
        "desc": "Makes a value that learning (descend) may adjust."
    },
    "descend": {
        "sig": "descend loss by rate [using adam]",
        "desc": "Adjusts every learnable value the loss depends on, to make the loss smaller."
    },
    "model": {
        "sig": "model name = \"anthropic:model\" [with {system: \"...\"}]",
        "desc": "Declares an AI model to ask questions."
    },
    "ask": {
        "sig": "ask model \"question\" [as number | yes/no | list]",
        "desc": "Asks an AI model; the answer is text, or the kind after as."
    },
    "within": {
        "sig": "name = value within lo to hi  /  to f(x within lo to hi)",
        "desc": "Keeps a variable's numbers (or a function input) from lo to hi; anything else is a problem."
    },
    "and": {
        "sig": "a and b",
        "desc": "yes when both are yes."
    },
    "or": {
        "sig": "a or b",
        "desc": "yes when at least one is yes."
    },
    "not": {
        "sig": "not a",
        "desc": "Turns yes into no and no into yes."
    },
    "xor": {
        "sig": "a xor b",
        "desc": "For integers: the bits set in one but not both."
    },
    "in": {
        "sig": "each x in list",
        "desc": "Part of each."
    },
    "as": {
        "sig": "repeat n as i  /  ask m \"q\" as number",
        "desc": "Names the counter of repeat, or the kind of an answer."
    },
    "by": {
        "sig": "descend loss by rate",
        "desc": "Part of descend: the learning rate."
    },
    "using": {
        "sig": "descend loss by rate using adam",
        "desc": "Part of descend: sgd or adam."
    },
    "with": {
        "sig": "model m = \"...\" with {system: \"...\"}",
        "desc": "Part of model: its settings."
    },
    "yes": {
        "sig": "yes",
        "desc": "The true yes/no value."
    },
    "no": {
        "sig": "no",
        "desc": "The false yes/no value."
    },
    "nothing": {
        "sig": "nothing",
        "desc": "The value that means 'no value'."
    }
}
