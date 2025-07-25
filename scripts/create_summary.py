import glob
import os


def create_summary(root_path):
    """
    Generates a summary from all Markdown files in the specified root path,
    with a special focus on architecture details.
    """
    summary = []
    architecture_docs = []
    other_docs = []

    for md_file in glob.glob(os.path.join(root_path, "**/*.md"), recursive=True):
        if "architecture" in md_file:
            architecture_docs.append(md_file)
        else:
            other_docs.append(md_file)

    summary.append("# Project Summary")
    summary.append("## Architecture")

    for doc in sorted(architecture_docs):
        summary.append(f"### {os.path.basename(doc)}")
        with open(doc) as f:
            summary.append(f.read())
        summary.append("\n---\n")

    summary.append("## Other Documents")

    for doc in sorted(other_docs):
        summary.append(f"### {os.path.basename(doc)}")
        with open(doc) as f:
            summary.append(f.read())
        summary.append("\n---\n")

    return "\n".join(summary)


if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    summary_content = create_summary(project_root)
    with open(os.path.join(project_root, "project_summary.md"), "w") as f:
        f.write(summary_content)
    print("Project summary created at project_summary.md")
