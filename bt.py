#! /usr/bin/env python
# coding=utf-8
import hashlib
import bencode
from base64 import b64decode, b32decode
import string


def get_torrent_url_from_btih(hash, all=False):
    methods = [
        lambda hash: 'http://bt.box.n0808.com/%s/%s/%s.torrent' %
        (hash[:2], hash[-2:], hash),
        lambda hash: 'http://torrage.com/torrent/%s.torrent' % hash,
    ]

    if all:
        return [m(hash) for m in methods]

    return methods[0](hash)


def parse_torrent_file(torrent):
    if isinstance(torrent, basestring):
        file = open(torrent, 'rb')
    else:
        file = torrent

    return bencode.bdecode(file.read())


def get_btih(metainfo):
    info = metainfo.get('info')
    info_hash_hex = hashlib.sha1(bencode.bencode(info)).hexdigest()
    return info_hash_hex.upper()


def create_magnet_url(btih):
    return 'magnet:?xt=urn:btih:' + btih


def get_simple_metainfo(metainfo):
    simple_metainfo = {}
    info = metainfo['info']

    encoding = metainfo.get('encoding', 'utf-8')

    if 'name.utf-8' in info:
        name = info['name.utf-8'].decode('utf-8')
    else:
        name = info['name'].decode(encoding)

    files = []
    if 'files' in info:
        for f in info['files']:
            length = f['length']
            if 'path.utf-8' in f:
                path = '/'.join(f['path.utf-8']).decode('utf-8')
            else:
                path = '/'.join(f['path']).decode(encoding)
            files.append((path, length))
    else:
        files.append((name, info['length']))

    if 'creation date' in metainfo:
        simple_metainfo['create_date'] = metainfo['creation date']
    simple_metainfo['name'] = name
    simple_metainfo['files'] = files
    simple_metainfo['btih'] = get_btih(metainfo)

    return simple_metainfo


def check_btih(btih):
    if len(btih) != 40:
        return False
    return not btih.translate(None, string.hexdigits)


class TorrentFile:

    def __init__(self, torrent):
        self._torrent = torrent
        if isinstance(torrent, basestring) and len(torrent) > 1024:
            self.metainfo = bencode.bdecode(torrent)
        else:
            self.metainfo = parse_torrent_file(torrent)
        self._simple_metainfo = get_simple_metainfo(self.metainfo)

    @property
    def btih(self):
        return self._simple_metainfo['btih']

    @property
    def name(self):
        return self._simple_metainfo['name']

    @property
    def info(self):
        return self._simple_metainfo

    @property
    def magnet_url(self):
        return create_magnet_url(self.btih)

    @property
    def torrent_url(self):
        return get_torrent_url_from_btih(self.btih)


class BTResourceObject:

    def __init__(self, obj):
        self._obj = obj

    def get_magnet_url(self):
        create_magnet_url(self._obj.hash)

    def get_torrent_url(self):
        obj = self._obj
        return getattr(obj, 'torrent', None) or \
            get_torrent_url_from_btih(self._obj.hash)

    def __getattr__(self, key):
        return getattr(self._obj, key)


def decode_thunder_url(url):
    return b64decode(url[10:])[2:-2]


def decode_btih(btih):
    return b32decode(btih).encode('hex')
