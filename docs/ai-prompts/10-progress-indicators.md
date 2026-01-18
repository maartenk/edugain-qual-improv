# AI Implementation Prompt: Progress Indicators for Long Operations

**Feature ID**: 1.10 from ROADMAP.md
**Priority**: MEDIUM
**Effort**: 2 days
**Type**: Infrastructure (UX)

## Objective

Add progress bars and status indicators for long-running operations (metadata download, URL validation) to improve user experience and reduce perceived latency.

## Context

**Current State**:
- Long operations show no progress feedback
- Users experience "black box" waiting periods
- No indication of completion percentage or ETA
- Terminal appears frozen during operations

**Current UX** (Poor):
```
Downloading metadata from https://mds.edugain.org/edugain-v2.xml...
[... 2 minutes of silence ...]
Downloaded 52,341,234 bytes
```

**Improved UX** (With Progress):
```
Downloading metadata: [████████████░░░░░░░░] 65% (34.2 MB / 52.3 MB) ETA: 45s
Validating URLs: [████████████████████] 1,823/2,341 (78%) ETA: 2m 15s
```

**Problem**:
- Users assume tool has hung or crashed
- No feedback during 2-10 minute validation runs
- Can't estimate remaining time
- Poor UX compared to modern CLI tools

## Requirements

### Core Functionality

1. **Metadata Download Progress**:
   - Show download progress bar with percentage
   - Display bytes downloaded / total bytes
   - Show current download speed (KB/s or MB/s)
   - Display estimated time remaining

2. **URL Validation Progress**:
   - Show validation progress: N/Total URLs validated
   - Display percentage complete
   - Show current rate (URLs/second)
   - Display estimated time remaining
   - Optional: Show current URL being validated

3. **Progress Bar Features**:
   - Unicode bar characters: `█░` or ASCII fallback `#-`
   - Auto-detect terminal width for responsive layout
   - Color support (green for complete, blue for in-progress)
   - Spinner animation for indeterminate operations

4. **CLI Flags**:
   ```bash
   --quiet              # Suppress all progress output
   --no-progress        # Disable progress bars (keep text status)
   --progress-style     # ascii|unicode|minimal
   ```

5. **Smart Detection**:
   - Auto-disable progress bars if stderr is not a TTY (CI/CD mode)
   - Auto-disable in `--quiet` mode
   - Fallback to simple status messages if terminal doesn't support ANSI

### Progress Bar Styles

**Unicode Style** (default):
```
Downloading metadata: [████████████░░░░░░░░] 65% (34.2 MB / 52.3 MB) ETA: 45s
```

**ASCII Style** (fallback):
```
Downloading metadata: [############--------] 65% (34.2 MB / 52.3 MB) ETA: 45s
```

**Minimal Style** (low-bandwidth):
```
Downloading: 65% complete (34.2/52.3 MB)
```

**CI/CD Mode** (non-interactive):
```
Downloading metadata... 34.2 MB / 52.3 MB (65%)
Validating URLs... 1823/2341 (78%)
```

### Implementation Details

**Files to Modify**:

1. **`src/edugain_analysis/core/metadata.py`**:
   - Add progress tracking to `get_metadata()` download
   - Use streaming download with progress callbacks

2. **`src/edugain_analysis/core/validation.py`**:
   - Add progress bar to parallel URL validation
   - Track completed/total URLs

3. **`src/edugain_analysis/cli/main.py`**:
   - Add progress-related CLI flags
   - Detect TTY mode
   - Configure progress bar settings

4. **New Module** (optional): `src/edugain_analysis/utils/progress.py`
   - Progress bar utility functions
   - Terminal detection
   - Style configuration

**Dependencies**:
- **`tqdm`**: Popular Python progress bar library (pip install tqdm)
  - Or implement simple custom progress bar (no dependencies)

**Edge Cases**:
- Unknown total size: Use indeterminate spinner
- Very fast operations (< 2s): Don't show progress bar
- Multiple concurrent progress bars: Stack vertically
- Terminal resize: Redraw progress bar
- SIGINT (Ctrl+C): Clean up progress bar before exit

## Acceptance Criteria

