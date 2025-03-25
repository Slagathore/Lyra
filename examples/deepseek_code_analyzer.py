"""
Example script demonstrating how to use DeepSeek API to analyze code with Lyra.
"""
import os
import sys
import argparse
from pathlib import Path

# Add parent directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lyra.self_improvement.llm_advisor import LLMAdvisor, compare_suggestions

def analyze_file(file_path: str, provider: str = "deepseek", prompt_type: str = "code_review", save_output: bool = False):
    """Analyze a file using the specified LLM provider"""
    print(f"Analyzing file: {file_path}")
    print(f"Using provider: {provider}")
    print(f"Analysis type: {prompt_type}")
    print("=" * 50)

    # Check if file exists
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found")
        return

    # Read file content
    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()
    
    print(f"File size: {len(code)} bytes")
    
    # Initialize the LLM advisor
    advisor = LLMAdvisor()
    
    # Check if the provider is enabled
    enabled_providers = advisor.get_enabled_providers()
    if provider not in enabled_providers:
        print(f"Error: Provider '{provider}' is not enabled")
        print(f"Available providers: {', '.join(enabled_providers)}")
        return
    
    # Get advice from the LLM
    print(f"\nRequesting advice from {provider}...")
    result = advisor.get_advice(code, file_path=file_path, provider=provider, prompt_type=prompt_type)
    
    if not result["success"]:
        print(f"Error: {result['error']}")
        return
    
    print(f"\n✓ Analysis completed in {result['elapsed_time']:.2f} seconds")
    print(f"Received {len(result['suggestions'])} suggestions:\n")
    
    # Print suggestions
    for i, suggestion in enumerate(result["suggestions"], 1):
        print(f"Suggestion {i} - {suggestion['type']}:")
        print("-" * 50)
        print(suggestion["text"][:500] + ("..." if len(suggestion["text"]) > 500 else ""))
        print("-" * 50)
        print(f"Confidence: {suggestion['confidence']}\n")
    
    # Save output if requested
    if save_output:
        output_dir = Path("analysis_results")
        output_dir.mkdir(exist_ok=True)
        
        output_file = output_dir / f"{Path(file_path).stem}_analysis.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Analysis of {file_path}\n")
            f.write(f"Provider: {provider}\n")
            f.write(f"Analysis type: {prompt_type}\n\n")
            f.write(f"Full response:\n\n{result['response']}\n\n")
            f.write("-" * 80 + "\n\n")
            f.write("Structured suggestions:\n\n")
            for i, suggestion in enumerate(result["suggestions"], 1):
                f.write(f"Suggestion {i} - {suggestion['type']}:\n")
                f.write("-" * 50 + "\n")
                f.write(f"{suggestion['text']}\n\n")
        
        print(f"Analysis saved to {output_file}")

def compare_providers(file_path: str, providers: list = None):
    """Compare code analysis from multiple providers"""
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found")
        return
    
    # Read file content
    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()
    
    # Get comparison results
    results = compare_suggestions(code, file_path=file_path, providers=providers)
    
    print(f"\nComparison of providers for file: {file_path}")
    print(f"Providers consulted: {results['combined']['providers_consulted']}")
    print(f"Total suggestions: {results['combined']['total_suggestions']}\n")
    
    # Print results from each provider
    for provider, result in results['provider_results'].items():
        if result['success']:
            print(f"\n=== Results from {provider} ===")
            print(f"Response time: {result.get('elapsed_time', 'N/A'):.2f} seconds")
            print(f"Suggestions: {len(result['suggestions'])}")
            print(f"Sample: {result['response'][:300]}...\n")
        else:
            print(f"\n=== {provider} failed: {result.get('error', 'Unknown error')} ===\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze code files using DeepSeek and other LLMs")
    parser.add_argument("file", help="Path to the file to analyze")
    parser.add_argument("--provider", default="deepseek", help="LLM provider to use (default: deepseek)")
    parser.add_argument("--type", default="code_review", choices=["code_review", "bug_fixing", "algorithm_optimization"],
                        help="Type of analysis to perform")
    parser.add_argument("--compare", action="store_true", help="Compare results from multiple providers")
    parser.add_argument("--save", action="store_true", help="Save analysis results to a file")
    
    args = parser.parse_args()
    
    if args.compare:
        # For comparison, use all enabled providers or DeepSeek + local if available
        advisor = LLMAdvisor()
        enabled_providers = advisor.get_enabled_providers()
        compare_providers(args.file, enabled_providers)
    else:
        analyze_file(args.file, args.provider, args.type, args.save)
