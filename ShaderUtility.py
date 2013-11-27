import logging
logger = logging.getLogger(__name__)

import re
from subprocess import Popen, PIPE

version_declaration_pattern = r'\s*#\s*version\s+(\d+)\s+es\s*'
layour_qualifier_pattern = r'layout\s*\(\s*location\s*=\s*(\d+)\s*\)\s*'

def Preprocess(input_text):

    version = 100
    lines = input_text.splitlines()

    # check empty input
    if len(lines) == 0:
        return '', version

    # check the version
    # The valid format for version declaration:
    # whitespace_opt POUND whitespace_opt VERSION whitespace number whitespace ES whitespace_opt
    match = re.match(version_declaration_pattern, lines[0])
    if match:
        version = int(match.group(1))
        lines[0] = ''
    input_text = '\n'.join(lines)

    try:
        # Note the use of universal_newlines to treat all newlines
        # as \n for Python's purpose
        #
        command = ['cpp', '-DGL_ES']
        logger.debug('Preprocess Command : %s' % ' '.join(command))
        pipe = Popen(command, stdin=PIPE, stdout=PIPE, universal_newlines=True)
        text, error = pipe.communicate(input=input_text)
        if error:
            logger.error('Preprocess Error : %s' % error)
    except OSError as e:
        raise RuntimeError("Unable to invoke 'cpp'.  " +
            'Make sure its path was passed correctly\n' +
            ('Original error: %s' % e))

    # remove the leading comment lines
    new_lines = []
    line_number = 1
    line_marker_pattern = r'# (\d+) ".*"'
    for line in text.splitlines():
        match = re.match(line_marker_pattern, line)
        if match:
            next_line_number = int(match.group(1))
            new_lines += [''] * (next_line_number - line_number)
            line_number = next_line_number
        else:
            new_lines.append(line)
            line_number += 1
    text = '\n'.join(new_lines)

    return text, version

def ConvertESSLToCGCCompilable(source):
    lines = source.splitlines()
    for i in range(len(lines)):

        # convert "#version 300 es" to "#version 300"
        if re.match(version_declaration_pattern, lines[i]):
            lines[i] = '#version 300'

        # filter away layout qualifiers
        match = re.search(layour_qualifier_pattern, lines[i])
        if match:
            lines[i] = lines[i].replace(match.group(), '')
    return '\n'.join(lines)