### Functional Requirements
- [ ] Progress bar shown for metadata downloads > 5 MB
- [ ] Progress bar shown for URL validations > 100 URLs
- [ ] Percentage, current/total, and ETA displayed
- [ ] Auto-disable in non-TTY environments
- [ ] `--quiet` suppresses all progress output
- [ ] `--no-progress` disables progress bars
- [ ] Unicode and ASCII styles supported
- [ ] Clean progress bar cleanup on completion or error

### Quality Requirements
- [ ] Progress bar doesn't interfere with output formatting
- [ ] Performance overhead < 1% (progress tracking is fast)
- [ ] Accurate ETA calculations (moving average)
- [ ] No flickering or redraw issues
- [ ] Graceful degradation in unsupported terminals

### Testing Requirements
- [ ] Test progress bar in interactive mode
- [ ] Test auto-disable in non-TTY mode
- [ ] Test `--quiet` flag suppresses progress
- [ ] Test progress bar cleanup on errors
- [ ] Test with various terminal widths
- [ ] Test Unicode and ASCII styles

## Testing Strategy

**Manual Testing** (Interactive):
```bash
# Test metadata download progress
edugain-analyze

# Test URL validation progress
edugain-analyze --validate

# Test quiet mode (no progress)
edugain-analyze --quiet

# Test ASCII style
edugain-analyze --progress-style ascii
```

**Automated Testing** (Non-interactive):
```python
def test_progress_disabled_in_non_tty():
    """Test progress bars disabled in non-TTY mode."""
    result = subprocess.run(
        ["edugain-analyze"],
        capture_output=True,
        text=True
    )
    # Should not contain progress bar characters
    assert "█" not in result.stderr
    assert "░" not in result.stderr

def test_quiet_suppresses_progress():
    """Test --quiet flag suppresses progress."""
    result = subprocess.run(
        ["edugain-analyze", "--quiet"],
        capture_output=True,
        text=True
    )
    # Should have minimal output
    assert len(result.stderr) < 100  # Very little stderr
```

## Implementation Guidance

### Option 1: Using tqdm Library (Recommended)

```python
# Add to pyproject.toml
[project.optional-dependencies]
progress = ["tqdm>=4.65.0"]

# src/edugain_analysis/core/metadata.py

import sys
from tqdm import tqdm

def get_metadata(
    url: str,
    show_progress: bool = True
) -> str:
    """
    Download metadata with progress bar.

    Args:
        url: Metadata URL
        show_progress: Show progress bar (auto-detect if None)

    Returns:
        Metadata XML content
    """
    # Auto-detect TTY mode
    if show_progress is None:
        show_progress = sys.stderr.isatty()

    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))

    # Download with progress bar
    if show_progress and total_size > 0:
        progress_bar = tqdm(
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
            desc="Downloading metadata",
            file=sys.stderr
        )

        chunks = []
        for chunk in response.iter_content(chunk_size=8192):
            chunks.append(chunk)
            progress_bar.update(len(chunk))

        progress_bar.close()
        return b''.join(chunks).decode('utf-8')
    else:
        # No progress bar
        return response.text
```

### Option 2: Custom Progress Bar (No Dependencies)

