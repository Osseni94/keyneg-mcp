"""
KeyNeg MCP Server - Sentiment Analysis for AI Agents

The first general-purpose sentiment analysis tool for Claude, ChatGPT, and Gemini.
Provides 95+ sentiment labels and keyword extraction through the Model Context Protocol.

Author: Kaossara Osseni
Email: admin@grandnasser.com
Website: https://grandnasser.com
"""

import os
import sys
from typing import Optional
from mcp.server.fastmcp import FastMCP

from keyneg_mcp.licensing import license_manager, LicenseTier

# Initialize MCP server
mcp = FastMCP(name="keyneg")

# Lazy load KeyNeg to avoid import errors if not installed
_keyneg_instance = None


def get_keyneg():
    """Lazy load KeyNeg instance."""
    global _keyneg_instance

    if _keyneg_instance is not None:
        return _keyneg_instance

    try:
        from keyneg import KeyNeg

        # Check for model path in environment or default location
        model_dir = os.environ.get("KEYNEG_MODEL_PATH")

        if not model_dir:
            # Try default locations
            default_paths = [
                os.path.expanduser("~/.keyneg/models/all-mpnet-base-v2"),
                os.path.expanduser("~/.keyneg/models"),
                "./models",
            ]
            for path in default_paths:
                if os.path.exists(path) and os.path.isfile(os.path.join(path, "model.onnx")):
                    model_dir = path
                    break

        if not model_dir:
            raise FileNotFoundError(
                "KeyNeg model not found. Please set KEYNEG_MODEL_PATH or "
                "install models to ~/.keyneg/models/"
            )

        # Build paths to model and tokenizer
        model_path = os.path.join(model_dir, "model.onnx")
        tokenizer_path = os.path.join(model_dir, "tokenizer.json")

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        if not os.path.exists(tokenizer_path):
            raise FileNotFoundError(f"Tokenizer file not found: {tokenizer_path}")

        _keyneg_instance = KeyNeg(model_path, tokenizer_path)
        return _keyneg_instance

    except ImportError:
        raise ImportError(
            "keyneg-enterprise-rs is not installed. "
            "Install with: pip install keyneg-enterprise-rs --extra-index-url https://pypi.grandnasser.com/simple"
        )


