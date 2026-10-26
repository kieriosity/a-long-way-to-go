#!/usr/bin/env python3
"""Builds the Long Way to Go site: the home page, a page per year and a page
for every strip, all sharing the same header and navigation.

    python tools/build.py

The output is plain static HTML with relative links, so it works on GitHub
Pages (including under a project subpath) and when opened straight from disk.

To add strips, put the images in a folder, add the week to WEEKS and rerun.
Needs Pillow (`pip install pillow`) to read image sizes and make thumbnails.
"""

from __future__ import annotations

import posixpath
from dataclasses import dataclass, field
from datetime import date, timedelta
from html import escape
from pathlib import Path
from urllib.parse import quote

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
BANNER = "2002/January/A long way to go banner.rev1.jpg"
THUMBS = "assets/thumbs"
THUMB_SIZE = 480
DESCRIPTION = "Long Way to Go, a comic strip by Andy Hartmann: the 1998 daily strips and a week from 2002."

# Every week in reading order: year, month, label, folder, and the date of the
# week's Sunday for weeks whose files are dated (Monday_01-14-2002.gif).
# Undated weeks name files by weekday (monday.gif; Wednesday is "wednsday").
# Sundays are .jpg, other days .gif. A day with no image is left out.
WEEKS = [
    ("1998", "January", "Week 3", "1998/JAN/Week3", None),
    ("1998", "January", "Week 4", "1998/JAN/Week 4", None),
    ("1998", "February", "Week 1", "1998/FEB/Week 1", None),
    ("1998", "February", "Week 2", "1998/FEB/Week 2", None),
    ("1998", "February", "Week 3", "1998/FEB/Week 3", None),
    ("1998", "February", "Week 4", "1998/FEB/Week 4", None),
    ("1998", "March", "Week 1", "1998/MAR/Week 1", None),
    ("1998", "March", "Week 2", "1998/MAR/Week 2", None),
    ("1998", "March", "Week 3", "1998/MAR/Week 3", None),
    ("1998", "March", "Week 4", "1998/MAR/Week 4", None),
    ("1998", "April", "Week 1", "1998/APR/Week 1", None),
    ("1998", "April", "Week 2", "1998/APR/Week 2", None),
    ("2002", "January", "January 13–19", "2002/January", date(2002, 1, 13)),
]


@dataclass
class Week:
    year: str
    month: str
    label: str
    folder: str
    sunday: date | None
    strips: list[Strip] = field(default_factory=list)

    @property
    def slug(self):
        return slugify(self.folder)

    @property
    def month_id(self):
        return slugify(f"{self.year} {self.month}")


@dataclass
class Strip:
    number: int
    week: Week
    day: str
    date: date | None
    page: str
    image: str
    width: int
    height: int
    prev: Strip | None = None
    next: Strip | None = None

    @property
    def when(self):
        """'January 13, 2002', or 'January 1998 · Week 3' for undated strips."""
        if self.date:
            return f"{self.date:%B} {self.date.day}, {self.date.year}"
        return f"{self.week.month} {self.week.year} · {self.week.label}"


def slugify(text):
    return "-".join("".join(c if c.isalnum() else " " for c in text.lower()).split())


def url(here, target):
    """Relative, URL-encoded link from the page at `here` to another site file."""
    return quote(posixpath.relpath("/" + target, "/" + posixpath.dirname(here)))


def image_size(path):
    with Image.open(ROOT / path) as im:
        return im.size


def load():
    weeks, strips = [], []
    for year, month, label, folder, sunday in WEEKS:
        week = Week(year, month, label, folder, sunday)
        for offset, day in enumerate(DAYS):
            when = sunday + timedelta(days=offset) if sunday else None
            if when:
                stem = f"{day}_{when:%m-%d-%Y}"
            else:
                stem = "wednsday" if day == "Wednesday" else day.lower()
            image = f"{folder}/{stem}.{'jpg' if day == 'Sunday' else 'gif'}"
            if not (ROOT / image).exists():
                continue
            strip = Strip(len(strips) + 1, week, day, when, f"{folder}/{stem}.html", image, *image_size(image))
            week.strips.append(strip)
            strips.append(strip)
        weeks.append(week)
    for a, b in zip(strips, strips[1:]):
        a.next, b.prev = b, a
    return weeks, strips


def thumbnail(week):
    """A small JPEG of the week's first strip, for its card in the archive."""
    dest = f"{THUMBS}/{week.slug}.jpg"
    if not (ROOT / dest).exists():
        (ROOT / THUMBS).mkdir(parents=True, exist_ok=True)
        with Image.open(ROOT / week.strips[0].image) as im:
            im = im.convert("RGB")
            im.thumbnail((THUMB_SIZE, THUMB_SIZE))
            im.save(ROOT / dest, "JPEG", quality=72, optimize=True, progressive=True)
    return dest