```python
# src/edugain_analysis/utils/progress.py

import sys
import time
from typing import Optional

class ProgressBar:
    """Simple progress bar for terminal output."""

    def __init__(
        self,
        total: int,
        description: str = "",
        width: int = 40,
        style: str = "unicode"
    ):
        """
        Initialize progress bar.

        Args:
            total: Total number of items
            description: Operation description
            width: Bar width in characters
            style: Bar style (unicode/ascii/minimal)
        """
        self.total = total
        self.current = 0
        self.description = description
        self.width = width
        self.style = style
        self.start_time = time.time()

        # Characters for different styles
        self.chars = {
            "unicode": {"filled": "█", "empty": "░"},
            "ascii": {"filled": "#", "empty": "-"},
            "minimal": {"filled": "=", "empty": " "}
        }

        # Detect if output is TTY
        self.enabled = sys.stderr.isatty()

    def update(self, n: int = 1):
        """Update progress by n items."""
        self.current = min(self.current + n, self.total)
        if self.enabled:
            self._draw()

    def _draw(self):
        """Draw progress bar to stderr."""
        if self.total == 0:
            return

        # Calculate percentage
        percent = int(100 * self.current / self.total)

        # Calculate bar
        filled = int(self.width * self.current / self.total)
        bar_chars = self.chars[self.style]
        bar = (bar_chars["filled"] * filled +
               bar_chars["empty"] * (self.width - filled))

        # Calculate ETA
        elapsed = time.time() - self.start_time
        if self.current > 0:
            rate = self.current / elapsed
            remaining = (self.total - self.current) / rate
            eta = self._format_time(remaining)
        else:
            eta = "?"

        # Build progress line
        line = f"\r{self.description}: [{bar}] {percent}% "
        line += f"({self.current}/{self.total}) ETA: {eta}"

        # Write to stderr
        sys.stderr.write(line)
        sys.stderr.flush()

    def _format_time(self, seconds: float) -> str:
        """Format seconds as human-readable time."""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}h {minutes}m"

    def close(self):
        """Close progress bar and move to next line."""
        if self.enabled:
            sys.stderr.write("\n")
            sys.stderr.flush()

# Usage in metadata.py
def get_metadata(url: str, show_progress: bool = True) -> str:
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))

    if show_progress and total_size > 0:
        progress = ProgressBar(
            total=total_size,
            description="Downloading metadata",
            style="unicode"
        )

        chunks = []
        for chunk in response.iter_content(chunk_size=8192):
            chunks.append(chunk)
            progress.update(len(chunk))

        progress.close()
        return b''.join(chunks).decode('utf-8')
    else:
        return response.text
```

### Step 3: URL Validation Progress

```python
# src/edugain_analysis/core/validation.py

def validate_urls_parallel(
    urls: list[str],
    threads: int = 10,
    show_progress: bool = True
) -> dict:
    """
    Validate URLs in parallel with progress bar.

    Args:
        urls: List of URLs to validate
        threads: Number of parallel threads
        show_progress: Show progress bar

    Returns:
        Dictionary of validation results
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    results = {}

    # Auto-detect TTY
    if show_progress is None:
        show_progress = sys.stderr.isatty()

    # Create progress bar
    if show_progress:
        # Option 1: tqdm
        from tqdm import tqdm
        progress = tqdm(total=len(urls), desc="Validating URLs", file=sys.stderr)

        # Option 2: Custom
        # progress = ProgressBar(len(urls), "Validating URLs")

    with ThreadPoolExecutor(max_workers=threads) as executor:
        # Submit all tasks
        future_to_url = {
            executor.submit(validate_privacy_url, url): url
            for url in urls
        }

        # Collect results as they complete
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                result = future.result()
                results[url] = result
                if show_progress:
                    progress.update(1)
            except Exception as e:
                results[url] = {"error": str(e)}
                if show_progress:
                    progress.update(1)

    if show_progress:
        progress.close()

    return results
```

### Step 4: CLI Integration

```python
# src/edugain_analysis/cli/main.py

parser.add_argument(
    "--quiet",
    action="store_true",
    help="Suppress progress indicators and non-essential output"
)
parser.add_argument(
    "--no-progress",
    action="store_true",
    help="Disable progress bars (keep status messages)"
)
parser.add_argument(
    "--progress-style",
    choices=["unicode", "ascii", "minimal"],
    default="unicode",
    help="Progress bar style (default: unicode)"
)

def main():
    args = parser.parse_args()

    # Determine if we should show progress
    show_progress = not args.quiet and not args.no_progress

    # Set progress style globally (if using custom implementation)
    if hasattr(sys, 'progress_style'):
        sys.progress_style = args.progress_style

    # Download metadata with progress
    xml_content = get_metadata(
        EDUGAIN_METADATA_URL,
        show_progress=show_progress
    )

    # ... analysis ...

    # Validate URLs with progress
    if args.validate:
        validation_results = validate_urls_parallel(
            privacy_urls,
            threads=URL_VALIDATION_THREADS,
            show_progress=show_progress
        )
```

## Success Metrics

- Users report improved experience with long operations
- No complaints about "frozen" tool during downloads
- Progress bars work correctly in 95%+ of terminals
- Performance overhead < 1%
- Clean output in CI/CD pipelines (non-TTY)
- All tests pass with progress features

## References

- tqdm library: https://github.com/tqdm/tqdm
- Python TTY detection: `sys.stderr.isatty()`
- ANSI escape codes: https://en.wikipedia.org/wiki/ANSI_escape_code
- Similar tools: wget, curl, pip, npm (all have progress bars)
