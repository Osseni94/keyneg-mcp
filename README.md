# KeyNeg MCP Server

**The first general-purpose sentiment analysis tool for AI agents.**

KeyNeg MCP Server brings enterprise-grade sentiment analysis to Claude, ChatGPT, Gemini, and any AI assistant that supports the Model Context Protocol (MCP).

## Features

- **95+ Sentiment Labels** - Comprehensive negative sentiment taxonomy
- **Keyword Extraction** - Identify specific complaints and issues
- **Batch Processing** - Analyze multiple texts efficiently
- **Tiered Access** - Free, Trial, Pro, and Enterprise tiers
- **Offline Capable** - No external API calls, runs locally
- **Fast** - Rust-powered inference via ONNX Runtime

## Installation

```bash
pip install keyneg-mcp
```

Or install from source:

```bash
git clone https://github.com/Osseni94/keyneg-mcp
cd keyneg-mcp
pip install -e .
```

### Prerequisites

1. **KeyNeg-RS** - The sentiment analysis engine:
   ```bash
   pip install keyneg-enterprise-rs --extra-index-url https://pypi.grandnasser.com/simple
   ```

2. **ONNX Model** - Export or download the model:
   ```bash
   pip install keyneg-enterprise-rs[model-export]
   keyneg-export-model --output-dir ~/.keyneg/models/all-mpnet-base-v2
   ```

## Configuration

### Claude Desktop

Add to your Claude Desktop config (`~/.config/claude/claude_desktop_config.json` on macOS/Linux or `%APPDATA%\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "keyneg": {
      "command": "keyneg-mcp",
      "env": {
        "KEYNEG_MODEL_PATH": "~/.keyneg/models/all-mpnet-base-v2"
      }
    }
  }
}
```

### Claude Code

```bash
claude mcp add keyneg keyneg-mcp
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `KEYNEG_MODEL_PATH` | Path to ONNX model directory | `~/.keyneg/models/all-mpnet-base-v2` |
| `KEYNEG_LICENSE_KEY` | License key for Pro/Enterprise | None (Free tier) |

## Available Tools

### `analyze_sentiment`

Analyze sentiment in text and return top sentiment labels with scores.

```
analyze_sentiment("The service was terrible and staff was rude", top_n=5)
```

**Returns:**
```json
{
  "sentiments": [
    {"label": "poor customer service", "score": 0.7234},
    {"label": "hostile", "score": 0.5123},
    {"label": "unprofessional", "score": 0.4567}
  ]
}
```

### `extract_keywords`

Extract negative keywords and phrases from text. *(Pro/Enterprise only)*

```
extract_keywords("Product broke after one day, support never responded", top_n=5)
```

**Returns:**
```json
{
  "keywords": [
    {"keyword": "broke", "score": 0.8234},
    {"keyword": "never responded", "score": 0.7123}
  ]
}
```

### `full_analysis`

Combined sentiment and keyword analysis.

```
full_analysis("Hotel was dirty, staff unhelpful, food cold")
```

**Returns:**
```json
{
  "sentiments": [...],
  "keywords": [...],
  "overall": "strongly_negative"
}
```

### `batch_analyze`

Analyze multiple texts at once. *(Trial/Pro/Enterprise only)*

```
batch_analyze(["Great!", "Terrible service", "It was okay"])
```

### `get_usage_info`

Check your current tier and usage.

```
get_usage_info()
```

### `get_sentiment_labels`

Get the full taxonomy of sentiment labels.

```
get_sentiment_labels()
```

## Pricing Tiers

| Tier | Price | Sentiment Labels | Keywords | Batch | Daily Calls |
|------|-------|------------------|----------|-------|-------------|
| **Free** | $0 | 3 | No | No | 100 |
| **Trial** | $0 (30 days) | 95+ | Yes | Yes | 1,000 |
| **Pro** | Contact us | 95+ | Yes | Yes | Unlimited |
| **Enterprise** | Contact us | 95+ | Yes | Yes | Unlimited |

Get a license at [grandnasser.com](https://grandnasser.com/docs/keyneg-rs)

## Use Cases

- **Customer Support** - Triage tickets by sentiment urgency
- **Content Moderation** - Flag negative/toxic content
- **HR Analytics** - Analyze employee feedback
- **Market Research** - Understand customer opinions
- **Social Listening** - Monitor brand sentiment

## Example Prompts for Claude

Once configured, you can ask Claude things like:

- *"Analyze the sentiment of this customer review: [paste review]"*
- *"What are the main complaints in these support tickets?"*
- *"Is this feedback positive or negative?"*
- *"Extract the key issues from this employee survey response"*

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run server locally
python -m keyneg_mcp.server
```

## License

MIT License - The MCP server is open source.

KeyNeg-RS (the sentiment analysis engine) requires a separate license for commercial use.

## Support

- **Documentation**: [grandnasser.com/docs/keyneg-mcp](https://grandnasser.com/docs/keyneg-mcp)
- **Issues**: [github.com/Osseni94/keyneg-mcp/issues](https://github.com/Osseni94/keyneg-mcp/issues)
- **Email**: admin@grandnasser.com

## Author

**Kaossara Osseni**
[Grand Nasser Enterprises](https://grandnasser.com)
