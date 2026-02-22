from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.layout import Layout
from rich.text import Text
from rich import box
import requests, sys, time, json
from typing import Dict, Any, Optional
from datetime import datetime


console = Console()

API_BASE_URL = "http://127.0.0.1:8000"
API_ENDPOINT = f"{API_BASE_URL}/api/v1/analyze"

def call_the_api(video_url: str, max_comments: int = 100) -> Optional[Dict[str, Any]]:
    try:
        response = requests.post(
            API_ENDPOINT,
            json={
                "video_url": video_url,
                "max_comments": max_comments
            },
            timeout=60
        )
        if response.status_code==200:
            return response.json()
        elif response.status_code==429:
            console.print("[red]Rate limit exceeded. Please wait a minute.[/red]")
            return None
        elif response.status_code==404:
            console.print("[red]Video not found or comments disabled.[/red]")
            return None
        else:
            console.print(f"[red]API Error: {response.status_code}[/red]")
            console.print(f"[yellow]{response.text}[/yellow]")
            return None
        
    except requests.exceptions.ConnectionError:
        console.print("[red]Cannot connect to API. Check if the server running!![/red]")
        console.print(f"[yellow]Trying to connect to: {API_BASE_URL}[/yellow]")
        return None
    except requests.exceptions.Timeout:
        console.print("[red]Request Timeout. Video might have too many comments.[/red]")
        return None
    except Exception as e:
        console.print(f"[red]Unexpected Error: {str(e)}[/red]")
        return None
    

