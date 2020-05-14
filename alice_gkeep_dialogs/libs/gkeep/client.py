# -*- coding: utf-8 -*-
from alice_gkeep_dialogs.libs import gkeepapi
from alice_gkeep_dialogs.libs.gkeep import exception


class GKeep(object):
    def __init__(self, username, token):
        self.keep = gkeepapi.Keep()
        self.keep.resume(username, token)

    def getAll(self):
        gnotes = self.keep.all()
        return [glist.title for glist in gnotes]

    def __getList(self, list_name):
        try:
            glist_iter = self.keep.find(func=lambda x: x.title.lower() == list_name.lower())
        except Exception:
            return False
        else:
            return glist_iter

    def checkListExist(self, list_name):
        glist_iter = self.__getList(list_name)
        if glist_iter:
            try:
                next(glist_iter)
            except StopIteration:
                return False
            else:
                return True

    def getListContent(self, list_name):
        self.keep.sync()
        glist_iter = self.__getList(list_name)
        if glist_iter:
            try:
                glist = next(glist_iter)
            except StopIteration:
                raise exception.GoogleKeepListNotFound('Не найден список {}'.format(list_name))
            else:
                return [glist_item.text for glist_item in glist.unchecked]
        else:
            raise exception.GoogleKeepListNotFound('Не найден список {}'.format(list_name))

    def __checkItemExist(self, list_name, add_item):
        glist_iter = self.__getList(list_name)
        if glist_iter:
            try:
                glist = next(glist_iter)
            except StopIteration:
                raise exception.GoogleKeepListNotFound('Не найден список {}'.format(list_name))
                return False
            else:
                for item in glist.items:
                    if add_item.lower().replace(' ', '') == item.text.lower().replace(' ', ''):
                        return True
                return False
        else:
            raise exception.GoogleKeepListNotFound('Не найден список {}'.format(list_name))
            return False

    def addItem(self, list_name, add_item_list):
        self.keep.sync()
        glist_iter = self.__getList(list_name)
        if glist_iter:
            try:
                glist = next(glist_iter)
            except StopIteration:
                raise exception.GoogleKeepListNotFound('Не найден список {}'.format(list_name))
                return False
            else:
                for item in add_item_list:
                    if not self.__checkItemExist(list_name, item):
                        glist.add(item)
                self.keep.sync()
                return True
        else:
            raise exception.GoogleKeepListNotFound('Не найден список {}'.format(list_name))
            return False

    def checkItem(self, list_name, check_item_list):
        self.keep.sync()
        glist_iter = self.__getList(list_name)
        if glist_iter:
            try:
                glist = next(glist_iter)
            except StopIteration:
                raise exception.GoogleKeepListNotFound('Не найден список {}'.format(list_name))
                return False
            else:
                check_item_list = [check_item.lower().replace(' ', '') for check_item in check_item_list]
                for item in glist.items:
                    if item.text.lower().replace(' ', '') in check_item_list and not item.checked:
                        item.checked = True
                        self.keep.sync()
                        return True
        else:
            raise exception.GoogleKeepListNotFound('Не найден список {}'.format(list_name))
            return False

    def checkAllItem(self, list_name):
        self.keep.sync()
        glist_iter = self.__getList(list_name)
        if glist_iter:
            try:
                glist = next(glist_iter)
            except StopIteration:
                raise exception.GoogleKeepListNotFound('Не найден список {}'.format(list_name))
                return False
            else:
                for item in glist.items:
                    item.checked = True
                self.keep.sync()
                return True
        else:
            raise exception.GoogleKeepListNotFound('Не найден список {}'.format(list_name))
            return False

    def deleteItem(self, list_name, delete_item_list):
        self.keep.sync()
        glist_iter = self.__getList(list_name)
        if glist_iter:
            try:
                glist = next(glist_iter)
            except StopIteration:
                raise exception.GoogleKeepListNotFound('Не найден список {}'.format(list_name))
                return False
            else:
                delete_item_list = [delete_item.lower().replace(' ', '') for delete_item in delete_item_list]
                for item in glist.items:
                    if item.text.lower().replace(' ', '') in delete_item_list:
                        item.delete()
                        self.keep.sync()
                        return True
        else:
            raise exception.GoogleKeepListNotFound('Не найден список {}'.format(list_name))
            return False

    def deleteAllItem(self, list_name):
        self.keep.sync()
        glist_iter = self.__getList(list_name)
        if glist_iter:
            try:
                glist = next(glist_iter)
            except StopIteration:
                raise exception.GoogleKeepListNotFound('Не найден список {}'.format(list_name))
                return False
            else:
                for item in glist.items:
                    item.delete()
                self.keep.sync()
                return True
        else:
            raise exception.GoogleKeepListNotFound('Не найден список {}'.format(list_name))
            return False