def layout(here, title, body, *, latest, section=None, head=""):
    """Wraps a page body in the shared head, masthead and footer."""
    def nav_link(target, text, key):
        current = ' aria-current="true"' if key == section else ""
        return f'<a href="{target}"{current}>{text}</a>'

    nav = "".join([
        nav_link(url(here, "index.html") + "#archive", "Archive", "archive"),
        nav_link(url(here, "1998/index.html"), "1998", "1998"),
        nav_link(url(here, "2002/index.html"), "2002", "2002"),
        nav_link(url(here, latest.page), "Latest", "latest"),
    ])
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)}</title>
<meta name="description" content="{escape(DESCRIPTION)}">
<meta name="author" content="Philip Maynard">
<meta name="theme-color" content="#f3eee3" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#171614" media="(prefers-color-scheme: dark)">
<link rel="icon" href="{url(here, 'assets/favicon.svg')}" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bangers&family=Libre+Franklin:wght@400;700;800&display=swap">
<link rel="stylesheet" href="{url(here, 'assets/site.css')}">
{head}</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="masthead">
  <div class="wrap">
    <a class="logo display" href="{url(here, 'index.html')}">Long Way to Go</a>
    <nav class="site-nav" aria-label="Site">{nav}</nav>
  </div>
</header>
<main id="main" class="wrap">
{body}
</main>
<footer class="footer">
  <div class="wrap">
    <p><strong>Long Way to Go</strong> by Andy Hartmann. Strips © Andrew H. Hartmann.</p>
    <p><a href="#main">Back to top ↑</a></p>
  </div>
</footer>
</body>
</html>
"""


def day_links(week, here, current=None, short=False):
    """Sunday-to-Saturday links for one week; days without a strip are greyed out."""
    by_day = {s.day: s for s in week.strips}
    items = []
    for day in DAYS:
        text = day[:2] if short else day[:3]
        strip = by_day.get(day)
        if strip is None:
            items.append(f'<span class="day missing" title="No {day} strip">{text}</span>')
        else:
            mark = ' aria-current="page"' if strip is current else ""
            items.append(f'<a class="day" href="{url(here, strip.page)}" title="{day}" aria-label="{day}"{mark}>{text}</a>')
    label = f"{week.month} {week.year}, {week.label}"
    return f'<nav class="days" aria-label="{escape(label)}">{"".join(items)}</nav>'


def week_card(week, here, level):
    first = week.strips[0]
    thumb = thumbnail(week)
    width, height = image_size(thumb)
    count = len(week.strips)
    return f"""<article class="week-card" id="{week.slug}">
  <a class="thumb" href="{url(here, first.page)}" tabindex="-1" aria-hidden="true"><img src="{url(here, thumb)}" width="{width}" height="{height}" alt="" loading="lazy" decoding="async"></a>
  <div class="week-card-body">
    <h{level} class="week-title display"><a href="{url(here, first.page)}">{escape(week.label)}</a></h{level}>
    <p class="meta">{count} strip{"s" if count != 1 else ""}</p>
    {day_links(week, here, short=True)}
  </div>
</article>"""


def months(weeks, here, level):
    """A year's weeks as cards, grouped under month headings at `level`."""
    sections = []
    for month in dict.fromkeys(w.month for w in weeks):
        in_month = [w for w in weeks if w.month == month]
        cards = "\n".join(week_card(w, here, level + 1) for w in in_month)
        sections.append(f"""<section class="month" id="{in_month[0].month_id}">
<h{level} class="month-name">{month}</h{level}>
<div class="cards">
{cards}
</div>
</section>""")
    return "\n".join(sections)


def year_summary(weeks):
    count = sum(len(w.strips) for w in weeks)
    names = list(dict.fromkeys(w.month for w in weeks))
    span = names[0] if len(names) == 1 else f"{names[0]}–{names[-1]}"
    return f"{count} strips · {span} {weeks[0].year}"


def by_year(weeks):
    years = {}
    for week in weeks:
        years.setdefault(week.year, []).append(week)
    return years


def strip_figure(strip, here, href, alt):
    return f"""<figure class="strip">
  <a href="{href}"><img src="{url(here, strip.image)}" width="{strip.width}" height="{strip.height}" alt="{escape(alt)}"></a>
</figure>"""


def alt_text(strip):
    return f"Long Way to Go comic strip for {strip.day}, {strip.when.replace(' · ', ', ')}"