def check_api_health() -> bool:
    """Check if API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False
    

def create_header(data: Dict[str, Any]) -> Panel:
    """Create header panel with video info"""
    header_text = Text()
    header_text.append("SENTIMENT ANALYSIS REPORT\n", style="bold")
    header_text.append("═" * 60 + "\n", style="dim")
    header_text.append("Video ID: ", style="bold")
    header_text.append(f"{data['video_id']}\n", style="yellow")
    header_text.append("Total Comments: ", style="bold")
    header_text.append(f"{data['total_comments']}\n", style="yellow")
    header_text.append("Valid Coments: ", style="bold")
    header_text.append(f"{data['valid_comments']}\n", style="yellow")
    header_text.append("Processing Time: ", style="bold")
    header_text.append(f"{data['processing_time_ms']}\n", style="yellow")
    header_text.append("Cached: ", style="bold")    
    cache_color = "orange" if data.get("cached", False) else "yellow"
    header_text.append(f"{data['cached']}\n", style=cache_color)

    return Panel(header_text, border_style="cyan", box=box.DOUBLE)

# ---

def create_sentiment_bars(dist: Dict[str, float]) -> str:
    """Create ASCII bar chart for sentiment distribution"""
    
    # Calculate bar lengths (max 40 chars)
    max_width = 40
    pos_bar = "█" * int(dist['positive'] / 100 * max_width)
    neu_bar = "█" * int(dist['neutral'] / 100 * max_width)
    neg_bar = "█" * int(dist['negative'] / 100 * max_width)
    
    # Pad with empty chars
    pos_bar = pos_bar.ljust(max_width, "░")
    neu_bar = neu_bar.ljust(max_width, "░")
    neg_bar = neg_bar.ljust(max_width, "░")
    
    return pos_bar, neu_bar, neg_bar

def display_sentiment_distribution(data: Dict[str, Any]):
    dist = data["sentiment_distribution"]
    table = Table(
        title="📊 SENTIMENT DISTRIBUTION",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan"
    )
    table.add_column("Sentiment", style="bold", width=12)
    table.add_column("Bar", width=42)
    table.add_column("Percentage", justify="right", style="bold", width=10)

    pos_bar, neu_bar, neg_bar = create_sentiment_bars(dist)

    table.add_row(
        "😊 Positive",
        f"[green]{pos_bar}[/green]",
        f"[green]{dist['positive']:.1f}%[/green]"
    )
    table.add_row(
        "😐 Neutral",
        f"[yellow]{neu_bar}[/yellow]",
        f"[yellow]{dist['neutral']:.1f}%[/yellow]"
    )
    table.add_row(
        "😞 Negative",
        f"[red]{neg_bar}[/red]",
        f"[red]{dist['negative']:.1f}%[/red]"
    )
    
    console.print(table)

    # Overall sentiment
    overall = data['overall_sentiment']
    confidence = data['average_confidence']
    
    if overall == "positive":
        sentiment_emoji = "😊"
        sentiment_color = "green"
    elif overall == "negative":
        sentiment_emoji = "😞"
        sentiment_color = "red"
    else:
        sentiment_emoji = "😐"
        sentiment_color = "yellow"
    
    console.print()
    console.print(
        f"[bold]Overall Sentiment:[/bold] [{sentiment_color}]{sentiment_emoji} {overall.upper()}[/{sentiment_color}]"
    )
    console.print(
        f"[bold]Average Confidence:[/bold] [cyan]{confidence:.2%}[/cyan]"
    )
    console.print()


def display_statistics(data: Dict[str, Any]):
    comments = data.get('comments', [])
    
    if not comments:
        return
    
    # Calculate stats
    total_likes = sum(c['like_count'] for c in comments)
    avg_likes = total_likes / len(comments) if comments else 0
    
    # Most liked comment
    most_liked = max(comments, key=lambda c: c['like_count'])
    
    # Create stats panel
    stats_text = Text()
    stats_text.append("📈 ENGAGEMENT METRICS\n", style="bold cyan")
    stats_text.append("─" * 50 + "\n", style="dim")
    stats_text.append(f"Total Likes: ", style="bold")
    stats_text.append(f"{total_likes:,}\n", style="green")
    stats_text.append(f"Avg Likes/Comment: ", style="bold")
    stats_text.append(f"{avg_likes:.1f}\n", style="green")
    stats_text.append(f"\nMost Liked Comment ({most_liked['like_count']} likes):\n", style="bold yellow")
    stats_text.append(f'"{most_liked["text"][:100]}..."\n', style="italic")
    stats_text.append(f"by {most_liked['author']}\n", style="dim")
    
    console.print(Panel(stats_text, border_style="green", box=box.ROUNDED))
    console.print()


# ---

def export_results(data: Dict[str, Any], filename: str = "analysis_report.json"):
    """Export Sentiment Analysis Report to JSON file"""
    data["exported_at"] = datetime.now().isoformat()
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    console.print(f"[bold italic green] Results exported to {filename}[/bold italic green]")

# ---

def display_full_report(data: Dict[str, Any]):
    """Display complete analysis report"""
    console.clear()
    console.print()

    console.print(create_header(data))
    console.print()

    display_sentiment_distribution(data)
    
    display_statistics(data)
    
    footer = Text()
    footer.append("⚡ Powered by ", style="dim")
    footer.append("RoBERTa Sentiment Model", style="bold cyan")
    footer.append(" | Built with ", style="dim")
    footer.append("FastAPI + Rich", style="bold magenta")
    
    console.print(Panel(footer, border_style="dim"))
    console.print()


def main():
    """Main CLI Interface"""
    console.print()
    console.print("[bold cyan]YouTube Sentiment Analysis Dashboard[/bold cyan]")
    console.print("[dim]Powered by RoBERTa Transformer Model[/dim]")
    console.print("")

    # check API health
    console.print("Checking API connection...", end=" ")
    if check_api_health():
        console.print("[bold green] Connected [/bold green]")
    else:
        console.print("[red] API not reachable[/red]")
        console.print("[yellow]Run on terminal: python -m uvicorn src.api.main:app --reload[/yellow]")

    console.print()

    url = console.input("[bold]Enter YouTube URL:[/bold] ").strip()
    if not url:
        console.print("[red] URL cannot be empty[/red]")
        sys.exit(1)
    try:
        max_comments_input = console.input("[bold] Max Comments to analyze:[/bold] ").strip()
        max_comments = int(max_comments_input) if max_comments_input else 100

    except ValueError:
        console.print("[yellow]Invalid number. Using default: 100 comments[/yellow]")
        max_comments = 100

    console.print()

    with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
        task = progress.add_task(
            "[cyan]🔄 Analyzing comments...", 
            total=None
        )
        result = call_the_api(url, max_comments)
        progress.update(task, completed=True)
    
    console.print()
    
    if result:
        display_full_report(result)
        
        console.print()
        another = console.input(
            "[bold]Analyze another video? (y/n):[/bold] "
        ).strip().lower()
        
        if another == 'y':
            console.print()
            main()
        else:
            console.print("[green]Thanks for using the dashboard![/green]")
    else:
        console.print("[red] Analysis failed. See error above.[/red]")
        sys.exit(1)

    export_results(result)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Analysis cancelled by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Unexpected Error: {e}[/red]")
        sys.exit(1)