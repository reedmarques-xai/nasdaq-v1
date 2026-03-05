"""HTML report generator using Jinja2 templates."""

from __future__ import annotations

import os
import webbrowser
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from rich.console import Console

from .models import MarketReport

console = Console()

# Resolve template directory relative to this file
_THIS_DIR = Path(__file__).resolve().parent
_TEMPLATE_DIR = _THIS_DIR.parent / "templates"


class ReportGenerator:
    """Renders a MarketReport into a self-contained HTML file."""

    def __init__(self, settings: dict) -> None:
        self.output_dir = Path(settings.get("output_dir", "output"))
        self.title = settings.get("title", "Market Signal Report")
        self.open_browser = settings.get("open_browser", True)

        self.env = Environment(
            loader=FileSystemLoader(str(_TEMPLATE_DIR)),
            autoescape=True,
        )

    def generate(self, report: MarketReport) -> Path:
        """Render the report and write it to disk.

        Returns the path to the generated HTML file.
        """
        template = self.env.get_template("report.html")

        # Prepare template context
        generated_at = report.generated_at.strftime("%Y-%m-%d %H:%M:%S")
        context = {
            "title": self.title,
            "generated_at": generated_at,
            "overview": report.overview,
            "signals": report.signals,
        }

        html = template.render(**context)

        # Write to output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"market_signals_{report.generated_at.strftime('%Y%m%d_%H%M%S')}.html"
        output_path = self.output_dir / filename

        output_path.write_text(html, encoding="utf-8")
        console.print(f"  📄 Report saved to [bold green]{output_path}[/bold green]")

        # Open in browser
        if self.open_browser:
            try:
                webbrowser.open(f"file://{output_path.resolve()}")
                console.print("  🌐 Opened report in browser")
            except Exception:
                console.print("  [yellow]Could not open browser automatically[/yellow]")

        return output_path
