# AI Pipeline Troubleshooting Guide

## Overview

This guide covers the AI verification pipeline for the community resource directory, including architecture, tools, debugging procedures, and common troubleshooting scenarios.

## Architecture Overview

### Core Components

```
AIReviewService (Main Orchestrator)
├── LLM (meta-llama/llama-4-maverick:free)
├── Agent Executor
├── Web Search Tools (DuckDuckGo)
├── Web Content Extraction (PullMdLoader)
└── Response Parser
```

### Key Files

- **`directory/services/ai/core/review_service.py`**: Main AI service orchestrator
- **`scripts/development/debug_ai_service.py`**: CLI debugging tool
- **`directory/views/ai_api_views.py`**: Manual verification API endpoint
- **`directory/views/ai_auto_verification_views.py`**: Automated verification API endpoint

## AI Pipeline Flow

### 1. Initialization
```python
# AIReviewService.__init__()
- Initialize LLM (meta-llama/llama-4-maverick:free)
- Create tools for agent (web search + content extraction)
- Set up agent executor
```

### 2. Verification Process
```python
# AIReviewService.verify_resource_data()
1. Format input data
2. Create agent with tools
3. Execute agent with resource data
4. Parse AI response
5. Generate verification report
```

### 3. Tool Integration
```python
# Agent uses these tools:
- web_search: DuckDuckGo search for resource information
- fetch_webpage_tool: PullMdLoader for website content extraction
```

## Current Tools (Updated 2025-08-30)

### 1. DuckDuckGo Search Tool
- **Purpose**: Search the web for information about community resources
- **Implementation**: `DuckDuckGoSearchRun` from `langchain_community.tools`
- **Usage**: Searches for current information about resource names, addresses, phone numbers, websites, and services
- **Benefits**: Free, no API key required, privacy-focused
- **Rate Limits**: None (free service)

### 2. PullMdLoader Webpage Tool
- **Purpose**: Fetch and convert web pages to Markdown format
- **Implementation**: `PullMdLoader` from `langchain_pull_md`
- **Usage**: Extracts content from organization websites for analysis
- **Benefits**: Handles JavaScript-rendered pages, cloud-based processing
- **Rate Limits**: 5 requests/second, 20 requests/minute (free tier)

## Removed Tools (Legacy)

The following tools were removed to simplify the system and focus on core web verification capabilities:

- `authoritative_web_search_tool` (replaced by DuckDuckGo search)
- `verify_website_tool` (functionality integrated into PullMdLoader)
- `verify_phone_tool` (basic format validation)
- `verify_email_tool` (basic format validation)
- `verify_address_tool` (basic validation)
- `verify_location_tool` (basic validation)
- `verify_organization_tool` (basic validation)
- `discover_services_tool` (replaced by PullMdLoader + AI analysis)
- `extract_service_details_tool` (replaced by PullMdLoader + AI analysis)

## Debugging Tools

### CLI Debug Tool

The primary debugging tool is located at `scripts/development/debug_ai_service.py`.

#### Usage

```bash
# Test with sample data (verbose output)
python scripts/development/debug_ai_service.py --test-data --verbose

# Test with specific resource ID
python scripts/development/debug_ai_service.py --resource-id 123 --verbose

# Test individual tools
python scripts/development/debug_ai_service.py --test-tools --verbose

# Help
python scripts/development/debug_ai_service.py --help
```

#### Environment Setup

```bash
# Activate virtual environment
source venv/bin/activate

# Install required packages
pip install langchain-pull-md duckduckgo-search ddgs

# Ensure Django environment is set up
export DJANGO_SETTINGS_MODULE=resource_directory.settings
```

### Debug Output Analysis

The debug tool provides comprehensive output including:

1. **Initialization Logs**: LLM setup, tool creation
2. **Agent Execution**: Tool invocations and responses
3. **AI Response**: Full AI response with tool usage
4. **Parsing Results**: Extracted data and confidence scores
5. **Summary**: Overall verification status

#### Key Debug Indicators

```bash
# ✅ Successful tool usage
Invoking: `web_search` with `{'query': 'Red Bird Mission services'}`
Invoking: `fetch_webpage_tool` with `{'url': 'https://www.redbirdky.org'}`

# ✅ Agent working
> Entering new AgentExecutor chain...

# ✅ PullMdLoader working
https://pull.md:443 "GET /https://www.redbirdky.org HTTP/1.1" 200 8579

# ❌ Missing dependencies
Could not import ddgs python package. Please install it with `pip install -U ddgs`
```

## Common Issues and Solutions

### 1. Missing Dependencies

**Problem**: `Could not import ddgs python package. Please install it with pip install -U ddgs`

**Solution**: Install required packages

```bash
pip install langchain-pull-md duckduckgo-search ddgs
```

### 2. PullMdLoader Rate Limits

**Problem**: PullMdLoader fails with rate limit errors

**Solution**: Respect rate limits (5 req/sec, 20 req/min)

```python
# Add delays between requests if needed
import time
time.sleep(0.2)  # 200ms delay between requests
```

### 3. Web Search Failures

**Problem**: DuckDuckGo search returns no results

**Solution**: Try different search queries or check network connectivity

```python
# Example search queries
"Red Bird Mission services"
"Red Bird Mission Kentucky"
"Red Bird Mission Beverly KY"
```

### 4. Website Access Issues

**Problem**: PullMdLoader fails to fetch website content

**Solution**: Check website accessibility and URL format

```python
# Ensure proper URL format
if not url.startswith('http'):
    url = f"https://{url}"
```

### 5. Agent Not Using Tools

**Problem**: AI generates responses without calling tools

