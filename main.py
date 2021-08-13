import re
import StellarPlayer
import importlib
import io
import sys
from .you_get import common,extractor,json_output


class IwebdecodePlugin(StellarPlayer.IStellarPlayerPlugin):
    def __init__(self, player: StellarPlayer.IStellarPlayer):
        super().__init__(player)
        self.playurl = []

    def show(self):
        list_layout = [[{'type':'label','name':'video_profile'},{'type':'link','name':'播放','width':60,'@click':'onPlayClick'}]]
        controls = [
            {'type':'space','height':10},
            {'group':
                [
                    {'type':'edit','name':'url_edit','label':'html页面地址'},
                    {'type':'button','name':'解析','width':60,'@click':'parse_html'},
                    {'type':'space','width':10}
                ],
                'height':30
            },
            {'type':'space','height':10},
            {'type':'list','name':'list','itemlayout':list_layout,'separator':True,'itemheight':40}
        ]
        self.player.doModal('main',500,400,'',controls)

    def get_module(self,url):
        try:
            video_host = common.r1(r'https?://([^/]+)/', url)
            video_url = common.r1(r'https?://[^/]+(.*)', url)
            assert video_host and video_url
        except AssertionError:
            url = google_search(url)
            video_host = common.r1(r'https?://([^/]+)/', url)
            video_url = common.r1(r'https?://[^/]+(.*)', url)

        if video_host.endswith('.com.cn') or video_host.endswith('.ac.cn'):
            video_host = video_host[:-3]
        domain = common.r1(r'(\.[^.]+\.[^.]+)$', video_host) or video_host
        assert domain, 'unsupported url: ' + url

        # all non-ASCII code points must be quoted (percent-encoded UTF-8)
        url = ''.join([ch if ord(ch) in range(128) else parse.quote(ch) for ch in url])
        video_host = common.r1(r'https?://([^/]+)/', url)
        video_url = common.r1(r'https?://[^/]+(.*)', url)

        k = common.r1(r'([^.]+)', domain)
        if k in common.SITES:
            yougetimport = '.'.join(['webdecode.you_get', 'extractors', common.SITES[k]])
            return (
                importlib.import_module(yougetimport),
                url
            )
        else:
            try:
                location = common.get_location(url) # t.co isn't happy with fake_headers
            except:
                location = common.get_location(url, headers=fake_headers)

            if location and location != url and not location.startswith('/'):
                return get_module(location)
            else:
                return (importlib.import_module('webdecode.you_get.extractors.universal'), url)

    def parse_html(self,*args):
        self.player.updateControlValue('main','list',[])
        self.playurl = []
        self.player.toast('main','开始解析')
    
        url = self.player.getControlValue('main','url_edit')
        if url:
            m, url = self.get_module(url)  
            try:
                website = m.site
            except :
                var_exists = False
            else:
                var_exists = True            
            if var_exists :
                website.url = url
                website.json_output = True;
                website.prepare()
                print(website.name)
                outjson = json_output.output(website)
            else:
                outjson = m.download(url,json_output = True)
                    
            if outjson :   
                streams = outjson.get('streams')
                sitename = outjson.get('site')
                if streams:
                    urls = []
                    if sitename in ["爱奇艺 (Iqiyi)", "优酷 (Youku)"]:
                        for k,v in streams.items():            
                            if 'm3u8_url' in v:
                                urls.append({'url':v['m3u8_url'],'video_profile':v.get('video_profile',k)})
                    elif sitename in ["InfoQ"]:
                         for k,v in streams.items(): 
                            urls.append({'url':v['url'],'video_profile':'video'})
                    else :
                        for k,v in streams.items(): 
                            srcdata = v.get('src',k)
                            profile = v.get('video_profile',k)
                            if profile == None:
                                profile = v.get('quality',k)
                            if type(srcdata) is list:
                                listlen = len(srcdata)
                                if listlen > 1:
                                    for i,srcurl in enumerate(srcdata):
                                        itemprofile = profile + '.片段' + str(i + 1)
                                        urls.append({'url':srcurl,'video_profile':itemprofile})
                                else:
                                    urls.append({'url':srcdata[0],'video_profile':profile})
                            else:
                                urls.append({'url':srcdata,'video_profile':profile})
                            

                    #print(urls)
                    self.player.updateControlValue('main','list',urls)
                    self.playurl = urls
                    self.player.toast('main','解析完成')
                else:
                    self.player.toast('main','没有解析到播放地址1')
            else:
                self.player.toast('main','没有解析到播放地址2')
            
    def onPlayClick(self, page, control, idx, *arg):
        self.player.play(self.playurl[idx]['url'])
    

def newPlugin(player:StellarPlayer.IStellarPlayer,*arg):
    plugin = IwebdecodePlugin(player)
    return plugin

def destroyPlugin(plugin:StellarPlayer.IStellarPlayerPlugin):
    plugin.stop()