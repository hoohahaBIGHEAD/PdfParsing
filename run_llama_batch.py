#!/usr/bin/env python3
"""
Simple batch PDF to Markdown conversion using LlamaParse
"""

import os
import time
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import nest_asyncio

# Load environment variables from .env file
load_dotenv()

# Enable nested async loops
nest_asyncio.apply()

# =============================================================================
# CONFIGURATION SETTINGS
# =============================================================================

# Input and output directories
INPUT_DIR = "pdf_source"
OUTPUT_DIR = "conversion_results/llama_cloud"

# LlamaParse settings
NUM_WORKERS = 4          # Number of parallel workers
LANGUAGE = "en"          # Language setting
VERBOSE = True           # Verbose output

# Output formats
OUTPUT_MARKDOWN = True   # Generate markdown files
OUTPUT_TEXT = True       # Generate text files

# Parse mode options (see: https://docs.cloud.llamaindex.ai/llamaparse/presets_and_modes/advance_parsing_modes)
# Available modes:
# - "parse_page_without_llm": Fast mode (text-only, no AI)
# - "parse_page_with_llm": Balanced mode (default, good for tables/images)
# - "parse_page_with_lvm": Vision model mode (best for rich visual content)
# - "parse_page_with_agent": Premium mode (highest accuracy for complex docs)
# - "parse_page_with_layout_agent": Layout-aware mode (precise positioning)
# - "parse_document_with_llm": Document-level LLM (better continuity)
# - "parse_document_with_agent": Document-level agent (best for complex continuity)
PARSE_MODE = "parse_page_with_llm"  # Default balanced mode

# =============================================================================

async def process_batch_pdfs():
    """Process all PDFs in the input directory using LlamaParse."""
    
    # Import LlamaParse
    try:
        from llama_cloud_services import LlamaParse
    except ImportError:
        print("Error: llama-cloud-services not installed. Run: pip install llama-cloud-services")
        return
    
    # Check for API key
    api_key = os.getenv('LLAMA_CLOUD_API_KEY')
    if not api_key:
        print("Error: LLAMA_CLOUD_API_KEY environment variable not set")
        print("Please set your API key: export LLAMA_CLOUD_API_KEY='llx-...'")
        return
    
    # Get all PDF files
    input_path = Path(INPUT_DIR)
    if not input_path.exists():
        print(f"Error: Input directory '{INPUT_DIR}' not found")
        return
    
    pdf_files = list(input_path.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in '{INPUT_DIR}'")
        return
    
    print(f"Found {len(pdf_files)} PDF files")
    
    # Create output directory
    output_path = Path(OUTPUT_DIR)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize LlamaParse parsers for different output types
    # Markdown parser (primary)
    parser_md = LlamaParse(
        api_key=api_key,
        num_workers=NUM_WORKERS,
        verbose=VERBOSE,
        language=LANGUAGE,
        result_type="markdown",  # For markdown output
        # Advanced settings for better parsing
        use_vendor_multimodal_model=True,  # Enable multimodal processing
        vendor_multimodal_model_name="openai-gpt4o",  # Use GPT-4o for vision
        # Splitting options
        split_by_page=False,  # Keep document continuity
    )
    
    # Text parser (for clean text output)
    parser_txt = None
    if OUTPUT_TEXT:
        parser_txt = LlamaParse(
            api_key=api_key,
            num_workers=NUM_WORKERS,
            verbose=False,  # Less verbose for text parser
            language=LANGUAGE,
            result_type="text",  # For text output
            # Simpler settings for text extraction
            split_by_page=False,
        )
    
    print(f"Using {NUM_WORKERS} workers")
    print(f"Parse mode: {PARSE_MODE}")
    print(f"Output formats: {', '.join([fmt for fmt, enabled in [('Markdown', OUTPUT_MARKDOWN), ('Text', OUTPUT_TEXT)] if enabled])}")
    print("Processing files...")
    
    start_time = time.time()
    
    try:
        # Convert file paths to strings for LlamaParse
        pdf_paths = [str(pdf_path) for pdf_path in pdf_files]
        
        # Parse with markdown parser (primary)
        print("Parsing for markdown output...")
        results_md = await parser_md.aparse(pdf_paths)
        
        # Parse with text parser if needed
        results_txt = None
        if OUTPUT_TEXT and parser_txt:
            print("Parsing for text output...")
            results_txt = await parser_txt.aparse(pdf_paths)
        
        # Process each result
        for i, pdf_path in enumerate(pdf_files):
            pdf_name = pdf_path.stem
            print(f"({i+1}/{len(pdf_files)}) Processing: {pdf_name}")
            
            # Create output directory for this PDF
            pdf_output_dir = output_path / pdf_name
            pdf_output_dir.mkdir(parents=True, exist_ok=True)
            
            saved_files = []
            image_count = 0
            
            # Get results for this file
            result_md = results_md[i]
            result_txt = results_txt[i] if results_txt else None
            
            # Save markdown if enabled
            if OUTPUT_MARKDOWN and result_md:
                md_path = pdf_output_dir / f"{pdf_name}.md"
                markdown_documents = result_md.get_markdown_documents(split_by_page=False)
                
                if markdown_documents:
                    # Combine all markdown content
                    markdown_content = "\n\n".join([doc.text for doc in markdown_documents])
                    with open(md_path, 'w', encoding='utf-8') as f:
                        f.write(markdown_content)
                    saved_files.append("MD")
                
                # Count images from markdown result
                try:
                    for page_idx, page in enumerate(result_md.pages):
                        if hasattr(page, 'images') and page.images:
                            image_count += len(page.images)
                except Exception as img_error:
                    print(f"   Warning: Could not count images: {img_error}")
            
            # Save text if enabled and available
            if OUTPUT_TEXT and result_txt:
                txt_path = pdf_output_dir / f"{pdf_name}.txt"
                text_documents = result_txt.get_text_documents(split_by_page=False)
                
                if text_documents:
                    # Combine all text content
                    text_content = "\n\n".join([doc.text for doc in text_documents])
                    
                    # Clean up the text content
                    if text_content.strip() and text_content.strip() != "---":
                        with open(txt_path, 'w', encoding='utf-8') as f:
                            f.write(text_content)
                        saved_files.append("TXT")
                    else:
                        # Fallback: extract text from pages
                        page_texts = []
                        for page in result_txt.pages:
                            if hasattr(page, 'text') and page.text.strip():
                                page_texts.append(page.text.strip())
                        
                        if page_texts:
                            text_content = "\n\n".join(page_texts)
                            with open(txt_path, 'w', encoding='utf-8') as f:
                                f.write(text_content)
                            saved_files.append("TXT")
            
            # Display saved files and image count
            formats_str = " + ".join(saved_files) if saved_files else "None"
            print(f"   ✓ Saved: {formats_str} ({image_count} images detected)")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print("\n" + "="*50)
        print(f"Conversion completed in {total_time:.1f} seconds")
        print(f"Successful: {len(results_md)}, Failed: 0")
        print(f"Average time per file: {total_time/len(results_md):.1f} seconds")
        
    except Exception as e:
        print(f"Error during processing: {e}")
        return

def main():
    """Main function to run the batch processing."""
    print("LlamaParse Batch PDF to Markdown Converter")
    print("=" * 50)
    
    # Run the async function
    asyncio.run(process_batch_pdfs())

if __name__ == "__main__":
    main() 