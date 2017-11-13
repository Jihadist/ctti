"""
Invoke as follows:

    python inception.py path/to/project/sources [libclang.so full path]
"""


from clang.cindex import Index, Cursor, CursorKind, Config
import os, sys, re, fnmatch

def align_doc(doc):
    processed_lines = []

    for line in doc.split('\n'):
        stripped = line.strip()
        aligned  = '{}{}'.format(' '*(0 if stripped.startswith('/') else 5), stripped)

        processed_lines.append(aligned)

    return '\n'.join(processed_lines)

def parse_cursor(c):
    element = {}
    element['file'] = c.location.file
    element['line'] = c.location.line
    element['spelling'] = c.spelling
    element['kind'] = '{}'.format(c.kind)
    element['cursor'] = c

    return element;

def generate_symbols(elements):
    with open('symbols.hpp', mode='w+') as file:
        file.write("""
/*
 * Generated from sources
 * Symbolic introspection the lazy way
 */

#ifndef CTTI_SYMBOLS_HPP
#define CTTI_SYMBOLS_HPP
""")

        for element in elements.values():
            file.write("""
#ifndef CTTI_SYMBOLS_{0}_DEFINED
#define CTTI_SYMBOLS_{0}_DEFINED
CTTI_DEFINE_SYMBOL({0}); // from {1}:{2} ({3})
#endif // CTTI_SYMBOLS_{0}_DEFINED

""".format(element['spelling'], element['file'], element['line'], element['kind']));

        file.write("""
#endif // CTTI_DEFINE_SYMBOLS_HPP""");

def parse(project_includedir, libclang_lib):
    if libclang_lib != "":
        Config.set_library_file(libclang_lib)

    index = Index.create()
    values = {};
    processed_files = [];

    valid_kinds = [
        CursorKind.NAMESPACE,
        CursorKind.CLASS_DECL,
        CursorKind.STRUCT_DECL,
        CursorKind.UNION_DECL,
        CursorKind.ENUM_DECL,
        CursorKind.FIELD_DECL,
        CursorKind.TYPE_ALIAS_DECL,
        CursorKind.NAMESPACE_ALIAS,
        CursorKind.CLASS_TEMPLATE,
        CursorKind.CXX_METHOD,
        CursorKind.ENUM_CONSTANT_DECL
    ];

    invalid_names = [
        "",
        "static_assert", # An static assert expression is parsed as a CXX METHOD, lol
        "std",
        "operator()",
        "operator+",
        "operator++",
        "operator+=",
        "operator-",
        "operator--",
        "operator-=",
        "operator<",
        "operator<=",
        "operator<<",
        "operator>",
        "operator>=",
        "operator>>",
        "operator=",
        "operator*=",
        "operator->",
        "operator*",
        "operator==",
        "operator!=",
        "operator~",
    ];

    def visitor(cursor):
        if cursor.spelling not in invalid_names and \
                cursor.kind in valid_kinds and \
                cursor.spelling not in values:
            print '{}# {}:{}: {} (Kind={})'.format(len(values), cursor.location.file, cursor.location.line, cursor.spelling, cursor.kind)
            values[cursor.spelling] = parse_cursor(cursor)

        if (cursor.kind == CursorKind.TRANSLATION_UNIT and not cursor.location.file in processed_files) or \
                cursor.kind != CursorKind.TRANSLATION_UNIT:
            for c in cursor.get_children():
                visitor(c)

    for root, dirnames, filenames in os.walk(project_includedir):
        for filename in \
                fnmatch.filter(filenames, '*.pb.h') + \
                fnmatch.filter(filenames, '*.pb.cc') + \
                fnmatch.filter(filenames, '*.h') + \
                fnmatch.filter(filenames, '*.hpp') + \
                fnmatch.filter(filenames, '*.c') + \
                fnmatch.filter(filenames, '*.cpp'):
            file = os.path.join(root, filename)
            tu = index.parse(file)
            visitor(tu.cursor)

    generate_symbols(values)

def main():
    project_includedir = sys.argv[1]
    libclang_lib = "";

    if len(sys.argv) > 2:
        libclang_lib = sys.argv[2]

    parse(project_includedir, libclang_lib)

if __name__ == '__main__':
    main()
