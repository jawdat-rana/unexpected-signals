"""Build the Unexpected Signals site from the stories in this repo.

Every folder in ``stories/`` is one piece: a ``story.toml`` with its metadata, a
``story.md`` with the text, and optional ``charts/``, ``data/`` and image files.
This script turns them into a static site in ``_site/``, ready for GitHub Pages.

    python newsroom/build.py new my-slug --title "Is autumn the worst month for trains?"
    python newsroom/build.py build            # published stories only, like the live site
    python newsroom/build.py build --drafts   # include drafts, for previewing
    python newsroom/build.py serve            # build with drafts and serve on localhost:8000

Needs Python 3.11+ and the ``markdown`` package (``pip install -e ".[site]"``).
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import http.server
import re
import shlex
import shutil
import tomllib
from dataclasses import dataclass, field
from email.utils import format_datetime
from pathlib import Path
from string import Template

import markdown

ROOT = Path(__file__).resolve().parent.parent
NEWSROOM = ROOT / "newsroom"
STORIES = ROOT / "stories"
TEMPLATES = ROOT / "templates"
OUT = ROOT / "_site"

# Files in a story folder that are sources, not part of the published page.
PRIVATE = {"story.toml", "story.md", "post.md", "README.md"}
STATUSES = {"draft", "published"}
WORDS_PER_MINUTE = 230


@dataclass
class Story:
    slug: str
    folder: Path
    title: str
    dek: str
    date: dt.date
    section: str
    status: str
    body_md: str
    tags: list[str] = field(default_factory=list)
    image: str = ""
    analysis: str = ""
    sources: list[dict[str, str]] = field(default_factory=list)
    series: str = ""
    issue: int = 0
    url: str = ""

    @property
    def minutes(self) -> int:
        words = len(re.findall(r"\w+", re.sub(r"\{\{.*?\}\}", "", self.body_md)))
        return max(1, round(words / WORDS_PER_MINUTE))


def load_story(folder: Path, url: str | None = None) -> Story:
    meta = tomllib.loads((folder / "story.toml").read_text(encoding="utf-8"))
    missing = [key for key in ("title", "dek", "date", "section", "status") if key not in meta]
    if missing:
        raise ValueError(f"{folder}/story.toml is missing {', '.join(missing)}")
    if meta["status"] not in STATUSES:
        raise ValueError(f"{folder}/story.toml: status must be one of {sorted(STATUSES)}")
    date = meta["date"]
    if not isinstance(date, dt.date):
        raise ValueError(f"{folder}/story.toml: date must be a TOML date, like 2026-11-17")
    return Story(
        slug=folder.name,
        folder=folder,
        title=meta["title"],
        dek=meta["dek"],
        date=date,
        section=meta["section"],
        status=meta["status"],
        body_md=(folder / "story.md").read_text(encoding="utf-8"),
        tags=meta.get("tags", []),
        image=meta.get("image", ""),
        analysis=meta.get("analysis", ""),
        sources=meta.get("sources", []),
        series=meta.get("series", ""),
        url=url or f"stories/{folder.name}/",
    )


def load_stories() -> list[Story]:
    stories = [
        load_story(folder)
        for folder in sorted(STORIES.iterdir() if STORIES.exists() else [])
        if folder.is_dir() and (folder / "story.toml").exists()
    ]
    # Issue numbers count published stories in date order, like a paper's issues.
    published = sorted((s for s in stories if s.status == "published"), key=lambda s: s.date)
    for number, story in enumerate(published, start=1):
        story.issue = number
    return sorted(stories, key=lambda s: s.date, reverse=True)


# --- Shortcodes ---------------------------------------------------------------
#
# A shortcode sits on its own line in story.md:
#
#   {{ chart src="charts/bars.js" data="data/pacs.csv" title="..." source="FEC" }}
#   {{ datawrapper id="aBc12" title="..." source="CBS" }}
#   {{ signal value="$24M" label="given by foreign-owned PACs in 2024" }}

SHORTCODE = re.compile(r"^\{\{\s*(\w+)(.*?)\}\}\s*$", re.MULTILINE)


def parse_attrs(text: str) -> dict[str, str]:
    attrs = {}
    for token in shlex.split(text):
        key, sep, value = token.partition("=")
        if not sep:
            raise ValueError(f"shortcode attribute {token!r} needs a value, like {token}=...")
        attrs[key] = value
    return attrs


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def inline_md(text: str) -> str:
    """Markdown for one line of figure text: links and emphasis, no <p> wrapper."""
    rendered = markdown.markdown(text, extensions=["smarty"])
    return re.sub(r"^<p>(.*)</p>$", r"\1", rendered, flags=re.DOTALL)


def figure(attrs: dict[str, str], inner: str) -> str:
    head = ""
    if attrs.get("title"):
        head += f'<h3 class="fig-title">{inline_md(attrs["title"])}</h3>'
    if attrs.get("subtitle"):
        head += f'<p class="fig-subtitle">{inline_md(attrs["subtitle"])}</p>'
    foot = []
    if attrs.get("source"):
        foot.append(f"Source: {inline_md(attrs['source'])}")
    if attrs.get("data"):
        foot.append(f'<a href="{esc(attrs["data"])}" download>Get the data</a>')
    if attrs.get("note"):
        foot.append(inline_md(attrs["note"]))
    size = esc(attrs.get("size", "wide"))
    caption = f"<figcaption>{' · '.join(foot)}</figcaption>" if foot else ""
    header = f"<header>{head}</header>" if head else ""
    return f'<figure class="fig fig-{size}">{header}{inner}{caption}</figure>'


def render_chart(attrs: dict[str, str]) -> str:
    if "src" not in attrs:
        raise ValueError("chart shortcode needs src=, the chart module, like charts/bars.js")
    data = f' data-data="{esc(attrs["data"])}"' if attrs.get("data") else ""
    alt = esc(attrs.get("alt", attrs.get("title", "Chart")))
    inner = (
        f'<div class="chart" data-chart="{esc(attrs["src"])}"{data} role="img" '
        f'aria-label="{alt}"><noscript>This chart needs JavaScript.</noscript></div>'
    )
    return figure(attrs, inner)


def render_datawrapper(attrs: dict[str, str]) -> str:
    if "id" not in attrs:
        raise ValueError("datawrapper shortcode needs id=, the chart id from its share link")
    chart_id = esc(attrs["id"])
    height = esc(attrs.get("height", "400"))
    title = esc(attrs.get("alt", attrs.get("title", "Datawrapper chart")))
    inner = (
        f'<iframe class="datawrapper" id="datawrapper-chart-{chart_id}" title="{title}" '
        f'src="https://datawrapper.dwcdn.net/{chart_id}/?dark=auto" scrolling="no" '
        f'frameborder="0" loading="lazy" data-external="1" '
        f'style="width:0;min-width:100%!important;border:none;height:{height}px"></iframe>'
    )
    return figure(attrs, inner)


def render_signal(attrs: dict[str, str]) -> str:
    return (
        '<aside class="signal-box">'
        f'<span class="signal-value">{esc(attrs.get("value", ""))}</span>'
        f'<span class="signal-label">{inline_md(attrs.get("label", ""))}</span>'
        "</aside>"
    )


RENDERERS = {"chart": render_chart, "datawrapper": render_datawrapper, "signal": render_signal}


def render_body(text: str) -> str:
    blocks: list[str] = []

    def stash(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in RENDERERS:
            raise ValueError(f"unknown shortcode {{{{ {name} }}}}; known: {sorted(RENDERERS)}")
        blocks.append(RENDERERS[name](parse_attrs(match.group(2))))
        return f"\n\nSIGNALBLOCK{len(blocks) - 1}END\n\n"

    body = markdown.markdown(
        SHORTCODE.sub(stash, text), extensions=["extra", "smarty", "sane_lists"]
    )
    return re.sub(r"<p>SIGNALBLOCK(\d+)END</p>", lambda m: blocks[int(m.group(1))], body)


# --- Pages --------------------------------------------------------------------


def template(name: str) -> Template:
    return Template((NEWSROOM / "templates" / name).read_text(encoding="utf-8"))


def long_date(day: dt.date) -> str:
    return f"{day.day} {day:%B %Y}"


def page(config: dict, *, root: str, title: str, description: str, body: str, path: str,
         image: str = "", kind: str = "website") -> str:  # fmt: skip
    base_url = config["base_url"].rstrip("/") + "/"
    image_url = base_url + (image or "assets/img/card.png")
    return template("base.html").substitute(
        root=root,
        title=esc(title),
        description=esc(description),
        canonical=esc(base_url + path),
        image=esc(image_url),
        og_type=kind,
        site_title=esc(config["title"]),
        tagline=esc(config["tagline"]),
        today=long_date(dt.date.today()),
        edition=esc(config.get("edition", "")),
        author=esc(config["author"]),
        repo=esc(config["repo"]),
        linkedin_link=(
            f'<a href="{esc(config["linkedin"])}">LinkedIn</a> · ' if config.get("linkedin") else ""
        ),
        analytics=analytics(config),
        body=body,
    )


def analytics(config: dict) -> str:
    """GoatCounter page counts, only when `goatcounter` is set in site.toml.

    GoatCounter sets no cookies and stores no personal data, so no consent
    banner is needed. Empty by default, so a fork tracks nothing.
    """
    code = config.get("goatcounter", "")
    if not code:
        return ""
    if not re.fullmatch(r"[a-z0-9-]+", code):
        raise ValueError("goatcounter must be the site code, like 'unexpected-signals'")
    return (
        f'<script data-goatcounter="https://{code}.goatcounter.com/count" '
        'async src="https://gc.zgo.at/count.js"></script>'
    )


def story_html(config: dict, story: Story, *, root: str) -> str:
    sources = "".join(
        f'<li><a href="{esc(s["url"])}">{esc(s["name"])}</a>'
        + (f' <span class="licence">{esc(s["licence"])}</span>' if s.get("licence") else "")
        + "</li>"
        for s in story.sources
    )
    repo = config["repo"].rstrip("/")
    code = (
        f'<li><a href="{esc(repo)}/tree/main/{esc(story.analysis)}">Analysis code</a></li>'
        if story.analysis
        else ""
    )
    src = story.folder.relative_to(ROOT).as_posix() if story.folder.is_relative_to(ROOT) else ""
    story_src = f'<li><a href="{esc(repo)}/tree/main/{esc(src)}">This page</a></li>' if src else ""
    issue = f"No. {story.issue}" if story.issue else {"draft": "Draft"}.get(story.status, "Guide")
    series = f'<span class="series">{esc(story.series)}</span>' if story.series else ""
    banner = (
        '<p class="draft-banner">Draft: not on the live site yet</p>'
        if story.status == "draft"
        else ""
    )
    return template("story.html").substitute(
        banner=banner,
        section=esc(story.section),
        series=series,
        title=inline_md(story.title),
        dek=inline_md(story.dek),
        author=esc(config["author"]),
        date_iso=story.date.isoformat(),
        date=long_date(story.date),
        minutes=story.minutes,
        issue=issue,
        body=render_body(story.body_md),
        sources=sources,
        code=code + story_src,
        root=root,
    )


def card(story: Story, *, root: str, lead: bool = False) -> str:
    cls = "card card-lead" if lead else "card"
    image = (
        f'<img src="{root}{story.url}{esc(story.image)}" alt="" loading="lazy">'
        if lead and story.image
        else ""
    )
    draft = ' <span class="tag-draft">Draft</span>' if story.status == "draft" else ""
    return (
        f'<article class="{cls}">{image}'
        f'<p class="kicker">{esc(story.section)}{draft}</p>'
        f'<h2><a href="{root}{story.url}">{inline_md(story.title)}</a></h2>'
        f'<p class="dek">{inline_md(story.dek)}</p>'
        f'<p class="meta"><time datetime="{story.date.isoformat()}">{long_date(story.date)}</time>'
        f" · {story.minutes} min read</p></article>"
    )


def front_html(config: dict, shown: list[Story], upcoming: list[Story]) -> str:
    root = ""
    if shown:
        lead, rest = shown[0], shown[1:]
        stories = card(lead, root=root, lead=True) + "".join(card(s, root=root) for s in rest)
    else:
        stories = (
            '<article class="card card-lead"><p class="kicker">Coming soon</p>'
            "<h2>The first signal is being checked.</h2>"
            '<p class="dek">New analyses appear here once or twice a week.</p></article>'
        )
    newsroom = ""
    if upcoming and config.get("show_upcoming", True):
        items = "".join(
            f"<li><span class=kicker>{esc(s.section)}</span> {inline_md(s.title)}</li>"
            for s in upcoming
        )
        newsroom = (
            '<aside class="newsroom"><h2 class="rule-label">In the newsroom</h2>'
            f"<ul>{items}</ul></aside>"
        )
    return template("front.html").substitute(
        stories=stories, newsroom=newsroom, about=inline_md(config["about"])
    )


def feed_xml(config: dict, stories: list[Story]) -> str:
    base_url = config["base_url"].rstrip("/") + "/"
    items = "".join(
        "<item>"
        f"<title>{esc(s.title)}</title>"
        f"<link>{base_url}{s.url}</link>"
        f"<guid>{base_url}{s.url}</guid>"
        f"<description>{esc(s.dek)}</description>"
        f"<pubDate>{format_datetime(dt.datetime(*s.date.timetuple()[:3], tzinfo=dt.UTC))}</pubDate>"
        "</item>"
        for s in stories
    )
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n<rss version="2.0"><channel>'
        f"<title>{esc(config['title'])}</title><link>{base_url}</link>"
        f"<description>{esc(config['tagline'])}</description>{items}</channel></rss>\n"
    )


def copy_assets(source: Path, target: Path) -> None:
    for path in source.rglob("*"):
        if path.is_file() and path.name not in PRIVATE and not path.name.startswith("."):
            dest = target / path.relative_to(source)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)


def build(out: Path = OUT, drafts: bool = False) -> list[Story]:
    config = tomllib.loads((NEWSROOM / "site.toml").read_text(encoding="utf-8"))
    stories = load_stories()
    shown = [s for s in stories if s.status == "published" or drafts]
    upcoming = [s for s in stories if s.status == "draft" and not drafts]

    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(NEWSROOM / "assets", out / "assets")
    (out / ".nojekyll").write_text("")

    def write(path: str, text: str) -> None:
        target = out / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    for story in shown:
        root = "../../"
        copy_assets(story.folder, out / story.url)
        image = story.url + story.image if story.image else ""
        body = story_html(config, story, root=root)
        title = f"{story.title} · {config['title']}"
        write(
            story.url + "index.html",
            page(
                config,
                root=root,
                title=title,
                description=story.dek,
                body=body,
                path=story.url,
                image=image,
                kind="article",
            ),  # fmt: skip
        )

    # The story template is also the style guide: it uses every component, so
    # building it proves the template works and shows what each piece looks like.
    template_story = load_story(TEMPLATES / "story", url="style/")
    template_story.status = "guide"
    copy_assets(template_story.folder, out / "style")
    write(
        "style/index.html",
        page(
            config,
            root="../",
            title=f"Style guide · {config['title']}",
            description="Every component a story can use.",
            body=story_html(config, template_story, root="../"),
            path="style/",
        ),  # fmt: skip
    )

    write(
        "index.html",
        page(
            config,
            root="",
            title=f"{config['title']}: {config['tagline']}",
            description=config["description"],
            body=front_html(config, shown, upcoming),
            path="",
        ),  # fmt: skip
    )
    write("feed.xml", feed_xml(config, [s for s in stories if s.status == "published"]))
    return shown


# --- New story ----------------------------------------------------------------


def new_story(slug: str, title: str, section: str, today: dt.date | None = None) -> Path:
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", slug):
        raise ValueError("slug must be lowercase words joined by dashes, like autumn-trains")
    target = STORIES / slug
    if target.exists():
        raise FileExistsError(f"{target} already exists")
    shutil.copytree(TEMPLATES / "story", target)
    meta = (target / "story.toml").read_text(encoding="utf-8")
    meta = re.sub(r'^title = ".*"$', f"title = {_toml_str(title)}", meta, flags=re.M)
    meta = re.sub(r'^section = ".*"$', f"section = {_toml_str(section)}", meta, flags=re.M)
    day = (today or dt.date.today()).isoformat()
    meta = re.sub(r"^date = .*$", f"date = {day}", meta, flags=re.M)
    meta = re.sub(r'^analysis = ".*"$', f'analysis = "analysis/{slug}"', meta, flags=re.M)
    (target / "story.toml").write_text(meta, encoding="utf-8")

    analysis = ROOT / "analysis" / slug
    if not analysis.exists():
        analysis.mkdir(parents=True)
        prepare = (TEMPLATES / "analysis" / "prepare.py").read_text(encoding="utf-8")
        (analysis / "prepare.py").write_text(prepare.replace("SLUG", slug), encoding="utf-8")
    return target


def _toml_str(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def serve(port: int) -> None:
    handler = lambda *a: http.server.SimpleHTTPRequestHandler(*a, directory=str(OUT))  # noqa: E731
    with http.server.ThreadingHTTPServer(("127.0.0.1", port), handler) as server:
        print(f"Serving {OUT} on http://localhost:{port}/ (Ctrl+C to stop)")
        server.serve_forever()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    b = commands.add_parser("build", help="build the site into _site/")
    b.add_argument("--drafts", action="store_true", help="include draft stories")
    s = commands.add_parser("serve", help="build with drafts and serve locally")
    s.add_argument("--port", type=int, default=8000)
    n = commands.add_parser("new", help="start a new story from the template")
    n.add_argument("slug", help="folder name and URL, like autumn-trains")
    n.add_argument("--title", default="Headline goes here")
    n.add_argument("--section", default="Signals")
    args = parser.parse_args(argv)

    if args.command == "new":
        target = new_story(args.slug, args.title, args.section)
        print(f"Created {target.relative_to(ROOT)} and analysis/{args.slug}/prepare.py")
    elif args.command == "build":
        shown = build(drafts=args.drafts)
        print(f"Built {len(shown)} stories into {OUT.relative_to(ROOT)}/")
    else:
        build(drafts=True)
        serve(args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