**Cause**: Agent not properly configured with tools

**Solution**: Ensure tools are passed to agent executor

```python
# ✅ Correct implementation
agent = create_openai_tools_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools)
```

### 6. Prompt Template Errors

**Problem**: `Input to ChatPromptTemplate is missing variables {'chat_history'}`

**Cause**: Prompt template includes unused variables

**Solution**: Remove unused placeholders

```python
# ✅ Correct - only required variables
return ChatPromptTemplate.from_messages([
    ("system", "..."),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])
```

## Tool Development Guide

### Current Tool Architecture

```python
def _create_tools(self) -> List[BaseTool]:
    tools = []
    
    # DuckDuckGo Search Tool
    search_tool = DuckDuckGoSearchRun(
        name="web_search",
        description="Search the web for information about community resources..."
    )
    tools.append(search_tool)
    
    # PullMdLoader Tool
    @tool
    def fetch_webpage_tool(url: str) -> str:
        """Fetch and convert a webpage to markdown format for analysis."""
        return fetch_webpage_content(url)
    
    tools.append(fetch_webpage_tool)
    return tools
```

### Tool Best Practices

- **Clear descriptions**: Help AI understand when to use the tool
- **Error handling**: Always handle exceptions gracefully
- **Type hints**: Use proper type annotations
- **Return strings**: Tools should return string results
- **Rate limiting**: Respect service rate limits

## Performance Optimization

### Agent Configuration

```python
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,  # Enable for debugging
    handle_parsing_errors=True,  # Handle tool call errors
    max_iterations=5  # Limit tool usage iterations
)
```

### Tool Timeouts

```python
# Add timeouts to web requests
response = requests.get(url, timeout=10)
```

### Rate Limiting

```python
# Respect PullMdLoader rate limits
# 5 requests per second
# 20 requests per minute
```

## Monitoring and Logging

### Log Levels

```python
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log tool usage
logger.info(f"Tool {tool_name} called with {args}")
```

### Debug Log File

The debug tool saves logs to `ai_debug.log` with timestamps and detailed information.

### Performance Metrics

Track:
- Tool execution time
- Success/failure rates
- AI response quality
- Overall verification accuracy
- Rate limit usage

## API Endpoints

### Manual Verification
```
POST /api/resources/{id}/ai-verify/
```

### Automated Verification
```
POST /api/resources/{id}/ai-auto-verify/
```

### Dashboard
```
GET /resources/{id}/ai-dashboard/
```

## Environment Variables

Required environment variables:

```bash
# AI Service
OPENROUTER_API_KEY=your_api_key_here

# Django Settings
DJANGO_SETTINGS_MODULE=resource_directory.settings
```

## Testing Strategy

### Unit Tests
- Test individual tools
- Test response parsing
- Test report generation

### Integration Tests
- Test full verification pipeline
- Test API endpoints
- Test error handling

### Manual Testing
- Use debug tool with real data
- Test with various resource types
- Verify tool usage patterns

## Troubleshooting Checklist

When debugging AI pipeline issues:

- [ ] Check environment variables
- [ ] Verify Python path setup
- [ ] Test LLM connectivity
- [ ] Check tool definitions
- [ ] Verify agent configuration
- [ ] Test individual tools
- [ ] Check prompt template
- [ ] Review debug logs
- [ ] Test with sample data
- [ ] Verify API endpoints
- [ ] Check rate limits
- [ ] Verify network connectivity

## Common Debug Commands

```bash
# Quick test
python scripts/development/debug_ai_service.py --test-data

# Full verbose test
python scripts/development/debug_ai_service.py --test-data --verbose

# Test specific resource
python scripts/development/debug_ai_service.py --resource-id 123 --verbose

# Test tools only
python scripts/development/debug_ai_service.py --test-tools --verbose

# Check logs
tail -f ai_debug.log

# Django shell test
python manage.py shell
>>> from directory.services.ai.core.review_service import AIReviewService
>>> service = AIReviewService()
>>> result = service.verify_resource_data({...})
```

## Recent Updates (2025-08-30)

### Added Tools
- **DuckDuckGo Search**: Free web search for resource information
- **PullMdLoader**: Web content extraction with JavaScript support

### Removed Tools
- Legacy verification tools (phone, email, address validation)
- Complex web scraping tools
- Service discovery tools

### Benefits of New Architecture
- **Simplified**: Fewer tools, clearer purpose
- **Free Services**: No API costs for core functionality
- **Better Performance**: Cloud-based processing
- **Render Compatible**: Works on free tier hosting
- **JavaScript Support**: Handles modern websites

## Future Improvements

### Planned Enhancements
- Tool result caching
- Better error handling
- Performance monitoring
- Tool usage analytics
- Automated testing
- Model selection optimization

### Known Limitations
- PullMdLoader rate limits (5 req/sec, 20 req/min)
- DuckDuckGo search result variability
- Model response variability
- Tool execution timeouts

---

## Quick Reference

### Key Files
- `review_service.py`: Main AI service
- `debug_ai_service.py`: Debug tool

### Key Commands
- `python scripts/development/debug_ai_service.py --test-data --verbose`
- `python manage.py shell`

### Key Environment Variables
- `OPENROUTER_API_KEY`
- `DJANGO_SETTINGS_MODULE`

### Key Debug Indicators
- "> Entering new AgentExecutor chain..."
- "Invoking: `web_search` with `args`"
- "Invoking: `fetch_webpage_tool` with `args`"
- PullMdLoader response codes
- Final AI response with pipe-separated data

### Required Packages
```bash
pip install langchain-pull-md duckduckgo-search ddgs
```
