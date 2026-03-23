"""
chatself CLI — analyze your WhatsApp history from the terminal.
"""

import json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()


@click.group()
@click.version_option("0.1.0", prog_name="chatself")
def main():
    """🪞 chatself — know yourself through your conversations."""


@main.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--name", "-n", prompt="Your name in the chat", help="Your display name as it appears in the export.")
@click.option("--output", "-o", type=click.Path(), default=None, help="Save JSON report to file.")
@click.option("--html", "html_output", type=click.Path(), default=None, help="Save HTML dashboard to file.")
@click.option("--lang", default="es", show_default=True, type=click.Choice(["es", "en"]), help="Language for affection analysis.")
@click.option("--ai", "ai_provider", default=None, type=click.Choice(["openai", "anthropic"]), help="Start an AI conversation after analysis (requires API key in env).")
@click.option("--model", default=None, help="Override the AI model (e.g. gpt-4o, claude-opus-4-5).")
def analyze(path: str, name: str, output: str | None, html_output: str | None, lang: str, ai_provider: str | None, model: str | None):
    """Analyze a WhatsApp .txt export or folder of exports."""
    from chatself.parsers.txt_parser import TxtParser
    from chatself.analytics.patterns import PatternAnalyzer
    from chatself.analytics.vocabulary import VocabularyAnalyzer
    from chatself.analytics.relationships import RelationshipAnalyzer

    p = Path(path)
    parser = TxtParser()

    if p.is_dir():
        chats = parser.parse_directory(p)
        console.print(f"[green]Loaded {len(chats)} chats from {p}[/green]")
        _print_multi_chat_summary(chats, name)
        if output:
            _save_json([{"chat": c.name, "messages": len(c.messages)} for c in chats], output)
        return

    # Single chat
    chat = parser.parse_file(p)
    console.print(f"\n[bold cyan]Chat: {chat.name}[/bold cyan]")
    console.print(f"Participants: {', '.join(chat.participants)}")

    patterns  = PatternAnalyzer(chat, name)
    vocab     = VocabularyAnalyzer(chat, name)
    relations = RelationshipAnalyzer(chat, name, lang=lang)

    _print_patterns(patterns)
    _print_vocabulary(vocab)
    _print_relationships(relations)

    if output:
        report = {
            "chat": chat.name,
            "patterns": patterns.summary(),
            "vocabulary": vocab.summary(),
            "relationships": relations.summary(),
        }
        _save_json(report, output)
        console.print(f"\n[green]JSON saved to {output}[/green]")

    if html_output:
        from chatself.report.builder import ReportBuilder
        out_path = ReportBuilder(chat, name, lang).save(html_output)
        console.print(f"[green]HTML dashboard saved to {out_path}[/green]")
        console.print(f"[dim]Open in browser: file:///{out_path.resolve()}[/dim]")


    if ai_provider:
        _run_ai_session(chat, name, patterns, vocab, relations, ai_provider, model)


def _run_ai_session(chat, my_name, patterns, vocab, relations, provider, model):
    from chatself.ai.context import build_context
    from chatself.ai.session import AISession
    from chatself.analytics.emojis import EmojiAnalyzer

    emojis = EmojiAnalyzer(chat, my_name)
    context = build_context(chat.name, my_name, patterns, vocab, relations, emojis)

    try:
        session = AISession(context, provider=provider, model=model)
    except Exception as e:
        console.print(f"\n[red]Could not start AI session: {e}[/red]")
        if provider == 'openai':
            console.print("[dim]  pip install openai && set OPENAI_API_KEY=sk-...[/dim]")
        else:
            console.print("[dim]  pip install anthropic && set ANTHROPIC_API_KEY=sk-ant-...[/dim]")
        return

    console.print(Panel(
        f"[bold green]AI session started[/bold green] · provider: [cyan]{provider}[/cyan] · model: [cyan]{session.model}[/cyan]\n"
        f"[dim]Raw messages are NOT sent. Only pre-computed stats.[/dim]\n"
        f"[dim]Type [bold]exit[/bold] to stop. [bold]reset[/bold] to clear history.[/dim]",
        title="🤖 chatself AI",
    ))

    while True:
        try:
            user_input = console.input("\n[bold cyan]You:[/bold cyan] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Session ended.[/dim]")
            break

        if not user_input:
            continue
        if user_input.lower() in ('exit', 'quit', 'q'):
            console.print("[dim]Goodbye.[/dim]")
            break
        if user_input.lower() == 'reset':
            session.reset()
            console.print("[dim]History cleared.[/dim]")
            continue

        console.print("\n[bold green]AI:[/bold green] ", end="")
        try:
            for chunk in session.stream(user_input):
                console.print(chunk, end="", highlight=False)
            console.print()
        except Exception as e:
            console.print(f"\n[red]Error: {e}[/red]")


