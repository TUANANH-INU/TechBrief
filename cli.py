#!/usr/bin/env python3
"""
TechBrief CLI - Management tool for the research system
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd):
    """Run shell command and print output"""
    print(f"🔧 Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    return result.returncode == 0


def docker_exec(container, cmd):
    """Execute command in docker container"""
    full_cmd = ["docker", "exec", "-it", container] + cmd.split()
    return run_command(full_cmd)


def cmd_start(args):
    """Start all services"""
    print("🚀 Starting TechBrief services...")
    if run_command(["docker-compose", "up", "-d"]):
        print("✅ Services started!")
        print("   - PostSQL: localhost:5432")
        print("   - Ollama: localhost:11434")
        print("   - API: http://localhost:8000/docs")
    else:
        print("Failed to start services")
        return 1


def cmd_stop(args):
    """Stop all services"""
    print("🛑 Stopping TechBrief services...")
    if run_command(["docker-compose", "down"]):
        print("✅ Services stopped!")
    else:
        print("Failed to stop services")
        return 1


def cmd_logs(args):
    """View service logs"""
    service = args.service or "backend"
    run_command(["docker-compose", "logs", "-f", service])


def cmd_research(args):
    """Trigger research manually"""
    print("🔬 Triggering research job...")
    cmd = ["curl", "-X", "POST", "http://localhost:8000/api/research/run-research"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print("Failed to trigger research")
        return 1


def cmd_articles(args):
    """Get latest articles"""
    print("📰 Latest articles:")
    cmd = ["curl", "http://localhost:8000/api/research/articles?limit=5"]
    subprocess.run(cmd)


def cmd_stats(args):
    """Get research statistics"""
    print("📊 Research statistics:")
    cmd = ["curl", "http://localhost:8000/api/research/stats"]
    subprocess.run(cmd)


def cmd_health(args):
    """Check system health"""
    print("🏥 Checking system health...")
    cmd = ["curl", "http://localhost:8000/api/research/health"]
    subprocess.run(cmd)
    print()


def cmd_pull_model(args):
    """Pull Ollama model"""
    model = args.model or "mistral"
    print(f"📥 Pulling model: {model}")
    print("   (This may take 5-10 minutes depending on model size)")

    cmd = f"docker exec techbrief_ollama ollama pull {model}".split()
    run_command(cmd)


def cmd_list_models(args):
    """List available models in Ollama"""
    print("📊 Available models:")
    cmd = "docker exec techbrief_ollama ollama list".split()
    run_command(cmd)


def cmd_test_slack(args):
    """Test Slack webhook"""
    skill = args.skill or "FastAPI"
    print(f"📨 Sending test Slack message for skill: {skill}...")
    cmd = ["curl", "-X", "POST", f"http://localhost:8000/api/research/send-slack?skill={skill}"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print("Failed to send test Slack message")
        return 1


def cmd_shell_db(args):
    """Connect to PostgreSQL"""
    print("🛢️  Connecting to PostgreSQL...")
    cmd = ["docker", "exec", "-it", "techbrief_db", "psql", "-U", "postgres", "-d", "techbrief_db"]
    subprocess.run(cmd)


def cmd_clean(args):
    """Clean up all data"""
    print("🗑️  Removing all containers and volumes...")
    response = input("⚠️  This will DELETE all data. Continue? (yes/no): ")
    if response.lower() == "yes":
        run_command(["docker-compose", "down", "-v"])
        print("✅ Cleaned!")
    else:
        print("Cancelled")


def cmd_init(args):
    """Initialize system"""
    print("⚙️  Initializing TechBrief...")

    # Check Docker
    try:
        subprocess.run(["docker", "--version"], capture_output=True, check=True)
    except Exception:
        print("Docker not found. Please install Docker first.")
        return 1

    # Create .env if not exists
    if not Path(".env").exists():
        print("📝 Creating .env from .env.example...")
        subprocess.run(["cp", ".env.example", ".env"])

    # Start services
    cmd_start(args)

    # Pull default model
    print("📥 Pulling mistral model (10-15 min, can be customized later)...")
    docker_exec("techbrief_ollama", "ollama pull mistral")

    print("✅ Initialization complete!")
    print("📖 Read the README.md for detailed instructions")


def main():
    parser = argparse.ArgumentParser(
        description="TechBrief CLI - Management tool for research system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ./cli.py init              # First-time setup
  ./cli.py start             # Start services
  ./cli.py research          # Trigger research job
  ./cli.py articles          # View latest articles
  ./cli.py stats             # View statistics
  ./cli.py logs backend      # View backend logs
  ./cli.py pull-model llama2 # Change model
  ./cli.py shell-db          # Connect to database
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Initialize
    subparsers.add_parser("init", help="Initialize system (first time setup)")

    # Start/Stop
    subparsers.add_parser("start", help="Start all services")
    subparsers.add_parser("stop", help="Stop all services")

    # Logs
    logs_parser = subparsers.add_parser("logs", help="View service logs")
    logs_parser.add_argument("service", nargs="?", default="backend", help="Service: backend, postgres, ollama (default: backend)")

    # Research
    subparsers.add_parser("research", help="Trigger research job manually")

    # Articles/Stats
    subparsers.add_parser("articles", help="Get latest articles")
    subparsers.add_parser("stats", help="Get research statistics")
    subparsers.add_parser("health", help="Check system health")

    # Models
    pull_parser = subparsers.add_parser("pull-model", help="Pull Ollama model")
    pull_parser.add_argument(
        "model",
        nargs="?",
        default="mistral",
        help="Model name (default: mistral). Examples: llama2, neural-chat, tinyllama",
    )

    subparsers.add_parser("list-models", help="List available models in Ollama")

    # Slack
    slack_parser = subparsers.add_parser("test-slack", help="Test Slack webhook integration")
    slack_parser.add_argument(
        "skill",
        nargs="?",
        default="FastAPI",
        help="Skill to include in test message (default: FastAPI)",
    )

    # Database
    subparsers.add_parser("shell-db", help="Connect to PostgreSQL")

    # Cleanup
    subparsers.add_parser("clean", help="Remove all data and containers")

    args = parser.parse_args()

    # Map commands to functions
    commands = {
        "init": cmd_init,
        "start": cmd_start,
        "stop": cmd_stop,
        "logs": cmd_logs,
        "research": cmd_research,
        "articles": cmd_articles,
        "stats": cmd_stats,
        "health": cmd_health,
        "pull-model": cmd_pull_model,
        "list-models": cmd_list_models,
        "test-slack": cmd_test_slack,
        "shell-db": cmd_shell_db,
        "clean": cmd_clean,
    }

    if args.command not in commands:
        parser.print_help()
        return 0

    return commands[args.command](args) or 0


if __name__ == "__main__":
    sys.exit(main())
