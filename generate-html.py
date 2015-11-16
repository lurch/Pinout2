#!/usr/bin/env python
import markdown
import unicodedata
import re
import os
import sys
import pinout
import markjaml
import urlmapper

reload(sys)
sys.setdefaultencoding('utf8')


def cssify(value):
    value = slugify(value);
    if value[0] == '3' or value[0] == '5':
        value = 'pow' + value

    return value


def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    """
    value = unicode(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub('[^\w\s-]', '', value).strip().lower()
    return re.sub('[-\s]+', '_', value)


def load_overlay(overlay):
    try:
        data = markjaml.load('src/{}/overlay/{}.md'.format(lang, overlay))

        loaded = data['data']
        loaded['long_description'] = data['html']
        if 'pin' in loaded:
            real_pins = dict()
            for pin in loaded['pin']:
                real_pins[str(pin)] = loaded['pin'][pin]
            del loaded['pin']
            loaded['pin'] = real_pins
    except IOError:
        return None

    details = []

    if 'type' not in loaded:
    	loaded['type'] = 'addon'

    if 'manufacturer' in loaded:
        details.append('* ' + strings['made_by'].format(manufacturer=loaded['manufacturer']))

    if 'pincount' in loaded:
        pincount = int(loaded['pincount'])
        if pincount == 40:
            details.append('* ' + strings['type_hat'])
        elif pincount == 26:
            details.append('* ' + strings['type_classic'])
        else:
            details.append('* ' + strings['pin_header'].format(pincount))

    if 'pin' in loaded:
        uses_5v = False
        uses_3v = False
        uses = 0
        for pin in loaded['pin']:
            pin = str(pin)
            if pin.startswith('bcm'):
                pin = pinout.bcm_to_physical(pin[3:])

            if pin in pinout.pins:
                actual_pin = pinout.pins[pin]

                if actual_pin['type'] in ['+3v3', '+5v', 'GND']:
                    if actual_pin['type'] == '+3v3':
                        uses_3v = True
                    if actual_pin['type'] == '+5v':
                        uses_5v = True
                else:
                    uses += 1

        if uses > 0:
            details.append(strings['uses_n_gpio_pins'].format(uses))

        if '3' in loaded['pin'] and '5' in loaded['pin']:
            pin_3 = loaded['pin']['3']
            pin_5 = loaded['pin']['5']
            if 'mode' in pin_3 and 'mode' in pin_5:
                if pin_3['mode'] == 'i2c' and pin_5['mode'] == 'i2c':
                    details.append('* ' + strings['uses_i2c'])

    if 'url' in loaded:
        details.append('* [{text}]({url})'.format(text=strings['more_information'], url=loaded['url']))

    if 'github' in loaded:
        details.append('* [{text}]({url})'.format(text=strings['github_repository'], url=loaded['github']))

    if 'buy' in loaded:
        details.append('* [{text}]({url})'.format(text=strings['buy_now'], url=loaded['buy']))

    if loaded['type'] != 'info':
    	loaded['long_description'] = '{}\n{}'.format(loaded['long_description'], markdown.markdown('\n'.join(details)))

    if 'page_url' not in loaded:
        loaded['page_url'] = slugify(loaded['name'])

    loaded['rendered_html'] = render_overlay_page(loaded)
    loaded['src'] = overlay
    pages[loaded['page_url']] = loaded
    navs[loaded['page_url']] = render_nav(loaded['page_url'], overlay=loaded)
    select_overlays.append((loaded['page_url'], loaded['name']))
    return loaded


def load_md(filename):
    filename = 'src/{}/{}'.format(lang, filename)
    try:
        html = markdown.markdown(open(filename).read(), extensions=['fenced_code'])

        return html
    except IOError:
        print('Unable to load markdown from {}'.format(filename))
        return ''


def render_pin_text(pin_num, pin_url, pin_name, pin_functions, pin_subtext):
    return '<article class="{pin_url}"><h1>{pin_name}</h1>{pin_functions}{pin_subtext}{pin_text}</article>'.format(
        pin_url=pin_url,
        pin_name=pin_name,
        pin_functions=pin_functions,
        pin_subtext=pin_subtext,
        pin_text=load_md('pin/pin-{}.md'.format(pin_num)))


def render_overlay_page(overlay):
    if overlay is None:
        return ''
    return '<article class="page_{}">{}</article>'.format(slugify(overlay['name']), overlay['long_description'])


def render_alternate(handle, name):
    handle = slugify(handle.lower())
    return '<span class="alternate legend_{}">{}</span>'.format(handle, name)


def render_pin_page(pin_num):
    pin = pinout.pins[str(pin_num)]
    pin_url = pin['name']

    if pin_url == 'Ground':
        return None, None, None

    pin_text_name = pin['name']

    pin_subtext = []

    pin_subtext.append(strings['physical_pin_n'].format(pin_num))

    if 'scheme' in pin:
        if 'bcm' in pin['scheme']:
            bcm = pin['scheme']['bcm']
            pin_url = 'gpio{}'.format(bcm)

            pin_text_name = 'BCM {}'.format(bcm)

            if pin['name'] != '':
                pin_subname_text = '({})'.format(pin['name'])
            pin_subtext.append('BCM pin {}'.format(bcm))
        if 'wiringpi' in pin['scheme']:
            wiringpi = pin['scheme']['wiringpi']
            pin_subtext.append('Wiring Pi pin {}'.format(wiringpi))
        if 'bcmAlt' in pin['scheme']:
            bcmAlt = pin['scheme']['bcmAlt']
            pin_subtext.append(strings['bcm_pin_rev1_pi'].format(bcmAlt))

    if 'description' in pin:
        pin_text_name = '{} ({})'.format(pin_text_name, pin['description'])

    fn_headings = []
    fn_functions = []
    pin_functions = ''
    if 'functions' in pin:
        for x in range(6):
            fn_headings.append('Alt' + str(x))

            function = ''
            if 'alt' + str(x) in pin['functions']:
                function = pin['functions']['alt' + str(x)]

            fn_functions.append(function)

        pin_functions = '''<table class="pin-functions">
		<thead>
			<tr>
				<th>{headings}</th>
			</tr>
		</thead>
		<tbody>
			<tr>
				<td>{functions}</td>
			</tr>
		</tbody>
		</table>'''.format(headings='</th><th>'.join(fn_headings), functions='</td><td>'.join(fn_functions))

    pin_url = slugify('pin{}_{}'.format(pin_num, pin_url))

    pin_text = render_pin_text(
        pin_num,
        pin_url,
        pin_text_name,
        pin_functions,
        '<ul><li>{}</li></ul>'.format('</li><li>'.join(pin_subtext))
    )
    # if pin_text != None:
    return pin_url, pin_text, pin_text_name  # pages[pin_url] = pin_text


def render_pin(pin_num, selected_url, overlay=None):
    pin = pinout.pins[str(pin_num)]

    pin_type = list([x.strip() for x in pin['type'].lower().split('/')])
    pin_url = pin['name']
    pin_name = pin['name']
    pin_used = False
    pin_link_title = []
    bcm_pin = None
    if 'scheme' in pin:
        if 'bcm' in pin['scheme']:
            bcm_pin = 'bcm' + str(pin['scheme']['bcm'])

    if overlay is not None and (pin_num in overlay['pin'] or str(pin_num) in overlay['pin'] or bcm_pin in overlay['pin']):

        if pin_num in overlay['pin']:
            overlay_pin = overlay['pin'][pin_num]
        elif str(pin_num) in overlay['pin']:
            overlay_pin = overlay['pin'][str(pin_num)]
        else:
            overlay_pin = overlay['pin'][bcm_pin]

        if overlay_pin is None:
            overlay_pin = {}

        pin_used = True
        # print(overlay)
        if 'name' in overlay_pin:
            pin_name = overlay_pin['name']

        if 'description' in overlay_pin:
            pin_link_title.append(overlay_pin['description'])

    if 'scheme' in pin:
        if 'bcm' in pin['scheme']:
            bcm = pin['scheme']['bcm']
            pin_subname = ''
            # pin_subname_text = ''
            # if pin_url == '':
            pin_url = 'gpio{}'.format(bcm)
            if pin_name != '':  # pin['name'] != '':
                pin_subname = '<small>({})</small>'.format(pin_name)  # pin['name'])
            pin_name = 'BCM {} {}'.format(bcm, pin_subname)
        if 'wiringpi' in pin['scheme']:
            wiringpi = pin['scheme']['wiringpi']
            pin_link_title.append(strings['wiring_pi_pin'].format(wiringpi))

    pin_url = base_url + slugify('pin{}_{}'.format(pin_num, pin_url))

    if pin['type'] in pinout.get_setting('urls'):
        pin_url = base_url + pinout.get_setting('urls')[pin['type']]

    selected = ''

    if base_url + selected_url == pin_url:
        selected = ' active'
    if pin_used:
        selected += ' overlay-pin'

    pin_url = pin_url + url_suffix

    return '<li class="pin{pin_num} {pin_type}{pin_selected}"><a href="{pin_url}" title="{pin_title}"><span class="default"><span class="phys">{pin_num}</span> {pin_name}</span><span class="pin"></span></a></li>\n'.format(
        pin_num=pin_num,
        pin_type=' '.join(map(cssify, pin_type)),
        pin_selected=selected,
        pin_url=pin_url,
        pin_title=', '.join(pin_link_title),
        pin_name=pin_name,
        langcode=lang
    )


def render_nav(url, overlay=None):
    html_odd = ''
    html_even = ''
    for odd in range(1, len(pinout.pins), 2):
        html_odd += render_pin(odd, url, overlay)
        html_even += render_pin(odd + 1, url, overlay)

    return '''<ul class="bottom">
{}</ul>
<ul class="top">
{}</ul>'''.format(html_odd, html_even)


def get_hreflang_urls(src):
    hreflang = []
    for lang in sorted(alternate_urls):
        if src in alternate_urls[lang]:
            url = alternate_urls[lang][src]
            hreflang.append('<link rel="alternate" href="{url}" hreflang="{lang}"/>'.format(
                lang=lang,
                url=url
            ))
    return hreflang


def get_lang_urls(src):
    urls = []
    for url_lang in sorted(alternate_urls):
        if src in alternate_urls[url_lang]:
            img_css = ''
            if url_lang == lang:
                img_css = ' class="grayscale"'
            url = alternate_urls[url_lang][src]
            urls.append(
                '<li><a href="{url}" rel="alternate" hreflang="{lang}"><img{css} src="{resource_url}{lang}.png" /></a>'.format(
                    lang=url_lang,
                    url=url,
                    resource_url=resource_url,
                    css=img_css
                ))
    return urls


'''
Main Program Flow
'''

lang = "en"
default_strings = {
    'made_by': 'Made by {manufacturer}',
    'type_hat': 'HAT form-factor',
    'type_classic': 'Classic form-factor',
    'pin_header': '{} pin header',
    'uses_i2c': 'Uses I2C',
    'wiring_pi_pin': 'Wiring Pi pin {}',
    'uses_n_gpio_pins': '* Uses {} GPIO pins',
    'bcm_pin_rev1_pi': 'BCM pin {} on Rev 1 ( very early ) Pi',
    'physical_pin_n': 'Physical pin {}',
    'more_information': 'More Information',
    'github_repository': 'GitHub Repository',
    'buy_now': 'Buy Now'
}

if len(sys.argv) > 1:
    lang = sys.argv[1]

alternate_urls = urlmapper.generate_urls(lang)

pinout.load(lang)

overlays = pinout.settings['overlays']

strings = pinout.get_setting('strings', {})

if type(strings) == list:
    _strings = {}
    for item in strings:
        _strings[item.keys()[0]] = item.values()[0]
    strings = _strings

for key, val in default_strings.items():
    if key not in strings:
        strings[key] = val

base_url = pinout.get_setting('base_url', '/pinout/')  # '/pinout-tr/pinout/'
resource_url = pinout.get_setting('resource_url', '/resources/')  # '/pinout-tr/resources/'
url_suffix = pinout.get_setting('url_suffix', '')  # '.html'

template = open('src/{}/template/layout.html'.format(lang)).read()

pages = {}
navs = {}
select_overlays = []

overlays_html = ''

if not os.path.isdir('output'):
    try:
        os.mkdir('output')
    except OSError:
        exit('Failed to create output dir')
if not os.path.isdir('output/{}'.format(lang)):
    try:
        os.mkdir('output/{}'.format(lang))
    except OSError:
        exit('Failed to create output/{} dir'.format(lang))
if not os.path.isdir('output/{}/pinout'.format(lang)):
    try:
        os.mkdir('output/{}/pinout'.format(lang))
    except OSError:
        exit('Failed to create output/{}/pinout dir'.format(lang))

overlays = map(load_overlay, overlays)

for url, name in select_overlays:
    overlays_html += '<li><a href="{}{}">{}</a></li>'.format(base_url, url, name)

'''
Manually add the index page as 'pinout', this is due to how the
website is currently structured with /pinout as the index
and all other pages in /pinout/

serve.py will mirror this structure for testing.
'''
pages['index'] = {}
pages['index']['rendered_html'] = render_overlay_page({'name': 'Index', 'long_description': load_md('index.md')})
navs['index'] = render_nav('pinout')

print('Rendering pin pages...')

for pin in range(1, len(pinout.pins) + 1):
    (pin_url, pin_html, pin_title) = render_pin_page(pin)
    if pin_url is None:
        continue

    hreflang = get_hreflang_urls('pin{}'.format(pin))
    langlinks = get_lang_urls('pin{}'.format(pin))

    pin_nav = render_nav(pin_url)
    pin_html = pinout.render_html(template,
                                  lang_links="\n\t\t".join(langlinks),
                                  hreflang="\n\t\t".join(hreflang),
                                  nav=pin_nav,
                                  content=pin_html,
                                  resource_url=resource_url,
                                  overlays=overlays_html,
                                  description=pinout.settings['default_desc'],
                                  title=pin_title + pinout.settings['title_suffix'],
                                  langcode=lang
                                  )
    print('Outputting page {}'.format(pin_url))

    with open(os.path.join('output', lang, 'pinout', '{}.html'.format(pin_url)), 'w') as f:
        f.write(pin_html)

# nav = render_nav()

print('Rendering overlay and index pages...')

for url in pages:
    content = pages[url]['rendered_html']
    nav = navs[url]
    hreflang = []
    langlinks = []

    if url == 'index':
        hreflang = get_hreflang_urls('index')
        langlinks = get_lang_urls('index')

    if 'src' in pages[url]:
        src = pages[url]['src']
        hreflang = get_hreflang_urls(src)
        langlinks = get_lang_urls(src)

    if not 'description' in pages[url]:
        pages[url]['description'] = pinout.settings['default_desc']

    if 'name' in pages[url]:
        pages[url]['name'] = pages[url]['name'] + pinout.settings['title_suffix']
    else:
        pages[url]['name'] = pinout.settings['default_title']

    html = pinout.render_html(template,
                              lang_links="\n\t\t".join(langlinks),
                              hreflang="\n\t\t".join(hreflang),
                              nav=nav,
                              content=content,
                              overlays=overlays_html,
                              resource_url=resource_url,
                              description=pages[url]['description'],
                              title=pages[url]['name'],
                              langcode=lang
                              )
    print('Outputting page {}'.format(url))

    if url != 'index':
        url = os.path.join('pinout', url)

    with open(os.path.join('output', lang, '{}.html'.format(url)), 'w') as f:
        f.write(html)
