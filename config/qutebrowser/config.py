config.load_autoconfig() 
import omarchy.draw
omarchy.draw.apply(c)


# --- Editor ---
c.editor.command = ['nvim', '{}']

# --- Downloads ---
c.downloads.location.directory = '~/Downloads'
c.downloads.location.prompt = True
c.downloads.remove_finished = 5000

# --- Home / startup ---
c.url.start_pages = ['https://www.google.com/']
c.url.default_page = 'https://www.google.com/'

# --- Fonts ---
c.fonts.default_family = ['JetBrains Mono', 'monospace']
c.fonts.default_size = '12pt'
c.fonts.web.family.standard = 'Cantarell'
c.fonts.web.family.serif = 'Cantarell'
c.fonts.web.family.sans_serif = 'Cantarell'

# --- Tabs ---
c.tabs.position = 'top'
c.tabs.show = 'multiple'
c.tabs.title.format = '{index}: {current_title}'
c.tabs.title.format_pinned = '{index}'

# --- Search engines ---
c.url.searchengines = {
    'DEFAULT': 'https://www.google.com/search?q={}',
    'ppx':    'https://www.perplexity.ai/search?q={}',
    'yt':     'https://www.youtube.com/results?search_query={}',
    'gh':     'https://github.com/search?q={}',
    'w':      'https://en.wikipedia.org/wiki/Special:Search?search={}',
    'r':      'https://www.reddit.com/search/?q={}',
    'a':      'https://wiki.archlinux.org/index.php?search={}',
    'wa':     'https://www.wolframalpha.com/input?i={}',
    'id':     'https://www.google.com/search?q={}&hl=id',
}

# --- Keybindings ---
config.bind('J', 'tab-next')
config.bind('K', 'tab-prev')
config.bind('gJ', 'tab-move +')
config.bind('gK', 'tab-move -')
config.bind('H', 'back')
config.bind('L', 'forward')
config.bind('x', 'tab-close')
config.bind('X', 'undo')
config.bind('d', 'hint links spawn mpv --force-window=yes {url}')
config.bind('gm', 'hint links spawn mpv {url}')
config.bind(',p', 'hint links spawn yt-dlp -o ~/Videos/%(title)s.%(ext)s {url}')
config.bind('yy', 'yank url')
config.bind('yp', 'yank pretty-url')
config.bind(';y', 'hint links yank')
config.bind('gi', 'hint inputs')
config.bind('gb', 'tab-take -f')
config.bind('gr', 'reload -f')
config.bind(',t', 'spawn --userscript extract-text')

# --- Adblock ---
c.content.blocking.method = 'both'
c.content.blocking.adblock.lists = [
    'https://easylist.to/easylist/easylist.txt',
    'https://easylist.to/easylist/easyprivacy.txt',
    'https://secure.fanboy.co.nz/fanboy-annoyance.txt',
    'https://raw.githubusercontent.com/uBlockOrigin/uAssets/master/filters/filters.txt',
]

# --- Privacy ---
c.content.cookies.accept = 'no-3rdparty'
c.content.cookies.store = True
c.content.headers.user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) QtWebEngine/6.11.1 Chrome/126.0.0.0 Safari/537.36'
c.content.webgl = False
c.content.autoplay = False
c.content.notifications.enabled = False
c.content.pdfjs = True
c.content.dns_prefetch = False
c.content.local_content_can_access_remote_urls = False
