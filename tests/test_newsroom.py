import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("newsroom_build", ROOT / "newsroom" / "build.py")
newsroom = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = newsroom  # dataclasses look the module up by name
spec.loader.exec_module(newsroom)


def test_shortcodes_render_inside_markdown():
    body = newsroom.render_body(
        "Intro *text*.\n\n"
        '{{ chart src="charts/a.js" data="data/a.csv" title="T" source="S" }}\n\n'
        '{{ datawrapper id="aBc12" title="DW" }}\n\n'
        '{{ signal value="$24M" label="given" }}\n'
    )
    assert "<em>text</em>" in body
    assert 'data-chart="charts/a.js"' in body and 'data-data="data/a.csv"' in body
    assert "datawrapper.dwcdn.net/aBc12/" in body
    assert 'class="signal-value">$24M<' in body
    assert "<p><figure" not in body and "SIGNALBLOCK" not in body


def test_unknown_shortcode_is_an_error():
    with pytest.raises(ValueError, match="unknown shortcode"):
        newsroom.render_body('{{ chrt src="a.js" }}')


def test_attribute_values_are_escaped():
    body = newsroom.render_body('{{ chart src="a.js" alt="<script>" }}')
    assert "<script>" not in body


def test_build_hides_drafts_but_lists_them(tmp_path, monkeypatch):
    stories = tmp_path / "stories"
    for slug, status, date in [("old", "published", "2026-01-01"), ("new", "draft", "2026-02-01")]:
        folder = stories / slug
        (folder / "data").mkdir(parents=True)
        (folder / "data" / "x.csv").write_text("a\n1\n")
        (folder / "post.md").write_text("private")
        (folder / "story.md").write_text(f"Body of {slug}.")
        (folder / "story.toml").write_text(
            f'title = "Title {slug}"\ndek = "Dek"\ndate = {date}\n'
            f'section = "Test"\nstatus = "{status}"\n'
        )
    monkeypatch.setattr(newsroom, "STORIES", stories)
    out = tmp_path / "_site"

    shown = newsroom.build(out)

    assert [s.slug for s in shown] == ["old"]
    assert (out / "stories/old/index.html").exists()
    assert (out / "stories/old/data/x.csv").exists()
    assert not (out / "stories/old/post.md").exists()
    assert not (out / "stories/new").exists()
    front = (out / "index.html").read_text()
    assert "In the newsroom" in front and "Title new" in front
    assert "No. 1" in (out / "stories/old/index.html").read_text()
    assert "Title new" not in (out / "feed.xml").read_text()
    assert (out / "style/index.html").exists()

    newsroom.build(out, drafts=True)
    assert (out / "stories/new/index.html").exists()


def test_new_story_copies_template(tmp_path, monkeypatch):
    monkeypatch.setattr(newsroom, "STORIES", tmp_path / "stories")
    monkeypatch.setattr(newsroom, "ROOT", tmp_path)
    import datetime as dt

    day = dt.date(2026, 11, 17)
    target = newsroom.new_story("autumn-trains", 'Is "autumn" worst?', "Trains", day)
    meta = newsroom.tomllib.loads((target / "story.toml").read_text())
    assert meta["title"] == 'Is "autumn" worst?'
    assert meta["section"] == "Trains"
    assert meta["date"] == dt.date(2026, 11, 17)
    assert meta["status"] == "draft"
    assert meta["analysis"] == "analysis/autumn-trains"
    prepare = (tmp_path / "analysis/autumn-trains/prepare.py").read_text()
    assert "stories/autumn-trains/data" in prepare
    with pytest.raises(ValueError):
        newsroom.new_story("Bad Slug", "t", "s")


def test_analytics_only_when_configured():
    assert newsroom.analytics({}) == ""
    tag = newsroom.analytics({"goatcounter": "unexpected-signals"})
    assert "unexpected-signals.goatcounter.com/count" in tag
