#!/usr/bin/env python3
"""
Simple batch PDF to Markdown conversion using Marker
"""

import os
import json
import time
import multiprocessing
from pathlib import Path

# =============================================================================
# CONFIGURATION SETTINGS
# =============================================================================

# Input and output directories
INPUT_DIR = "pdf_source"
OUTPUT_DIR = "conversion_results/marker"

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

def process_single_pdf(args):
    """Process a single PDF file."""
    pdf_path, output_dir = args
    start_time = time.time()
    
    try:
        from marker.converters.pdf import PdfConverter
        from marker.models import create_model_dict
        from marker.output import text_from_rendered
        
        # Create output directory
        pdf_name = Path(pdf_path).stem
        pdf_output_dir = Path(output_dir) / pdf_name
        pdf_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Convert PDF
        converter = PdfConverter(artifact_dict=create_model_dict())
        rendered = converter(str(pdf_path))
        text, out_meta, images = text_from_rendered(rendered)
        
        # Save markdown
        md_path = pdf_output_dir / f"{pdf_name}.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        # Save metadata
        meta_path = pdf_output_dir / f"{pdf_name}_meta.json"
        
        # Extract only the metadata from the rendered object
        metadata = None
        if hasattr(rendered, 'metadata'):
            metadata = rendered.metadata
        elif hasattr(rendered, 'model_dump'):
            try:
                full_data = rendered.model_dump()
                metadata = full_data.get('metadata', {})
            except:
                pass
        elif hasattr(rendered, 'dict'):
            try:
                full_data = rendered.dict()
                metadata = full_data.get('metadata', {})
            except:
                pass
        
        # If we couldn't get the metadata, create a basic structure
        if metadata is None:
            metadata = {
                "pdf_name": pdf_name,
                "processing_time_seconds": time.time() - start_time,
                "page_count": getattr(rendered, 'page_count', 'unknown'),
                "text_length": len(text),
                "images_extracted": len(images) if images else 0
            }
        
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False, default=str)
        
        # Save images
        image_count = 0
        if images:
            for image_name, image_obj in images.items():
                try:
                    image_path = pdf_output_dir / image_name
                    if hasattr(image_obj, 'save'):
                        image_obj.save(image_path)
                        image_count += 1
                except Exception as e:
                    print(f"Warning: Could not save image {image_name}: {e}")
        
        elapsed_time = time.time() - start_time
        return True, f"✓ {pdf_name}: {elapsed_time:.1f}s ({image_count} images)", elapsed_time
        
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
    
    # Set torch device
    os.environ["TORCH_DEVICE"] = device
    
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