@mcp.tool()
def analyze_sentiment(
    text: str,
    top_n: int = 5,
) -> dict:
    """
    Analyze sentiment in text and return top sentiment labels with scores.

    Use this tool to understand the emotional tone and sentiment of text content.
    Perfect for analyzing customer feedback, reviews, support tickets, or any text
    where understanding sentiment is important.

    Args:
        text: The text to analyze for sentiment
        top_n: Number of top sentiment labels to return (default: 5)

    Returns:
        Dictionary with sentiment labels, scores, and usage info

    Example:
        analyze_sentiment("The service was terrible and the staff was rude")
        -> Returns top negative sentiments like "poor customer service", "hostile", etc.
    """
    # Check license and usage
    allowed, message = license_manager.check_and_increment_usage()
    if not allowed:
        return {
            "error": message,
            "upgrade_url": "https://grandnasser.com/docs/keyneg-rs",
        }

    # Apply tier limits
    max_labels = license_manager.get_feature("max_sentiment_labels", 3)
    top_n = min(top_n, max_labels)

    try:
        kn = get_keyneg()
        sentiments = kn.extract_sentiments(text, top_n=top_n)

        # Format results
        results = [
            {"label": label, "score": round(score, 4)}
            for label, score in sentiments
        ]

        response = {
            "text": text[:100] + "..." if len(text) > 100 else text,
            "sentiments": results,
            "count": len(results),
        }

        # Add tier info for limited tiers
        if license_manager.current_tier in (LicenseTier.FREE, LicenseTier.TRIAL):
            response["tier"] = license_manager.current_tier.value
            response["upgrade_url"] = "https://grandnasser.com/docs/keyneg-rs"

        return response

    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def extract_keywords(
    text: str,
    top_n: int = 10,
) -> dict:
    """
    Extract negative keywords and phrases from text.

    Use this tool to identify specific negative terms, complaints, or issues
    mentioned in text. Useful for categorizing feedback or identifying
    specific problem areas.

    Args:
        text: The text to extract keywords from
        top_n: Number of keywords to return (default: 10)

    Returns:
        Dictionary with keywords, scores, and usage info

    Example:
        extract_keywords("The product broke after one day and support never responded")
        -> Returns keywords like "broke", "never responded", etc.
    """
    # Check license and usage
    allowed, message = license_manager.check_and_increment_usage()
    if not allowed:
        return {
            "error": message,
            "upgrade_url": "https://grandnasser.com/docs/keyneg-rs",
        }

    # Check if keywords are enabled for this tier
    if not license_manager.get_feature("keywords_enabled", False):
        return {
            "error": "Keyword extraction requires Pro or Enterprise tier",
            "tier": license_manager.current_tier.value,
            "upgrade_url": "https://grandnasser.com/docs/keyneg-rs",
        }

    try:
        kn = get_keyneg()
        keywords = kn.extract_keywords(text, top_n=top_n)

        # Format results
        results = [
            {"keyword": kw, "score": round(score, 4)}
            for kw, score in keywords
        ]

        response = {
            "text": text[:100] + "..." if len(text) > 100 else text,
            "keywords": results,
            "count": len(results),
        }

        return response

    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def full_analysis(
    text: str,
    sentiment_top_n: int = 5,
    keyword_top_n: int = 10,
) -> dict:
    """
    Perform comprehensive sentiment and keyword analysis on text.

    Combines sentiment analysis and keyword extraction in a single call.
    Use this for complete text analysis when you need both sentiment
    understanding and specific issue identification.

    Args:
        text: The text to analyze
        sentiment_top_n: Number of sentiment labels (default: 5)
        keyword_top_n: Number of keywords (default: 10)

    Returns:
        Dictionary with sentiments, keywords, and summary

    Example:
        full_analysis("The hotel room was dirty, staff was unhelpful, and the food was cold")
        -> Returns both sentiment labels and specific complaint keywords
    """
    # Check license and usage (counts as one call)
    allowed, message = license_manager.check_and_increment_usage()
    if not allowed:
        return {
            "error": message,
            "upgrade_url": "https://grandnasser.com/docs/keyneg-rs",
        }

    # Apply tier limits
    max_labels = license_manager.get_feature("max_sentiment_labels", 3)
    sentiment_top_n = min(sentiment_top_n, max_labels)
    keywords_enabled = license_manager.get_feature("keywords_enabled", False)

    try:
        kn = get_keyneg()

        # Get sentiments
        sentiments = kn.extract_sentiments(text, top_n=sentiment_top_n)
        sentiment_results = [
            {"label": label, "score": round(score, 4)}
            for label, score in sentiments
        ]

        response = {
            "text": text[:100] + "..." if len(text) > 100 else text,
            "sentiments": sentiment_results,
            "sentiment_count": len(sentiment_results),
        }

        # Get keywords if enabled
        if keywords_enabled:
            keywords = kn.extract_keywords(text, top_n=keyword_top_n)
            keyword_results = [
                {"keyword": kw, "score": round(score, 4)}
                for kw, score in keywords
            ]
            response["keywords"] = keyword_results
            response["keyword_count"] = len(keyword_results)
        else:
            response["keywords"] = []
            response["keywords_note"] = "Keyword extraction requires Pro tier"

        # Determine overall sentiment
        if sentiment_results:
            top_score = sentiment_results[0]["score"]
            if top_score >= 0.5:
                response["overall"] = "strongly_negative"
            elif top_score >= 0.3:
                response["overall"] = "moderately_negative"
            else:
                response["overall"] = "mildly_negative"

        # Add tier info for limited tiers
        if license_manager.current_tier in (LicenseTier.FREE, LicenseTier.TRIAL):
            response["tier"] = license_manager.current_tier.value
            response["upgrade_url"] = "https://grandnasser.com/docs/keyneg-rs"

        return response

    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def batch_analyze(
    texts: list[str],
    top_n: int = 3,
) -> dict:
    """
    Analyze sentiment for multiple texts in batch.

    Efficiently process multiple pieces of text at once.
    Use this when you have several documents, reviews, or messages
    to analyze together.

    Args:
        texts: List of texts to analyze
        top_n: Number of sentiment labels per text (default: 3)

    Returns:
        Dictionary with results for each text

    Example:
        batch_analyze(["Great product!", "Terrible service", "It was okay"])
        -> Returns sentiment analysis for each text
    """
    # Check if batch is enabled
    if not license_manager.get_feature("batch_enabled", False):
        return {
            "error": "Batch processing requires Trial, Pro, or Enterprise tier",
            "tier": license_manager.current_tier.value,
            "upgrade_url": "https://grandnasser.com/docs/keyneg-rs",
        }

    # Check license and usage (counts as one call per text)
    results = []
    for i, text in enumerate(texts):
        allowed, message = license_manager.check_and_increment_usage()
        if not allowed:
            results.append({
                "index": i,
                "text": text[:50] + "..." if len(text) > 50 else text,
                "error": message,
            })
            continue

        try:
            kn = get_keyneg()
            max_labels = license_manager.get_feature("max_sentiment_labels", 3)
            actual_top_n = min(top_n, max_labels)

            sentiments = kn.extract_sentiments(text, top_n=actual_top_n)
            sentiment_results = [
                {"label": label, "score": round(score, 4)}
                for label, score in sentiments
            ]

            results.append({
                "index": i,
                "text": text[:50] + "..." if len(text) > 50 else text,
                "sentiments": sentiment_results,
            })

        except Exception as e:
            results.append({
                "index": i,
                "text": text[:50] + "..." if len(text) > 50 else text,
                "error": str(e),
            })

    return {
        "total": len(texts),
        "processed": len([r for r in results if "error" not in r]),
        "results": results,
    }


