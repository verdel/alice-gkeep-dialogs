#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import argparse
import sys
import os
import re
import alice_gkeep_dialogs.libs.tools as tools
from alice_gkeep_dialogs.libs.gkeep import client
from alice_gkeep_dialogs.libs.gkeep import exception
from flask import Flask, request
from functools import wraps

app = Flask(__name__)
cfg = None
default_gkeep_list = None
logger = None
keep = None


@app.route('/gkeep', methods=['POST'])
def api():
    global logger
    logger.debug('Request: %r', request.json)

    response = {
        "version": request.json['version'],
        "session": request.json['session'],
        "response": {
            "end_session": False
        }
    }

    handle_dialog(request.json, response)
    logger.debug('Response: %r', response)

    return json.dumps(
        response,
        ensure_ascii=False,
        indent=2
    )


def restricted(func):
    @wraps(func)
    def wrapped(req, res, *args, **kwargs):
        if req['request']['command'] == 'ping':
            allowed_user = True
        else:
            user_id = req['session']['user']['user_id']
            if cfg['alice']:
                if cfg['alice']['allow_user']:
                    allowed_user = any(d['id'] == user_id for d in cfg['alice']['allow_user'])
                else:
                    allowed_user = True
            else:
                allowed_user = True

        if allowed_user:
            return func(req, res, *args, **kwargs)
        else:
            logger.debug('Not authorized user with id {} try to access'.format(user_id))
            res['response']['text'] = 'Вы не авторизованы для использования навыка.'
            return
    return wrapped


