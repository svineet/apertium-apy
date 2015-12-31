#!/usr/bin/env python3
import logging
import json

WIKI_API_URL = 'http://wiki.apertium.org/w/api.php'


# Apertium Wiki utility functions
def wikiLogin(s, loginName, password):
    try:
        payload = {'action': 'login', 'format': 'json', 'lgname': loginName, 'lgpassword': password}
        authResult = s.post(WIKI_API_URL, params=payload)
        authToken = json.loads(authResult.text)['login']['token']
        logging.debug('Auth token: {}'.format(authToken))

        payload = {'action': 'login', 'format': 'json', 'lgname': loginName, 'lgpassword': password, 'lgtoken': authToken}
        authResult = s.post(WIKI_API_URL, params=payload)
        if not json.loads(authResult.text)['login']['result'] == 'Success':
            logging.critical('Failed to login as {}: {}'.format(loginName, json.loads(authResult.text)['login']['result']))
        else:
            logging.info('Login as {} succeeded'.format(loginName))
            return authToken
    except Exception as e:
        logging.critical('Failed to login: {}'.format(e))


def wikiGetPage(s, pageTitle):
    payload = {
        'action': 'query',
        'format': 'json',
        'titles': pageTitle,
        'prop': 'revisions',
        'rvprop': 'content'
    }
    viewResult = s.get(WIKI_API_URL, params=payload)
    jsonResult = json.loads(viewResult.text)

    if 'missing' not in list(jsonResult['query']['pages'].values())[0]:
        return list(jsonResult['query']['pages'].values())[0]['revisions'][0]['*']


def wikiEditPage(s, pageTitle, pageContents, editToken):
    payload = {
        'action': 'edit',
        'format': 'json',
        'title': pageTitle,
        'text': pageContents,
        'bot': 'True',
        'contentmodel': 'wikitext',
        'token': editToken
    }
    editResult = s.post(WIKI_API_URL, data=payload)
    jsonResult = json.loads(editResult.text)
    return jsonResult


def wikiGetToken(s, tokenType, props):
    try:
        payload = {
            'action': 'query',
            'format': 'json',
            'prop': props,
            'intoken': tokenType,
            'titles': 'Main Page'
        }
        tokenResult = s.get(WIKI_API_URL, params=payload)
        token = json.loads(tokenResult.text)['query']['pages']['1']['%stoken' % tokenType]
        logging.debug('%s token: %s' % (tokenType, token))
        return token
    except Exception as e:
        logging.error('Failed to obtain %s token: %s' % (tokenType, e))


def addText(content, data):
    if not content:
        content = ''

    newContentLines = []
    added = False
    for l in content.splitlines():
        newContentLines.append(l)
        if l == ('== '+data['langpair']+' =='):
            newContentLines.append(
                '* %s ; %s ; %s' % (data['context'], data['word'],
                                    data['newWord'])
                )
            added = True

    if not added:
        newContentLines.append('== %s ==' % data['langpair'])
        newContentLines.append(
            '* %s ; %s ; %s' % (data['context'], data['word'],
                                data['newWord'])
            )
        pass

    return "\n".join(newContentLines)


def addSuggestion(s, SUGGEST_URL, editToken, data):
    content = wikiGetPage(s, SUGGEST_URL)
    content = addText(content, data)
    editResult = wikiEditPage(s, SUGGEST_URL, content, editToken)

    if editResult['edit']['result'] == 'Success':
        logging.info('Update of page %s' % (SUGGEST_URL))
        return True
    else:
        logging.error('Update of page %s failed: %s' % (SUGGEST_URL,
                                                        editResult))
        return False
