import argparse
import shlex
import sys
from pprint import pprint
from string import Template

import markdown
import yaml
from markdown.extensions.toc import TocExtension

# UNITS = ("html", "host", "css", "js")
UNITS = ("host", "css", "js")

FORMATS = {
    "html": 1,
    "markdown": 4,
}

cmd_start = """\
#!/usr/bin/env sh

alias moosh="{moosh}"

"""

cmd_tpl = """
moosh \
activity-add \
--name {name} \
--section {section} \
--idnumber {idnumber} \
--options={options} \
assign {courseid}
"""

cmd_tpl_options = """
--intro={intro_html}
--introformat=1
--activity={instructions_html}
--activityformat=1
--grade=10
--gradepass=5
--submissiondrafts=0
--requiresubmissionstatement=0
--attemptreopenmethod=manual
--assignsubmission_file_enabled=1
--assignsubmission_file_maxfiles=1
--assignsubmission_file_maxsizebytes=-1
--assignsubmission_file_filetypes[filetypes]=.html
"""

cmd_end = """
echo "UPDATE mdl_assign SET intro=REPLACE(intro, '&#13;', '\\n'), activity=REPLACE(activity, '&#13;', '\\n');" | moosh sql-cli
"""

md_start = """\
# Introduction to Web Development

[TOC]

---

## HTML Template

Right click on the following link and click on "save as": <a href="template.html" download>HTML Template</a>. This file will be used in all the following practicals.

---
"""

html_doc_tpl = """\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Introduction to Web Development</title>
</head>
<body>
    {}
</body>
</html>
"""


def md_to_html(text):
    return markdown.markdown(
        text, extensions=["fenced_code", TocExtension(toc_depth="2-3")]
    )


def md_to_html_oneline(text):
    # Required for the script (cmd) output, as moosh doesn't parse newlines.
    # These HTML entities will be replaced at the end of the script running a SQL query.
    return md_to_html(text).replace("\n", "&#13;")


class Output:
    def __init__(self, md="", html="", cmd=""):
        self.md = md
        self.html = html
        self.cmd = cmd


def compile(unit, **kwargs):
    with open(f"units/{unit}.yml") as f:
        document = yaml.load(f, Loader=yaml.FullLoader)

    instructions = document.get("instructions", "")
    instructions_html = md_to_html_oneline(instructions)

    doc_context = {
        "unit": unit,
        "instructions": instructions,
        "instructions_html": instructions_html,
    }
    doc_context.update(kwargs)
    doc_context.update({key: str(val) for key, val in document.items()})

    md_content = "## {title}\n\n".format(**doc_context)
    cmd_content = ""
    for i, activity in enumerate(document["activities"]):
        assert sum(activity["rubric"].values()) == 10
        nactivity = i + 1
        grading = "\n".join(
            f"- {key}: {value} points\n" for key, value in activity["rubric"].items()
        )
        resources = "\n".join(
            f"- [{key}]({value})\n" for key, value in activity["resources"].items()
        )
        intro = (
            ""
            + "#### Introduction\n"
            + activity["introduction"]
            + "#### Steps\n"
            + document.get("pre_steps", "")
            + activity["steps"]
            + document.get("post_steps", "")
            + "#### Challenge\n"
            + activity["challenge"]
            + "#### Grading criteria\n"
            + grading
            + "#### Additional resources\n"
            + resources
        )

        context = doc_context.copy()
        context.update(
            {
                "nactivity": f"{nactivity}",
                "idnumber": f"{unit}{nactivity}",
            }
        )
        context.update({key: str(val) for key, val in activity.items()})
        context.update(
            {
                "intro": intro,
                "intro_html": md_to_html_oneline(intro),
                "name": document.get("name_prefix", "") + activity["name"],
            }
        )

        context["options"] = cmd_tpl_options.format(**context)

        # Interpolate variables
        for key, value in context.items():
            interpolated = Template(value).safe_substitute(**context)
            context[key] = interpolated

        sh_context = {}
        for key, value in context.items():
            sh_context[key] = shlex.quote(value)

        md_content += "### {name}\n\n{intro}\n\n#### Submission\n{instructions}".format(
            **context
        )
        cmd_content += cmd_tpl.format(**sh_context)
    return Output(md=md_content, cmd=cmd_content)


def main(args):
    options = vars(args)
    out = Output()
    out.md = md_start.format(**options)
    out.cmd = cmd_start.format(**options)
    for unit in args.units.split(","):
        unit_out = compile(unit, **options)
        out.md += unit_out.md + "\n---\n"
        out.cmd += unit_out.cmd
    out.html = html_doc_tpl.format(md_to_html(out.md))
    out.cmd += cmd_end.format(**options)

    with open("activities.md", "w") as f:
        f.write(out.md)
    with open("activities.html", "w") as f:
        f.write(out.html)
    with open("activities.sh", "w") as f:
        f.write(out.cmd)


parser = argparse.ArgumentParser(
    prog="activitygen", formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument(
    "units",
    nargs="?",
    default=",".join(UNITS),
    help="Units to be generated",
)
parser.add_argument(
    "-c",
    "--courseid",
    default="2",
    help="Moodle course ID",
)
parser.add_argument(
    "-s",
    "--section",
    default="1",
    help="Moodle section",
)
parser.add_argument(
    "-f",
    "--format",
    choices=FORMATS.keys(),
    default="html",
    help="Moodle format",
)
parser.add_argument(
    "-m",
    "--moosh",
    default="moosh",
    help="Moosh path",
)

if __name__ == "__main__":
    args = parser.parse_args()
    if args.format != "html":
        print("Format generator not implemented")
    main(args)
