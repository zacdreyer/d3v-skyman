#
#  @author     Zac Dreyer [D3V.Digital]
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


from modules import cli


def stop():
    result = cli.execute("ps -ef | grep 'd3vskyman.py' | awk '{print $2}'")
    result = result.split('\n')
    cli.execute("kill -9 " + result[0])
    return True


def update(path):
    result = cli.execute('cd ' + path + ';git pull -v;')
    stop()
    return True
