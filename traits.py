#!/usr/bin/env python

from __future__ import unicode_literals
import os
import json
import io
from collections import OrderedDict

PACK_PATH = 'pack'
TRANSLATION_PATH = 'translations'
TRAITS_FILENAME = 'traits.json'

def _split_traits(traits):
    """split trait string into list (i.e. "Item. Weapon." --> ["Item", "Weapon"])

    Args:
        traits (str): raw traits string from json

    Returns:
        List[str]: splited traits
    """
    # Assumption: traits are splited by . (same as web version)
    return [x.strip() for x in traits.split('.') if x.strip()]

def _merge_traits(traits):
    """merge trait lists into single string (reversed from _split_traits)
     (i.e. ["Item", "Weapon"] --> "Item. Weapon.")

    Args:
        traits (List[str]): traits list

    Returns:
        str: raw traits string for json
    """
    if not traits:
        return ''
    return '. '.join(traits)+'.'

def get_json_files(path, cycles=None):
    """get json files from directory tree of path

    Args:
        path (str): target path
        cycles ([type], optional): files for cycles. Defaults to None (all).

    Returns:
        List[str]: lists of all json files
    """
    if not os.path.isdir(path):
        raise IOError('%s is not directory (when parsing json)'%path)
    json_files = []
    if not cycles:
        cycles = os.listdir(path)
    for cycle in cycles:
        if os.path.isfile(cycle) and os.path.splitext(cycle)[-1].lower() == '.json':
            json_files.append(cycle)
            continue
        for pack in os.listdir(os.path.join(path, cycle)):
            if os.path.splitext(pack)[-1].lower() == '.json':
                json_files.append(os.path.join(cycle, pack))
    return json_files

def make_placeholder():
    """make placeholder file from pack (english) and save

    We collect all traits from all json file in pack_path.
    Then, all traits are saved as save_path.
    """
    json_files = get_json_files(PACK_PATH)
    traits = set()
    for json_file in json_files:
        with io.open(os.path.join(PACK_PATH, json_file), encoding='utf-8') as fp:
            data = json.load(fp, object_pairs_hook=OrderedDict)
        for card in data:
            if 'traits' not in card:
                continue
            traits.update(
                _split_traits(card['traits'])
            )
        del data
    traits = sorted(list(traits))
    data = [{'code': x, 'name': x} for x in traits]
    with io.open(TRAITS_FILENAME, 'w', encoding='utf-8') as fp:
        string = json.dumps(data, ensure_ascii=False, indent=4)
        fp.write(string)

def update_placeholder(code):
    """update translation placeholder from raw file

    Args:
        code (str): language code (eg. de, es, ko...)
    """
    if not os.path.isfile(TRAITS_FILENAME):
        raise IOError('traits file not found.')
    if not os.path.isdir('%s/%s'%(TRANSLATION_PATH, code)):
        raise IOError('language code(%s) is not found.'%code)
    trans_traits_path = '%s/%s/%s'%(TRANSLATION_PATH, code, TRAITS_FILENAME)
    trans_data = None
    if os.path.isfile(trans_traits_path):
        with io.open(trans_traits_path, encoding='utf-8') as fp:
            trans_data = json.load(fp, object_pairs_hook=OrderedDict)
    if not trans_data:
        trans_data = []
    trans_codes = [x['code'] for x in trans_data]
    with io.open(TRAITS_FILENAME, encoding='utf-8') as fp:
        data = json.load(fp, object_pairs_hook=OrderedDict)
    for item in data:
        if item['code'] not in trans_codes:
            trans_data.append(item)
    trans_data.sort(key=lambda x: x['code'])
    with io.open(trans_traits_path, 'w', encoding='utf-8') as fp:
        string = json.dumps(trans_data, ensure_ascii=False, indent=4)
        fp.write(string)

def update_traits(code, cycles=None, no_overwrite=True):
    with io.open('%s/%s/%s'%(TRANSLATION_PATH, code, TRAITS_FILENAME), encoding='utf-8') as fp:
        data = json.load(fp, object_pairs_hook=OrderedDict)
    traits_map = {}
    for item in data:
        traits_map[item['code']] = item['name']
    del data
    jsons = [x for x in get_json_files('%s/%s/%s'%(TRANSLATION_PATH, code, PACK_PATH), cycles)
             if os.path.isfile(os.path.join(PACK_PATH, x))]
    if not json:
        raise IOError('no proper json files')
    for file in jsons:
        path_trans = os.path.join(TRANSLATION_PATH, code, PACK_PATH, file)
        with io.open(os.path.join(PACK_PATH, file), encoding='utf-8') as fp:
            data_en = json.load(fp, object_pairs_hook=OrderedDict)
        with io.open(path_trans, encoding='utf-8') as fp:
            data_trans = json.load(fp, object_pairs_hook=OrderedDict)
        code_en = [x['code'] for x in data_en]
        changed = False
        for item in data_trans:
            if 'traits' not in item:
                continue
            try:
                item_en = data_en[code_en.index(item['code'])]
            except ValueError:
                continue
            if no_overwrite and item['traits'] != item_en['traits']:
                # if already written
                continue
            traits_en = _split_traits(item_en['traits'])
            traits = [traits_map[x] for x in traits_en]
            item['traits'] = _merge_traits(traits)
            changed = True
        if changed:
            with io.open(path_trans, 'w', encoding='utf-8') as fp:
                string = json.dumps(data_trans, ensure_ascii=False, indent=4)
                fp.write(string)

def json2txt(path_json, path_text):
    """text file convesion for text file (utiliy purpose)
    format: [[code]]\t[[name]]\n

    Args:
        path_json (str): path of json file (usually translations/**/traits.json)
        path_text (str): path of text file for SAVE
    """
    with io.open(path_json, encoding='utf-8') as fp:
        data = json.load(fp, object_pairs_hook=OrderedDict)
    fp = io.open(path_text, 'w', encoding='utf-8')
    for item in data:
        fp.write('%s\t%s\n'%(item['code'], item['name']))
    fp.close()

def txt2json(path_json, path_text):
    """update translation json file from txt

    Args:
        path_json (str): path of json file (usually translations/**/traits.json)
        path_text (str): path of text file
    """
    data = {}
    with io.open(path_json, encoding='utf-8') as fp:
        temp = json.load(fp, object_pairs_hook=OrderedDict)
    for item in temp:
        data[item['code']] = item['name']
    del temp
    fp = io.open(path_text, encoding='utf-8')
    for line in fp:
        if not line.strip():
            continue
        code, name = line.split('\t')
        code, name = code.strip(), name.strip()
        print(code, name)
        if code in data:
            data[code] = name
    fp.close()
    data = [{'code': key, 'name': value} for key, value in data.items()]
    data.sort()
    with io.open(path_json, 'w', encoding='utf-8') as fp:
        string = json.dumps(data, ensure_ascii=False, indent=4)
        fp.write(string)

def main():
    make_placeholder()
    update_placeholder('ko')
    update_traits('ko')

if __name__ == '__main__':
    main()
