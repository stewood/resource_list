"""
Cursor Agent Service for AI-powered operations.

This service handles interactions with the Cursor Agent for AI-powered
website discovery and other automated tasks.
"""

import json
import subprocess
import sys
from typing import Any, Dict, List, Optional

from django.utils import timezone

from directory.models.verification_models import CursorAgentResult
from directory.config.verification_config import ProcessConfig, default_process_config

# Import the cursor parser
try:
    import os
    # Add the project root to the path for importing test modules
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
    from test_cursor_parser import parse_cursor_agent_output
    CURSOR_PARSER_AVAILABLE = True
except ImportError:
    CURSOR_PARSER_AVAILABLE = False


class CursorAgentService:
    """
    Service for Cursor Agent operations.

    This service encapsulates the logic for calling Cursor Agent, handling
    streaming responses, and managing process lifecycle.
    """

    def __init__(self, config: Optional[ProcessConfig] = None):
        """
        Initialize the Cursor Agent service.

        Args:
            config: Configuration for the service
        """
        self.config = config or default_process_config

    def call_cursor_agent(self, prompt: str, timeout_seconds: int = 180) -> CursorAgentResult:
        """
        Call Cursor Agent with a prompt and return the result.

        Args:
            prompt: The prompt to send to Cursor Agent
            timeout_seconds: Maximum time to wait for response

        Returns:
            CursorAgentResult with the operation results
        """
        try:
            if CURSOR_PARSER_AVAILABLE:
                return self._call_with_parser(prompt, timeout_seconds)
            else:
                return self._call_with_subprocess(prompt, timeout_seconds)

        except Exception as e:
            return CursorAgentResult(
                success=False,
                error=f"Failed to call Cursor Agent: {str(e)}"
            )

    def _call_with_parser(self, prompt: str, timeout_seconds: int) -> CursorAgentResult:
        """
        Call Cursor Agent using the new parser.

        Args:
            prompt: The prompt to send
            timeout_seconds: Timeout for the operation

        Returns:
            CursorAgentResult
        """
        result = parse_cursor_agent_output(
            prompt=prompt,
            timeout_seconds=timeout_seconds,
            verbose=False,
            show_tool_calls=False,
            show_system_messages=False
        )

        return CursorAgentResult(
            success=result['success'],
            error=result.get('error'),
            full_text=result.get('full_text', ''),
            duration_ms=result.get('duration_ms', 0),
            tool_calls=result.get('tool_calls', []),
            parsed_data=self._parse_result_data(result.get('full_text', ''))
        )

    def _call_with_subprocess(self, prompt: str, timeout_seconds: int) -> CursorAgentResult:
        """
        Call Cursor Agent using subprocess (fallback method).

        Args:
            prompt: The prompt to send
            timeout_seconds: Timeout for the operation

        Returns:
            CursorAgentResult
        """
        try:
            process = subprocess.Popen(
                ['cursor-agent', '--force', '--print', '-f', '--model', 'auto', prompt],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            assistant_content = []
            raw_output = []
            json_complete = False
            start_time = timezone.now()
            elapsed_time = 0
            current_response = ""
            tool_calls = []

            # Stream output and parse JSON messages
            try:
                for line in process.stdout:
                    # Check timeout
                    elapsed_time = (timezone.now() - start_time).total_seconds()
                    if elapsed_time > timeout_seconds:
                        process.terminate()
                        break

                    raw_output.append(line)

                    # Try to parse each line as JSON
                    try:
                        if line.strip().startswith('{') and line.strip().endswith('}'):
                            message = json.loads(line.strip())

                            # Handle assistant content (streaming text)
                            if message.get('type') == 'assistant' and 'message' in message:
                                content = message['message'].get('content', [])
                                for item in content:
                                    if isinstance(item, dict) and 'text' in item:
                                        text = item['text']
                                        assistant_content.append(text)
                                        current_response += text

                            # Handle tool calls
                            elif message.get('type') == 'tool_call':
                                if message.get('subtype') == 'started':
                                    tool_call = message.get('tool_call', {})
                                    mcp_call = tool_call.get('mcpToolCall', {})
                                    tool_name = mcp_call.get('args', {}).get('toolName', 'unknown')
                                    tool_calls.append(tool_name)

                            # Check for completion
                            elif message.get('type') == 'result' and message.get('subtype') == 'success':
                                json_complete = True
                                process.terminate()
                                break

                    except json.JSONDecodeError:
                        # Not a JSON line, continue processing
                        pass

                    # Check for the <|END|> marker
                    if '<|END|>' in line:
                        json_complete = True
                        process.terminate()
                        break

                    if json_complete:
                        break

            except Exception as stream_error:
                return CursorAgentResult(
                    success=False,
                    error=f"Error during streaming: {str(stream_error)}",
                    full_text=''.join(raw_output),
                    duration_ms=int((timezone.now() - start_time).total_seconds() * 1000)
                )

            # Wait for process to finish
            try:
                process.wait(timeout=self.config.subprocess_timeout)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

            # Return the result
            if assistant_content:
                return CursorAgentResult(
                    success=json_complete,
                    full_text=''.join(assistant_content).strip(),
                    duration_ms=int((timezone.now() - start_time).total_seconds() * 1000),
                    tool_calls=tool_calls,
                    parsed_data=self._parse_result_data(''.join(assistant_content))
                )
            else:
                return CursorAgentResult(
                    success=False,
                    error="No assistant content received",
                    full_text=''.join(raw_output),
                    duration_ms=int((timezone.now() - start_time).total_seconds() * 1000)
                )

        except Exception as e:
            return CursorAgentResult(
                success=False,
                error=f"Subprocess error: {str(e)}"
            )

    def _parse_result_data(self, full_text: str) -> Optional[Dict[str, Any]]:
        """
        Parse the result data from Cursor Agent output.

        Args:
            full_text: Full text output from Cursor Agent

        Returns:
            Parsed data dictionary or None
        """
        try:
            # Try to extract JSON from the response
            json_start = full_text.find('{')
            json_end = full_text.rfind('}') + 1

            if json_start == -1 or json_end == 0:
                return None

            json_text = full_text[json_start:json_end]
            return json.loads(json_text)

        except (json.JSONDecodeError, ValueError):
            return None

    def validate_cursor_agent_setup(self) -> Dict[str, Any]:
        """
        Validate that Cursor Agent is properly set up and accessible.

        Returns:
            Validation result dictionary
        """
        try:
            # Try to run cursor-agent --help
            result = subprocess.run(
                ['cursor-agent', '--help'],
                capture_output=True,
                text=True,
                timeout=10
            )

            return {
                "available": result.returncode == 0,
                "version_info": result.stdout if result.returncode == 0 else None,
                "error": result.stderr if result.returncode != 0 else None
            }

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            return {
                "available": False,
                "error": str(e)
            }

