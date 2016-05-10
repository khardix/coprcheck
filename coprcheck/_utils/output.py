"""Formatted output utilities."""


from contextlib import contextmanager
from functools import partial
import sys

from blessings import Terminal
from tqdm import tqdm


_term = Terminal()


print_progress = partial(print, file=sys.stderr, flush=True)
"""Print message on stderr with immediate flushing. Useful for progress reporting."""


@contextmanager
def running_task(name: str) -> None:
    """Indicate that the task is running, and successfull/failed exit.

    The task is reported to succeeded if finished without exception.
    """

    print_progress('Running {}...'.format(name), end='\t')

    try:
        yield
    except Exception:
        # Report failure and reraise the exception to be handled outside
        print_progress('[{c}{s:^4}{n}]'.format(
            c=_term.bold_red,
            s='FAIL',
            n=_term.normal,
            ))
        raise
    else:
        print_progress('[{c}{s:^4}{n}]'.format(
            c=_term.green,
            s='OK',
            n=_term.normal,
            ))


def report_failed(report: dict) -> None:
    """Print (colored) report of reported fialures.

    Expected format of report:
        {package: {check: {short_name: [diagnostics]}}}
    """

    pkg_color = _term.bold_white
    check_color = _term.yellow
    code_color = _term.bold_red
    diag_color = _term.white

    indent = '\t'

    print('Failed packages:')
    for package, checks in report.items():
        message = (indent*0, pkg_color(package), ':')
        print(*message, sep='')

        for check, errors in checks.items():
            message = (indent*1, check_color(check), ':')
            print(*message, sep='')

            for code, diagnostics in errors.items():
                message = (indent*2, code_color(code), ':')
                print(*message, sep='')

                for diag in diagnostics:
                    message = (indent*3, '- ', diag_color(diag))
                    print(*message, sep='')
