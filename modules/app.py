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

from config_loader import load_config
from modules import cli

config = load_config()


def stop():
    result = cli.execute("ps -ef | grep '[d]3vskyman.py' | awk '{print $2}'")
    pids = [line.strip() for line in result.splitlines() if line.strip().isdigit()]
    if not pids:
        return False

    for pid in pids:
        cli.execute("kill -TERM " + pid)
    return True


def update(path):
    safe_path = os.path.realpath(path)
    if not safe_path or not os.path.isdir(safe_path):
        raise ValueError('Invalid update path')

    cli.execute('cd ' + shlex.quote(safe_path) + ';git pull -v;')
    stop()
    return True
