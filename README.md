# `reportable` makes reports portable

## What does that even mean?

When you write a report using typesetting languages like LaTeX, Markdown or
Quarto, I sometimes find myself just wildly linking images and other files in
the report from a bunch of different directories or from directories that
include a bunch of other files that are not necessary for the report. So when I
want to share the report with someone else, I have to zip the whole directory,
including all the unnecessary files. If the directories containing the links
contain a lot of images or videos, this can be a huge file. So I thought, why
not just make a tool that copies all the necessary files to a new directory and
then links them from there. This is what `reportable` does.

Yes, it is essentially a crutch that fixes problems that arise because of my
bad habits.

## What does `reportable` do?

1. It parses the report file and finds all the files that are linked in the report.
2. It copies all the linked files to a new directory.
3. It changes the links in the report to point to the new directory.
4. It writes a new report file with the new links into the new directory.
5. It executes the needed commands to compile the report.

Voilà! You have a portable report. This is particularly useful when you give
presentations on conferences using Quarto.
