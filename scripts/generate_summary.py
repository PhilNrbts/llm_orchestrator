import glob
import os
import re


def extract_section(content, start_heading):
    """
    Extracts content from a markdown string, starting from a specific heading
    until the next heading of the same or higher level.
    """
    # Find the start of the section
    # This regex looks for the heading at the beginning of a line
    start_match = re.search(
        f"^{re.escape(start_heading)}$", content, re.MULTILINE | re.IGNORECASE
    )
    if not start_match:
        return ""

    content_after_start = content[start_match.end() :]

    # Determine the heading level (e.g., ## -> level 2)
    level = start_heading.count("#")

    # Regex to find the next heading of the same or higher level
    # e.g., if level is 2 (##), find the next ^(##? .*)$
    next_heading_pattern = f"^#{'{'}{'1,'}{level}{'}'} .*$"

    # Search for the next heading in the rest of the content
    next_match = re.search(next_heading_pattern, content_after_start, re.MULTILINE)

    if next_match:
        # If a next heading is found, slice the content up to that point
        end_pos = next_match.start()
        return content_after_start[:end_pos].strip()
    else:
        # If no subsequent heading, return the rest of the content
        return content_after_start.strip()


def create_file_overview(root_path):
    """
    Creates a markdown section for the file overview.
    """
    overview = ["## File Overview\n"]
    overview.append(
        "This is a high-level overview of the key files and directories in the project.\n"
    )

    file_structure = {
        "app/": "Core application logic.",
        "app/main.py": "Main CLI entry point (using Click).",
        "app/orchestrator.py": "Logic for running queries.",
        "app/clients.py": "Clients for different LLM providers.",
        "app/key_management.py": "Secure vault and key handling.",
        "app/session.py": "Manages user session and configuration.",
        "app/chat.py": "Interactive chat functionality.",
        "docs/": "Project documentation.",
        "docs/ROADMAP.md": "The development roadmap.",
        "docs/architecture/": "C4 model diagrams and ADRs.",
        "docs/usage/": "User guides (installation, configuration).",
        "scripts/": "Helper scripts for development and setup.",
        "tests/": "Unit and integration tests.",
        "config.yaml": "Main configuration file.",
        "models.yaml": "Configuration for LLM models.",
        "pyproject.toml": "Project metadata and dependencies for Poetry.",
        "README.md": "Main project README.",
    }

    for path, description in file_structure.items():
        overview.append(f"* **{path}**: {description}\n")

    overview.append("\n---\n\n")
    return "".join(overview)


def create_compressed_summary(root_path):
    """
    Generates a compressed and structured summary from key Markdown files,
    extracting only the most relevant sections to avoid redundancy.
    """
    summary = ["# LLM Orchestrator Project Overview\n"]

    # --- 1. Project README (Extracting only the Quick Start) ---
    readme_path = os.path.join(root_path, "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, encoding="utf-8") as f:
            content = f.read()
            # Add the project's one-liner description
            summary.append(content.split("\n")[2] + "\n")
            summary.append("---\n\n")
            # Extract and add the quick start guide
            quick_start = extract_section(content, "## Quick Start")
            summary.append("## Quick Start\n")
            summary.append(quick_start + "\n")
            summary.append(
                "For detailed instructions, see the **Installation** and **Configuration** sections below.\n"
            )
            summary.append("---\n\n")

    # --- 2. File Overview ---
    summary.append(create_file_overview(root_path))

    # --- 3. Architecture Section (C4 and ADRs) ---
    summary.append("## Architecture\n")
    summary.append(
        "The project's architecture is documented using the C4 model and Architecture Decision Records (ADRs).\n"
    )

    # C4 Models: Extracting bullet points
    summary.append("### C4 Model\n")
    c4_files = {
        "C1: System Context": "docs/architecture/c1-system-context.md",
        "C2: Containers": "docs/architecture/c2-container-diagram.md",
        "C3: Components": "docs/architecture/c3-component-diagram.md",
    }
    for title, path in c4_files.items():
        file_path = os.path.join(root_path, path)
        if os.path.exists(file_path):
            with open(file_path, encoding="utf-8") as f:
                # Extracts the first bulleted list from the file
                bullets = re.search(r"(\\* .*\\n)+", f.read(), re.MULTILINE)
                if bullets:
                    summary.append(
                        f"* **{title}**: {' '.join([line.strip('* ') for line in bullets.group(0).strip().splitlines()])}\\n"
                    )

    # ADRs: Extracting only the "Decision" section
    summary.append("\n### Key Architectural Decisions (ADRs)\n")
    adr_path = os.path.join(root_path, "docs/architecture/adr")
    if os.path.exists(adr_path):
        adr_files = sorted(
            glob.glob(os.path.join(adr_path, "00[1-9]*.md"))
        )  # Ignore template
        for adr_file in adr_files:
            with open(adr_file, encoding="utf-8") as f:
                content = f.read()
                title = content.split("\n")[0].replace("# ", "")
                decision = extract_section(content, "## Decision")
                summary.append(f"* **{title}**: {decision}\n")
    summary.append("\n---\n\n")

    # --- 4. Roadmap ---
    roadmap_path = os.path.join(root_path, "docs/ROADMAP.md")
    if os.path.exists(roadmap_path):
        summary.append("## Roadmap and Future Directions\n")
        with open(roadmap_path, encoding="utf-8") as f:
            content = f.read()
            # Extract just the list of future directions
            future_directions = extract_section(content, "## Development Roadmap")
            summary.append(future_directions + "\n")
    summary.append("---\n\n")

    # --- 5. Contributing ---
    contrib_path = os.path.join(root_path, "docs/contributing.md")
    if os.path.exists(contrib_path):
        summary.append("## Contributing\n")
        with open(contrib_path, encoding="utf-8") as f:
            # Extract just the key bullet points or code blocks
            content = f.read()
            summary.append("* **Setup**: `poetry install`\n")
            summary.append(
                f"* **Code Style**: {extract_section(content, '## Code Style')}\n"
            )
            summary.append(
                f"* **Proposing Changes**: {extract_section(content, '## Proposing Changes')}\n"
            )

    return "".join(summary)


if __name__ == "__main__":
    # Assuming this script is in a 'scripts' directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    summary_content = create_compressed_summary(project_root)

    docs_dir = os.path.join(project_root, "docs")
    output_filename = os.path.join(docs_dir, "PROJECT_OVERVIEW.md")
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(summary_content)

    print(f"Project overview created at {output_filename}")
