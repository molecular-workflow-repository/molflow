#!/usr/bin/env python

from __future__ import print_function
import argparse
from pathlib import Path

from . import info, convert, versioning
from .run import run_workflow
from .runners import cwl


DESCRIPTION = 'Command line interface for running workflows in the molecular-workflow-repository.'

workflow_name_parser = argparse.ArgumentParser(add_help=False)
workflow_name_parser.add_argument('workflow_name', help='Name or path of the workflow')


def parser():
    parser = argparse.ArgumentParser('molflow', description=DESCRIPTION,
                                     epilog="Run 'molflow [cmd] --help' for detailed "
                                            "help a specific command.")

    cmdparser = parser.add_subparsers(dest='cmd')
    run_argparser(cmdparser)
    list_argparser(cmdparser)
    info_argparser(cmdparser)
    convert_argparser(cmdparser)
    create_argparser(cmdparser)
    tag_argparser(cmdparser)
    cwl_argparser(cmdparser)
    return parser


def tag_argparser(cmdparser):
    tag = cmdparser.add_parser('tag', help='Tag a development workflow with a new version',
                                parents=[workflow_name_parser])
    tag.add_argument('newversion', help='Semantic version number')
    tag.set_defaults(func=versioning.tag_workflow)


def create_argparser(cmdparser):
    create = cmdparser.add_parser('create', help='Create a workflow',
                                   parents=[workflow_name_parser])
    create.add_argument('path', help='Create workflow template in this directory')


def info_argparser(cmdparser):
    infoparser = cmdparser.add_parser('info', help='Examine a workflow',
                                       parents=[workflow_name_parser])
    infoparser.add_argument('--show-tasks', help='Show all tasks in this workflow')
    infoparser.set_defaults(func=info.print_metadata)


def list_argparser(cmdparser):
    lister = cmdparser.add_parser('list', help='List available workflows')
    lister.add_argument('keywords', nargs='*',
                        help="Only list workflows with these keywords")
    lister.set_defaults(func=info.list_workflows)


def run_argparser(cmdparser):
    run = cmdparser.add_parser('run', help='Run a workflow', parents=[workflow_name_parser])
    run.add_argument('inputs', nargs='*',
                     help='Inputs in the form "name=value", OR path to a JSON or YAML file'
                          'specifying the inputs')
    run.add_argument('--outputdir', '-o',
                     help='Directory to write output to. The directory is '
                     "created if it doesn't exist. (default: '[workflow name].run)'")
    run.add_argument('--overwrite', action='store_true',
                     help='Overwrite the old output directory')
    run.add_argument('--saveall', action='store_true',
                     help="Save each intermediate step's outputs as well as the workflow's outputs")
    run.add_argument('--maxcpus', type=int, default=4,
                     help='Maximum number of CPUs to allocate (default: 4)')
    run.add_argument('--quiet', '-q', action='store_true',
                     help='Only print final output and fatal errors (no logging messages)')
    run.set_defaults(func=run_workflow)


def convert_argparser(cmdparser):
    converter = cmdparser.add_parser('convert',
                                      help='Convert molecular files, strings, and python objects',
                                      epilog=convert.get_help().replace('\n', '|n'),
                                      formatter_class=MultilineFormatter)
    converter.add_argument('input', help='Input file or string')
    converter.add_argument('--input-format', '--fi',
                           help='Input format (default: determined from input)')
    converter.add_argument('output', help='Ouput filename')
    converter.add_argument('--output-format', '--fo',
                           help='Input format (default: determined from output filename)')
    converter.set_defaults(func=convert.drive_converter)


def cwl_argparser(cmdparser):
    cwlexporter = cmdparser.add_parser('writecwl',
                                       help='Export workflow in Common Workflow Language (CWL) 1.0',
                                       parents=[workflow_name_parser])
    cwlexporter.add_argument('--outputdir', '-o', default=None,
                             help='Directory to write output to. The directory is '
                                  "created if it doesn't exist. (default: [workflow name].cwl)")
    cwlexporter.set_defaults(func=cwl.export_cwl)




class MultilineFormatter(argparse.HelpFormatter):
    """ FROM http://stackoverflow.com/a/32974697/1958900
    """
    def _fill_text(self, text, width, indent):
        import textwrap as _textwrap
        text = self._whitespace_matcher.sub(' ', text).strip()
        paragraphs = text.split('|n ')
        multiline_text = ''
        for paragraph in paragraphs:
            formatted_paragraph = _textwrap.fill(paragraph, width, initial_indent=indent, subsequent_indent=indent) + '\n'
            multiline_text = multiline_text + formatted_paragraph
        return multiline_text


def main():
    args = parser().parse_args()
    args.func(args)


def _runargs(argstring):
    """ Pass CLI args via a string for debugging/testing """
    args = parser().parse_args(argstring.split())
    args.func(args)

