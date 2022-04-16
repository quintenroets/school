from datetime import datetime

from bs4 import BeautifulSoup

from school.utils.path import Path

from .contentmanager import Item

soup = BeautifulSoup(features="html.parser")


def write_output_to_html(sections):
    content = make_output(sections)
    output_file().text = content


def output_file():
    return (Path.assets / "output" / ".html").with_timestamp()


def make_output(sections):
    header = f'<link href="file:///{Path.templates}/output.css" rel="stylesheet"/>\n'
    sections_content = "\n".join(make_section_output(s) for s in sections)
    return header + "<main><h1>New items</h1><hr>" + sections_content + "</main>"


def make_section_output(section):
    path_str = get_path_string(section.titles)
    content_str = get_content_string(section.dest, section.items)
    dest_str = get_dest_string(section.dest)
    return path_str + content_str + dest_str


def get_path_string(path):
    path_string = "<b>" + path[0] + "</b>" if path else ""
    path_string += "".join(
        [f"<br>{' ' * 5 * i}&#x2B9E;{line}" for i, line in enumerate(path[1:])]
    )
    return "<pre>" + path_string + "</pre><br>"


def get_content_string(dest, content):
    return "".join(get_item_string(dest, item) for item in content)


def get_dest_string(folder: Path, title: str = "Open"):
    tag = OutputWriter.make_tag("a")
    tag.string = title
    tag["target"] = "_blanck"
    tag["href"] = folder.as_uri() if folder else ""

    return "<h4>" + str(tag) + "</h4><hr>"


def get_item_string(dest: Path, item: Item):
    attributes = {
        "style": "color: black;",
        "target": "_blanck",
        "href": item.dest.as_uri() if item.dest and item.dest.exists() else dest,
    }

    tag_item = OutputWriter.make_tag("a")
    tag_item.string = item.title

    for k, v in attributes.items():
        tag_item[k] = v
    return str(tag_item) + "<br>"


def make_tag(name):
    return soup.new_tag(name=name)
