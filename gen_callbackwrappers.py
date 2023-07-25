from argparse import ArgumentParser
import jq
import json
import re

def readFile(filename:str):
    with open(filename) as file:
        return file.read()

def loadJson(filename: str):
    return json.loads(readFile(filename))

def prefixed_arg_name(arg, prefix = ""):
    arg_name = arg["name"]
    return f"{arg_name}" if not prefix else f"{prefix}.{arg_name}"

def get_arg_repr(arg, prefix = ""):
    if arg["Klass"] == "CtypesTypedef":
        return prefixed_arg_name(arg, prefix)
    elif arg["Klass"] == "CtypesPointer":
        return f'POINTER({get_arg_repr(arg["destination"], prefix)})'
    elif arg["Klass"] == "CtypesSimple":
        return prefixed_arg_name(arg, prefix)
    elif arg["Klass"] == "CtypesArray":
        return f'POINTER({get_arg_repr(arg["base"], prefix)})'
    else:
        raise Exception(f'Don\'t know how to deal with {arg["Klass"]}!')

def get_args_typelist(args, prefix = ""):
    typelist = []
    for arg in args:
        typelist.append(f"{get_arg_repr(arg, prefix)}")

    return typelist

def get_args_names(args):
    names = []
    for arg in args:
        names.append(arg["identifier"])

    return names

def lower_first(s): 
    return s[:1].lower() + s[1:] if s else ''

ignore_funcs = [
    "ZP_AcquireModuleFunc",
    "ZP_ReleaseModuleFunc",
    "ZP_InitZPM",
    "ZP_ShutdownZPM"
]

source = []

parser = ArgumentParser(description = "Generate callback decorators from ctypes bindings + JSON representation of a C header file")
parser.add_argument("--bindings", help = "Path to the the bindings python file", required = True)

parser.add_argument("--append", help = "Append to ctypes bindings file", required = False, default = True)
parser.add_argument("--output", help = "Path to the output bindings file", required = False, default = None)

parser.add_argument("--json", help = "Path to the ctypes JSON file", required = True)

parser.add_argument("--wrap", "-w", required = False, default = ".*", help = "Regex of function names to wrap")
parser.add_argument("--ignore", "-i", nargs = "+", default = [], required = False, help = "Function names to ignore")
args = parser.parse_args()

source.append(f"from typing import Callable")
source.append("")

ctypes_json = loadJson(args.json)
ctypes_bindings = readFile(args.bindings)
func_names = jq.compile('.[] | select(.ctype.Klass == "CtypesFunction") | .name').input(ctypes_json).all()
for func_name in func_names:
    # If we can't match it in functions to wrap or the function name is ignored, move on
    if not re.match(args.wrap, func_name) or str(func_name) in args.ignore:
        continue

    # Find the corresponding definition in the ctypes bindings
    signature_types = re.findall(rf"^{func_name} = CFUNCTYPE\((.*)\)", ctypes_bindings, re.MULTILINE)[0].split(",")
    
    argTypes = signature_types[1:]
    argNames = jq.compile(f'.[] | select(.ctype.Klass == "CtypesFunction" and .name == "{func_name}") | .ctype.argtypes[].identifier').input(ctypes_json).all()

    source.append(fr"def {func_name}Type(f: Callable[[{','.join(argTypes)}], {signature_types[0]}]):")
    source.append(f"    @CFUNCTYPE({','.join(signature_types)})")
    source.append(f"    def callbackHandler({', '.join(argNames)}):")
    source.append(f"        return f({', '.join(argNames)})")
    source.append("    ")
    source.append("    return callbackHandler")

mode = 'w'
if args.append:
    mode = 'a'
    args.output = args.bindings
with open(args.output, mode, encoding='utf-8') as f:
    for line in source:
        f.write(f"{line}\n")