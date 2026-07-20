#
#  @author     Zac Dreyer
#  @license    LICENSE
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

import os
import shlex
import subprocess

from config_loader import load_config

config = load_config()


DISALLOWED_TOKENS = {';', '|', '&', '>', '<', '`', '$'}
MAX_COMMAND_LENGTH = 2048


def execute_stream(cmd, chunk_size=1024):
    if not cmd or not cmd.strip():
        raise ValueError('Command cannot be empty')

    cleaned_cmd = cmd.strip()
    if len(cleaned_cmd) > MAX_COMMAND_LENGTH:
        raise ValueError('Command exceeds maximum length')
    if any(ord(char) < 32 for char in cleaned_cmd):
        raise ValueError('Command contains control characters')

    try:
        argv = shlex.split(cleaned_cmd, posix=True)
    except ValueError as exc:
        raise ValueError('Command contains invalid quoting') from exc

    if not argv:
        raise ValueError('Command cannot be empty')

    if any(token in DISALLOWED_TOKENS or any(char in token for char in DISALLOWED_TOKENS) for token in argv):
        raise ValueError('Command contains disallowed shell metacharacters')

    env = os.environ.copy()
    env['PYTHONUNBUFFERED'] = '1'
    process = subprocess.Popen(
        argv,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        text=True,
        encoding='utf-8',
        errors='replace',
        env=env
    )

    try:
        while True:
            chunk = process.stdout.read(chunk_size)
            if not chunk:
                break
            yield chunk
        process.wait()
    finally:
        if process.stdout:
            process.stdout.close()


def execute(cmd):
    output = ''.join(execute_stream(cmd))
    if config.app['debug'] == 1:
        print(output)
    return output