@main.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--name", "-n", prompt="Your name", help="Your display name.")
def timeline(path: str, name: str):
    """Show your personal evolution year by year across all chats."""
    from chatself.parsers.txt_parser import TxtParser
    from chatself.analytics.timeline import TimelineAnalyzer

    p = Path(path)
    parser = TxtParser()
    chats = parser.parse_directory(p) if p.is_dir() else [parser.parse_file(p)]

    analyzer = TimelineAnalyzer(chats, name)
    data = analyzer.year_by_year()

    table = Table(title="Your Evolution by Year", box=box.ROUNDED)
    table.add_column("Year", style="cyan")
    table.add_column("Messages", justify="right")
    table.add_column("Avg Length", justify="right")
    table.add_column("Vocab Size", justify="right")
    table.add_column("Peak Hour", justify="right")
    table.add_column("Top Words")

    for row in data:
        table.add_row(
            row["year"],
            str(row["messages_sent"]),
            str(row["avg_length"]),
            str(row["vocabulary_size"]),
            f"{row['peak_hour']}h" if row["peak_hour"] is not None else "-",
            ", ".join(row["top_words"][:5]),
        )

    console.print(table)


def _print_patterns(p: "PatternAnalyzer"):
    summary = p.summary()
    table = Table(title="📊 Communication Patterns", box=box.SIMPLE)
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    table.add_row("Total messages", str(summary["total_messages"]))
    table.add_row("Your messages", str(summary["my_messages"]))
    table.add_row("Their messages", str(summary["their_messages"]))
    table.add_row("Message ratio (you/them)", str(summary["message_ratio"]))
    table.add_row("Peak activity hour", f"{summary['peak_hour']}h")
    for sender, rt in summary["response_times"].items():
        table.add_row(f"Response median ({sender})", f"{rt['median_min']} min")
    console.print(table)


def _print_vocabulary(v: "VocabularyAnalyzer"):
    summary = v.summary()
    console.print(Panel(
        f"Messages sent: [bold]{summary['total_sent']}[/bold]  "
        f"Avg length: [bold]{summary['avg_length']} chars[/bold]  "
        f"Vocabulary: [bold]{summary['vocabulary_size']} words[/bold]",
        title="📝 Your Vocabulary",
    ))
    tics = summary["verbal_tics"][:10]
    if tics:
        table = Table(title="Your Verbal Tics", box=box.SIMPLE)
        table.add_column("Phrase")
        table.add_column("Count", justify="right")
        for phrase, count in tics:
            table.add_row(phrase, str(count))
        console.print(table)


def _print_relationships(r: "RelationshipAnalyzer"):
    aff = r.affection_score()
    me_pct  = aff.get("me", {}).get("pct", 0)
    them_pct = aff.get("them", {}).get("pct", 0)
    console.print(Panel(
        f"Your affection markers: [bold]{me_pct}%[/bold] of your messages\n"
        f"Their affection markers: [bold]{them_pct}%[/bold] of their messages",
        title="❤️ Emotional Tone",
    ))
    gaps = r.silence_gaps()[:3]
    if gaps:
        console.print("\n[yellow]Longest silences:[/yellow]")
        for g in gaps:
            console.print(f"  {g['from']} → {g['to']}  ({g['days']} days)  resumed by: {g['resumed_by']}")


def _print_multi_chat_summary(chats, name: str):
    table = Table(title=f"📱 All chats — {len(chats)} conversations", box=box.ROUNDED)
    table.add_column("Chat", max_width=40)
    table.add_column("Messages", justify="right")
    table.add_column("First", justify="right")
    table.add_column("Last", justify="right")
    for chat in sorted(chats, key=lambda c: len(c.messages), reverse=True)[:20]:
        dr = chat.date_range
        table.add_row(
            chat.name,
            str(chat.message_count),
            dr[0].strftime("%Y-%m-%d") if dr else "-",
            dr[1].strftime("%Y-%m-%d") if dr else "-",
        )
    console.print(table)


def _save_json(data, path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
