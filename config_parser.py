from ets.ets_small_config_parser import ConfigParser as Parser
from inspect import getsourcefile
from os.path import dirname, normpath
from os import chdir

PATH = normpath(dirname(getsourcefile(lambda: 0)))
chdir(PATH)

CONFIG_FILE = 'bots_banner.conf'

config = Parser(config_file=CONFIG_FILE)

SLEEP_TIME = config.get_option('main', 'sleep_time')
OFFER_THRESHOLD = config.get_option('main', 'offer_threshold')
CACHE_TIMEOUT = config.get_option('main', 'cache_timeout')

LOG_FILE = config.get_option('log', 'log_file', string=True)