@mcp.tool()
def get_usage_info() -> dict:
    """
    Get current license and usage information.

    Check your current tier, daily usage, and remaining calls.
    Useful for monitoring usage and understanding your current limits.

    Returns:
        Dictionary with tier, usage stats, and feature availability
    """
    usage = license_manager.usage_info
    features = {
        "sentiment_labels": license_manager.get_feature("max_sentiment_labels"),
        "keywords_enabled": license_manager.get_feature("keywords_enabled"),
        "batch_enabled": license_manager.get_feature("batch_enabled"),
        "custom_taxonomy": license_manager.get_feature("custom_taxonomy"),
    }

    return {
        "license": usage,
        "features": features,
        "upgrade_url": "https://grandnasser.com/docs/keyneg-rs",
    }


@mcp.tool()
def get_sentiment_labels() -> dict:
    """
    Get the list of all available sentiment labels.

    Returns the complete taxonomy of 95+ sentiment labels that KeyNeg
    can detect. Useful for understanding what types of sentiment
    can be identified.

    Returns:
        Dictionary with list of all sentiment labels by category
    """
    try:
        from keyneg import get_default_taxonomy

        taxonomy = get_default_taxonomy()
        return {
            "labels": taxonomy,
            "count": len(taxonomy),
            "note": "Full 95+ labels available in Pro and Enterprise tiers",
        }
    except ImportError:
        # Fallback - return sample labels
        sample_labels = [
            "poor customer service",
            "hostile work environment",
            "lack of communication",
            "unfair treatment",
            "broken promises",
            "quality issues",
            "safety concerns",
            "billing problems",
            "delivery issues",
            "unresponsive support",
        ]
        return {
            "labels": sample_labels,
            "count": len(sample_labels),
            "note": "Sample labels shown. Install keyneg-enterprise-rs for full taxonomy.",
        }


def main():
    """Run the KeyNeg MCP server."""
    # Validate license on startup
    license_info = license_manager.validate_license()
    print(f"KeyNeg MCP Server starting...", file=sys.stderr)
    print(f"License tier: {license_info.tier.value}", file=sys.stderr)

    if license_info.expires_at:
        print(f"Expires: {license_info.expires_at.date()}", file=sys.stderr)

    # Run the server
    mcp.run()


if __name__ == "__main__":
    main()
