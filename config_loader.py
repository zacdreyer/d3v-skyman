import importlib.util
import sys
from pathlib import Path


def load_config():
    if 'config' in sys.modules:
        module = sys.modules['config']
        validate_config(module)
        return module

    repo_root = Path(__file__).resolve().parent
    for candidate in [repo_root / 'config.py', repo_root / 'example.config.py']:
        if candidate.exists():
            spec = importlib.util.spec_from_file_location('config', candidate)
            module = importlib.util.module_from_spec(spec)
            sys.modules['config'] = module
            spec.loader.exec_module(module)
            validate_config(module)
            return module

    raise FileNotFoundError('No config.py found. Copy example.config.py to config.py and fill in the values.')


def validate_config(module):
    app_config = getattr(module, 'app', None)
    if not isinstance(app_config, dict):
        raise ValueError('app configuration must be a dict')
    if 'debug' not in app_config:
        raise ValueError('app.debug is required')

    daemon_config = getattr(module, 'daemon', None)
    if not isinstance(daemon_config, dict):
        raise ValueError('daemon configuration must be a dict')
    if 'password' not in daemon_config or not daemon_config['password']:
        raise ValueError('daemon.password must be set')
    if len(daemon_config['password']) < 18:
        raise ValueError('daemon.password must be at least 18 characters')
    if 'port' not in daemon_config:
        raise ValueError('daemon.port is required')
    if not isinstance(daemon_config['port'], int) or not 0 <= daemon_config['port'] <= 65535:
        raise ValueError('daemon.port must be between 0 and 65535')
    if 'whitelist' not in daemon_config or not daemon_config['whitelist']:
        raise ValueError('daemon.whitelist must contain at least one entry')

    encryption_config = getattr(module, 'encryption', None)
    if not isinstance(encryption_config, dict):
        raise ValueError('encryption configuration must be a dict')
    if 'key' not in encryption_config or not encryption_config['key']:
        raise ValueError('encryption.key must be set')
    if 'iv' not in encryption_config or not encryption_config['iv']:
        raise ValueError('encryption.iv must be set')
