#!/usr/bin/env python3
"""
Simple batch PDF to Markdown conversion using Docling with image export
"""

import os
import time
import multiprocessing
import urllib.parse
import re
from pathlib import Path

# =============================================================================
# CONFIGURATION SETTINGS
# =============================================================================

# Input and output directories
INPUT_DIR = "pdf_source"
OUTPUT_DIR = "conversion_results/docling"

# Worker settings
MAX_WORKERS_CUDA = 2      # Conservative for GPU memory
MAX_WORKERS_MPS = 2       # Conservative for Apple Silicon
MAX_WORKERS_CPU = 4       # More workers for CPU-only

# =============================================================================

def get_device():
    """Determine the best available device for processing."""
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"
    except ImportError:
        return "cpu"

def fix_markdown_image_paths(md_content):
    """Fix image paths in markdown to properly encode special characters."""
    
    # Find all image links and replace them with encoded versions
    lines = md_content.split('\n')
    fixed_lines = []
    
    for line in lines:
        if '![Image](' in line and line.strip().endswith('.png)'):
            # Extract the path from the line
            start_idx = line.find('![Image](') + 9  # length of '![Image]('
            end_idx = line.rfind('.png)') + 4  # include '.png'
            
            if start_idx < end_idx:
                path = line[start_idx:end_idx]
                
                # URL encode the path, but keep / and . unencoded for proper paths
                encoded_path = urllib.parse.quote(path, safe='/.:-_')
                
                # Replace the path in the line
                new_line = line[:start_idx] + encoded_path + line[end_idx:]
                fixed_lines.append(new_line)
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def process_single_pdf(args):
    """Process a single PDF file with image extraction."""
    pdf_path, output_dir = args
    start_time = time.time()
    
    try:
        from docling.document_converter import DocumentConverter
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        from docling.document_converter import PdfFormatOption
        from docling_core.types.doc import ImageRefMode
        
        # Create output directory
        pdf_name = Path(pdf_path).stem
        pdf_output_dir = Path(output_dir) / pdf_name
        pdf_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure pipeline for image generation
        pipeline_options = PdfPipelineOptions()
        pipeline_options.images_scale = 2.0  # Higher resolution images
        pipeline_options.generate_page_images = True
        pipeline_options.generate_picture_images = True
        
        # Create converter with image options
        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
        
        # Convert PDF
        result = converter.convert(str(pdf_path))
        
        # Save markdown with image references
        md_path = pdf_output_dir / f"{pdf_name}.md"
        result.document.save_as_markdown(md_path, image_mode=ImageRefMode.REFERENCED)
        
        # Fix image paths in the generated markdown
        with open(md_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # Apply path encoding fixes
        fixed_md_content = fix_markdown_image_paths(md_content)
        
        # Write back the fixed markdown
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(fixed_md_content)
        
        # Count images in artifacts folder
        artifacts_dir = pdf_output_dir / f"{pdf_name}_artifacts"
        image_count = 0
        if artifacts_dir.exists():
            image_count = len(list(artifacts_dir.glob("*.png")))
        
        elapsed_time = time.time() - start_time
        status_msg = f"✓ {pdf_name}: {elapsed_time:.1f}s"
        if image_count > 0:
            status_msg += f" ({image_count} images)"
        return True, status_msg, elapsed_time
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        return False, f"✗ {Path(pdf_path).stem}: {str(e)}", elapsed_time

def main():
    # Setup
    input_path = Path(INPUT_DIR)
    output_path = Path(OUTPUT_DIR)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Find PDF files
    pdf_files = list(input_path.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in '{INPUT_DIR}'")
        return
    
    print(f"Found {len(pdf_files)} PDF files")
    
    # Setup device and workers
    device = get_device()
    print(f"Using device: {device}")
    
    # Auto-determine worker count
    cpu_count = multiprocessing.cpu_count()
    if device == "cuda":
        workers = min(MAX_WORKERS_CUDA, cpu_count)
    elif device == "mps":
        workers = min(MAX_WORKERS_MPS, cpu_count)
    else:
        workers = min(MAX_WORKERS_CPU, cpu_count)
    
    print(f"Using {workers} workers")
    
    # Prepare arguments
    process_args = [(str(pdf), str(output_path)) for pdf in pdf_files]
    
    # Process files
    start_time = time.time()
    
    if workers == 1:
        # Sequential processing
        results = []
        for i, args_tuple in enumerate(process_args, 1):
            print(f"Processing {i}/{len(pdf_files)}: {Path(args_tuple[0]).name}")
            result = process_single_pdf(args_tuple)
            results.append(result)
            print(f"  {result[1]}")
    else:
        # Parallel processing
        with multiprocessing.Pool(workers) as pool:
            results = []
            for i, result in enumerate(pool.imap(process_single_pdf, process_args), 1):
                results.append(result)
                print(f"({i}/{len(pdf_files)}) {result[1]}")
    
    # Summary
    total_time = time.time() - start_time
    successful = sum(1 for r in results if r[0])
    failed = len(results) - successful
    avg_time = sum(r[2] for r in results) / len(results) if results else 0
    
    print(f"\n{'='*50}")
    print(f"Conversion completed in {total_time:.1f} seconds")
    print(f"Successful: {successful}, Failed: {failed}")
    print(f"Average time per file: {avg_time:.1f} seconds")

if __name__ == "__main__":
    main() 