def home_page(weeks, strips):
    here = "index.html"
    first, latest = strips[0], strips[-1]
    banner_w, banner_h = image_size(BANNER)
    archive = "\n".join(f"""<section class="year" id="y{year}">
<div class="year-head">
<h3 class="display"><a href="{url(here, f'{year}/index.html')}">{year}</a></h3>
<p>{year_summary(ws)}</p>
</div>
{months(ws, here, 4)}
</section>""" for year, ws in by_year(weeks).items())

    body = f"""<section class="hero">
  <div>
    <p class="kicker">A comic strip by Andy Hartmann</p>
    <h1 class="display">Long Way to Go</h1>
    <p class="lede">The daily strip from its 1998 run, January through April, plus a week of strips from January 2002. {len(strips)} strips in all.</p>
    <div class="actions">
      <a class="btn btn-primary" href="{url(here, first.page)}">Start from the beginning</a>
      <a class="btn" href="{url(here, latest.page)}">Read the latest strip</a>
    </div>
  </div>
  <figure class="hero-art">
    <img src="{url(here, BANNER)}" width="{banner_w}" height="{banner_h}" alt="A man looks at his reflection in a mirror, thinking: Still a long way to go…">
  </figure>
</section>

<section aria-labelledby="latest">
  <div class="section-head">
    <h2 class="display" id="latest">Latest strip</h2>
    <p>{latest.day}, {latest.when}</p>
  </div>
  {strip_figure(latest, here, url(here, latest.page), alt_text(latest))}
</section>

<section id="archive" aria-labelledby="archive-title">
  <div class="section-head">
    <h2 class="display" id="archive-title">Archive</h2>
    <p>Pick a week, or jump straight to a day.</p>
  </div>
{archive}
</section>"""
    return layout(here, "Long Way to Go · A comic strip by Andy Hartmann", body, latest=latest)


def year_page(year, weeks, latest):
    here = f"{year}/index.html"
    first = weeks[0].strips[0]
    body = f"""<nav class="crumbs" aria-label="Breadcrumb"><ol>
  <li><a href="{url(here, 'index.html')}#archive">Archive</a></li>
  <li aria-current="page">{year}</li>
</ol></nav>
<header class="page-head">
  <div>
    <p class="kicker">Long Way to Go</p>
    <h1 class="display">{year}</h1>
    <p class="lede">{year_summary(weeks)}</p>
  </div>
  <a class="btn btn-primary" href="{url(here, first.page)}">Start reading {year}</a>
</header>
{months(weeks, here, 2)}"""
    return layout(here, f"{year} · Long Way to Go", body, latest=latest, section=year)


def strip_page(strip, strips):
    here = strip.page
    week = strip.week
    first, latest = strips[0], strips[-1]
    year_index = f"{week.year}/index.html"

    def button(target, text, rel=None):
        if target is None or target is strip:
            return f'<span class="btn" aria-disabled="true">{text}</span>'
        rel_attr = f' rel="{rel}"' if rel else ""
        return f'<a class="btn" href="{url(here, target.page)}"{rel_attr}>{text}</a>'

    head = ""
    if strip.prev:
        head += f'<link rel="prev" href="{url(here, strip.prev.page)}">\n'
    if strip.next:
        head += f'<link rel="next" href="{url(here, strip.next.page)}">\n'
        head += f'<link rel="prefetch" href="{url(here, strip.next.image)}">\n'
    head += f'<script src="{url(here, "assets/site.js")}" defer></script>\n'

    body = f"""<nav class="crumbs" aria-label="Breadcrumb"><ol>
  <li><a href="{url(here, 'index.html')}#archive">Archive</a></li>
  <li><a href="{url(here, year_index)}">{week.year}</a></li>
  <li><a href="{url(here, year_index)}#{week.month_id}">{week.month}</a></li>
  <li><a href="{url(here, year_index)}#{week.slug}">{escape(week.label)}</a></li>
</ol></nav>
<header class="strip-head">
  <div>
    <p class="kicker">{escape(strip.when)}</p>
    <h1 class="display">{strip.day}</h1>
  </div>
  <p class="counter">Strip {strip.number} of {len(strips)}</p>
</header>
<div class="toolbar">
  {day_links(week, here, current=strip)}
  <div class="step">{button(strip.prev, "‹ Previous", "prev")}{button(strip.next, "Next ›", "next")}</div>
</div>
{strip_figure(strip, here, url(here, strip.image), alt_text(strip))}
<nav class="pager" aria-label="Strips">
  <div>{button(first, '« <span class="label">First</span>')}{button(strip.prev, "‹ Previous", "prev")}</div>
  <div>{button(strip.next, "Next ›", "next")}{button(latest, '<span class="label">Latest</span> »')}</div>
</nav>
<p class="hint">Tip: the <kbd>←</kbd> and <kbd>→</kbd> keys flip through the strips. Click a strip to see it full size.</p>"""
    title = f"{strip.day}, {strip.when.replace(' · ', ', ')} · Long Way to Go"
    section = "latest" if strip is latest else week.year
    return layout(here, title, body, latest=latest, section=section, head=head)


def write(path, html):
    (ROOT / path).write_text(html, encoding="utf-8", newline="\n")


def main():
    weeks, strips = load()
    latest = strips[-1]
    write("index.html", home_page(weeks, strips))
    for year, ws in by_year(weeks).items():
        write(f"{year}/index.html", year_page(year, ws, latest))
    for strip in strips:
        write(strip.page, strip_page(strip, strips))
    print(f"Built {len(strips)} strip pages across {len(weeks)} weeks.")


if __name__ == "__main__":
    main()
