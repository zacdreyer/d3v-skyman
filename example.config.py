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

# APP Configuration
app = {
    "name": '',
    "debug": 1  # Switch to 0 on production deployments
}

# Module Configuration
module = {
    "active": {  # Comma seperated activated dev-skyman modules
        "app",
        "cli"
    }
}

# Encryption Configuration
# Generate with https://www.allkeysgenerator.com/Random/Security-Encryption-Key-Generator.aspx
encryption = {
    'iv': '',  # Should be 16 characters (16 bytes / 128 bit)
    'key': '',  # Should be 32 characters (32 bytes / 256 bit)
}

# Daemon Configuration
daemon = {
    'port': 25120,  # Port must be 0-65535.
    'password': '',  # Should be 18 characters minimum
    'whitelist': {  # Comma seperated whitelisted IPs which are allowed to access dev-skyman
        '127.0.0.1'
    }
}