@restricted
def handle_dialog(req, res):
    global default_gkeep_list
    global keep

    if req['request']['command'] == 'ping':
        res['response']['text'] = 'pong'
        res['response']['end_session'] = True
        return

    elif not req['request']['nlu']['tokens']:
        res['response']['text'] = ''
        return

    elif any(elem in req['request']['nlu']['tokens'] for elem in ['помощь', 'умеешь']):
        res['response']['text'] = 'Я могу подсказать вам, какие текущие списки покупок у вас есть. Спросите у меня "Какие есть списки?"'
        return

    elif any(elem in req['request']['nlu']['tokens'] for elem in ['какие', 'списки']):
        if default_gkeep_list:
            res['response']['text'] = 'У вас есть следующие списки: {}. Сейчас список по-умолчанию: {}.'.format(', '.join(keep.getAll()), default_gkeep_list)
        else:
            res['response']['text'] = 'У вас есть следующие списки: {}.'.format(', '.join(keep.getAll()))
        return

    elif all(elem in req['request']['nlu']['tokens'] for elem in ['что', 'списке']):
        item_list = re.match(r'.*списке\s*([\w\s]*)', req['request']['original_utterance'])
        if item_list:
            if item_list.group(1):
                list_name = item_list.group(1)
                if not keep.checkListExist(list_name):
                    res['response']['text'] = 'Не найден список {}.'.format(list_name)
                    return
            elif default_gkeep_list:
                list_name = default_gkeep_list
            else:
                res['response']['text'] = 'Не выбран ни один из списков. Задайте список по-умолчанию, либо укажите список в запросе на удаление.'
                return
            try:
                glistContent = keep.getListContent(list_name)
            except exception.GoogleKeepListNotFound as exc:
                logger.debug(exc)
                res['response']['text'] = exc.message
                return
            else:
                if glistContent:
                    res['response']['text'] = 'В списке есть следующие неотмеченные записи: {}.'.format(', '.join(glistContent))
                    return
                else:
                    res['response']['text'] = 'Список пуст.'
                    return
        else:
            res['response']['text'] = 'Я вас не поняла, попробуйте повторить команду.'
            return

    elif any(elem in req['request']['nlu']['tokens'] for elem in ['добавь', 'добавить']):
        if 'добавить' in req['request']['nlu']['tokens']:
            res['response']['end_session'] = True
        # TODO Individual acknowledgement for item create operation
        item_list = re.match(r'.*Добав(?:ь|ить)\s(.*)(?:\sв\sсписок)\s*(.*)', req['request']['original_utterance'], re.IGNORECASE)
        if item_list:
            if item_list.group(2):
                list_name = item_list.group(2)
                if not keep.checkListExist(list_name):
                    res['response']['text'] = 'Не найден список {}.'.list_name
                    return
            elif default_gkeep_list:
                list_name = default_gkeep_list
            else:
                res['response']['text'] = 'Не выбран ни один из списков. Задайте список по-умолчанию, либо укажите список в запросе на добавление.'
                return
            item_list = item_list.group(1).split(' и ')
            if keep.addItem(list_name, item_list):
                res['response']['text'] = 'Добавила.'
                return
            else:
                res['response']['text'] = 'Я не смогла добавить указанные позиции в список. Попробуйте ещё раз.'
                return
        else:
            res['response']['text'] = 'Я вас не поняла, попробуйте повторить команду.'
            return

    elif any(elem in req['request']['nlu']['tokens'] for elem in ['отметь', 'отметить']):
        if 'отметить' in req['request']['nlu']['tokens']:
            res['response']['end_session'] = True
        item_list = re.match(r'.*Отмет(?:ь|ить)\s(.*)(?:\sв\sсписке)\s*(.*)', req['request']['original_utterance'], re.IGNORECASE)
        if item_list:
            if item_list.group(2):
                list_name = item_list.group(2)
                if not keep.checkListExist(list_name):
                    res['response']['text'] = 'Не найден список {}.'.list_name
                    return
            elif default_gkeep_list:
                list_name = default_gkeep_list
            else:
                res['response']['text'] = 'Не выбран ни один из списков. Задайте список по-умолчанию, либо укажите список в запросе на отметку.'
                return
            if 'все' in req['request']['nlu']['tokens']:
                if keep.checkAllItem(list_name):
                    res['response']['text'] = 'Отметила все записи в списке {}.'.format(list_name)
                    return
                else:
                    res['response']['text'] = 'Я не смогла отметить все записи в указанном списке. Попробуйте ещё раз.'
                    return
            else:
                item_list = item_list.group(1).split(' и ')
                if keep.checkItem(list_name, item_list):
                    res['response']['text'] = 'Отметила.'
                    return
                else:
                    res['response']['text'] = 'Я не смогла отметить указанные позиции в списке. Попробуйте ещё раз.'
                    return
        else:
            res['response']['text'] = 'Я вас не поняла, попробуйте повторить команду.'
            return

    elif any(elem in req['request']['nlu']['tokens'] for elem in ['удали', 'удалить']):
        if 'удалить' in req['request']['nlu']['tokens']:
            res['response']['end_session'] = True
        # TODO Individual acknowledgement for item delete operation
        item_list = re.match(r'.*Удал(?:и|ить)\s(.*)(?:\sиз\sсписка)\s*([\w\s]*)', req['request']['original_utterance'], re.IGNORECASE)
        if item_list:
            if item_list.group(2):
                list_name = item_list.group(2)
                if not keep.checkListExist(list_name):
                    res['response']['text'] = 'Не найден список {}.'.list_name
                    return
            elif default_gkeep_list:
                list_name = default_gkeep_list
            else:
                res['response']['text'] = 'Не выбран ни один из списков. Задайте список по-умолчанию, либо укажите список в запросе на удаление.'
                return
            if 'все' in req['request']['nlu']['tokens']:
                if keep.deleteAllItem(list_name):
                    res['response']['text'] = 'Удалила все записи из списка {}.'.format(list_name)
                    return
                else:
                    res['response']['text'] = 'Я не смогла очистить указанный список. Попробуйте ещё раз.'
                    return
            else:
                item_list = item_list.group(1).split(' и ')
                if keep.deleteItem(list_name, item_list):
                    res['response']['text'] = 'Удалила.'
                    return
                else:
                    res['response']['text'] = 'Я не смогла удалить указанные позиции из списка. Попробуйте ещё раз.'
                    return
        else:
            res['response']['text'] = 'Я вас не поняла, попробуйте повторить команду.'
            return
# TODO: Add delete all on command 'Очисти список'
    else:
        res['response']['text'] = 'Я вас не поняла, попробуйте повторить команду.'
        return


def cli():
    parser = argparse.ArgumentParser(description='Alice Google Keep Dialog')
    parser.add_argument('-c', '--config', required=True,
                        help='configuration file path')
    parser.add_argument('--debug', default=os.environ.get('GOOGLE_APP_DEBUG', False), action='store_true', help='enable debug level logging')
    return parser.parse_args()


def main():
    global cfg
    global default_gkeep_list
    global keep
    global logger

    args = cli()
    logger = tools.init_log(debug=args.debug)

    if not os.path.isfile(args.config):
        print('Alice Google Keep configuration file {} not found'.format(args.config))
        logger.error('Alice Google Keep configuration file {} not found'.format(args.config))
        sys.exit()

    try:
        cfg = tools.get_config(args.config)
    except Exception as exc:
        logger.error('Config file error: {}'.format(exc))
        sys.exit(1)

    try:
        keep = client.GKeep(cfg['google_keep']['username'], cfg['google_keep']['token'])
    except Exception as exc:
        logger.error(exc)
        sys.exit(1)

    if 'default_list' in cfg['google_keep']:
        if keep.checkListExist(cfg['google_keep']['default_list']):
            default_gkeep_list = cfg['google_keep']['default_list']
    app.run(debug=False, host='0.0.0.0')


if __name__ == '__main__':
    main()
