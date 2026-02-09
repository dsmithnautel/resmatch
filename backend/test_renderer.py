#!/usr/bin/env python3
"""
Standalone test script for renderer.py

Usage:
    python test_renderer.py                    # Uses latest cv.yaml
    python test_renderer.py <compile_id>       # Uses specific compile folder
    python test_renderer.py --mock             # Creates mock data from scratch
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

from app.models import ScoredUnit
from app.services.rendercv_mapper import map_to_rendercv_model


def test_existing_yaml(compile_id: str | None = None):
    """Test RenderCV rendering using an existing cv.yaml file."""

    output_base = Path(__file__).parent / "output"

    # Find the compile folder
    if compile_id:
        output_dir = output_base / compile_id
        if not output_dir.exists():
            print(f"❌ Folder not found: {output_dir}")
            return
    else:
        # Use the most recent one
        folders = sorted(
            [d for d in output_base.iterdir() if d.is_dir()],
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )
        if not folders:
            print("❌ No output folders found")
            return
        output_dir = folders[0]

    yaml_path = output_dir / "cv.yaml"
    if not yaml_path.exists():
        print(f"❌ cv.yaml not found in {output_dir}")
        return

    print(f"📂 Using: {output_dir.name}")
    print(f"📄 YAML: {yaml_path}")

    # Preview YAML content
    with open(yaml_path) as f:
        cv_data = yaml.safe_load(f)

    print("\n📋 YAML Preview:")
    print(f"   Name: {cv_data.get('cv', {}).get('name', 'N/A')}")
    print(f"   Email: {cv_data.get('cv', {}).get('email', 'N/A') or '⚠️  EMPTY'}")
    print(f"   Phone: {cv_data.get('cv', {}).get('phone', 'N/A') or '⚠️  EMPTY'}")
    print(f"   Theme: {cv_data.get('design', {}).get('theme', 'N/A')}")

    sections = cv_data.get("cv", {}).get("sections", {})
    print(f"   Sections: {', '.join(sections.keys())}")

    # Run RenderCV
    print("\n🚀 Running RenderCV...")
    try:
        cmd = ["rendercv", "render", "cv.yaml"]
        result = subprocess.run(
            cmd, cwd=str(output_dir), capture_output=True, text=True, check=True
        )
        print("✅ RenderCV succeeded!")
        if result.stdout.strip():
            print(f"\nOutput:\n{result.stdout}")

    except subprocess.CalledProcessError as e:
        print("❌ RenderCV failed!")
        print("\nError output:")
        print(e.stderr if e.stderr else e.stdout)
        print("\n💡 Tip: Check the YAML file for validation errors")
        print("💡 Common issues: empty email/phone, invalid design settings")
        return

    # Find generated PDF
    rendercv_out = output_dir / "rendercv_output"
    if rendercv_out.exists():
        pdf_files = list(rendercv_out.glob("*.pdf"))
        if pdf_files:
            found_pdf = pdf_files[0]
            target_pdf = output_dir / "resume.pdf"

            # Move PDF
            shutil.move(str(found_pdf), str(target_pdf))
            print(f"\n✅ PDF generated: {target_pdf}")

            # Cleanup
            shutil.rmtree(rendercv_out, ignore_errors=True)
            print("🧹 Cleaned up intermediate files")

            # Show file size
            size_kb = target_pdf.stat().st_size / 1024
            print(f"📊 PDF size: {size_kb:.1f} KB")
        else:
            print("❌ No PDF found in rendercv_output/")
    else:
        print("❌ rendercv_output/ folder not created")


def test_with_mock_data():
    """Test the full pipeline with mock data (no database needed)."""

    print("🧪 Testing with mock data...")

    # Mock selected units
    selected_units = [
        ScoredUnit(
            text="Developed a full-stack web application using React and Node.js",
            section="experience",
            org="Tech Startup",
            role="Software Engineer",
            dates={"start": "Jan 2023", "end": "Present"},
            llm_score=9.5,
            selected=True,
            matched_requirements=["Full-stack development", "React"],
            tags={"skills": ["React", "Node.js", "JavaScript"]},
        ),
        ScoredUnit(
            text="Built REST APIs serving 10,000+ daily requests",
            section="experience",
            org="Tech Startup",
            role="Software Engineer",
            dates={"start": "Jan 2023", "end": "Present"},
            llm_score=8.8,
            selected=True,
            matched_requirements=["API development"],
            tags={"skills": ["REST", "Node.js"]},
        ),
    ]

    # Mock header info
    header_info = {
        "name": "Test User",
        "email": "test@example.com",
        "phone": "+1 1234567890",
        "linkedin": "https://linkedin.com/in/testuser",
        "github": "https://github.com/testuser",
    }

    # Create test output directory
    output_dir = Path(__file__).parent / "output" / "test_mock"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Map to RenderCV format
    print("📦 Mapping data to RenderCV format...")
    cv_data = map_to_rendercv_model(selected_units, header_info)

    # Save YAML
    yaml_path = output_dir / "cv.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(cv_data, f, sort_keys=False, allow_unicode=True)

    print(f"✅ Created: {yaml_path}")

    # Run RenderCV
    print("\n🚀 Running RenderCV...")
    try:
        cmd = ["rendercv", "render", "cv.yaml"]
        subprocess.run(cmd, cwd=str(output_dir), capture_output=True, text=True, check=True)
        print("✅ RenderCV succeeded!")

    except subprocess.CalledProcessError as e:
        print("❌ RenderCV failed!")
        print(f"Error:\n{e.stderr}")
        return

    # Find and move PDF
    rendercv_out = output_dir / "rendercv_output"
    if rendercv_out.exists():
        pdf_files = list(rendercv_out.glob("*.pdf"))
        if pdf_files:
            target_pdf = output_dir / "resume.pdf"
            shutil.move(str(pdf_files[0]), str(target_pdf))
            print(f"\n✅ PDF generated: {target_pdf}")
            shutil.rmtree(rendercv_out, ignore_errors=True)
        else:
            print("❌ No PDF generated")


def show_available_compiles():
    """List all available compile folders."""
    output_base = Path(__file__).parent / "output"
    folders = sorted(
        [d for d in output_base.iterdir() if d.is_dir()],
        key=lambda x: x.stat().st_mtime,
        reverse=True,
    )

    print("\n📁 Available compile folders:\n")
    for i, folder in enumerate(folders[:10], 1):
        has_yaml = (folder / "cv.yaml").exists()
        has_pdf = (folder / "resume.pdf").exists()
        status = (
            "✅ YAML+PDF" if has_yaml and has_pdf else "📄 YAML only" if has_yaml else "❌ Empty"
        )
        print(f"  {i}. {folder.name:30s} {status}")

    if len(folders) > 10:
        print(f"\n  ... and {len(folders) - 10} more")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--mock":
            test_with_mock_data()
        elif arg == "--list":
            show_available_compiles()
        else:
            # Assume it's a compile_id
            test_existing_yaml(arg)
    else:
        print("🔍 No compile_id specified, using most recent...\n")
        test_existing_yaml()
        print("\n" + "=" * 60)
        print("💡 Tip: Use 'python test_renderer.py --list' to see all options")
        print("💡 Tip: Use 'python test_renderer.py --mock' to test with fake data")
