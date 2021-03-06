# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

from wtforms.validators import Required
from invenio.webdeposit_config_utils import WebDepositConfiguration

__all__ = ['WebDepositField']


def WebDepositField(key=None):
    class WebDepositFieldClass(object):
        """
        Class that all webdeposit fields must inherit.

        A helper to add attributes and methods to every webdeposit field.
        """

        def __init__(self, **kwargs):
            # Create our own Required data member
            # for client-side use
            if 'validators' in kwargs:
                for v in kwargs.get("validators"):
                    if type(v) is Required:
                        self.required = True
            if 'group' in kwargs:
                self.group = kwargs.pop('group')
            else:
                self.group = None

            super(WebDepositFieldClass, self).__init__(**kwargs)
            self.config = WebDepositConfiguration(field_type=self.__class__.__name__)
            self.recjson_key = self.config.get_recjson_key() or key

        def merge_validation_json(self, json1, json2):
            """ Merges 2 jsons returned from 2 validation functions

                @param json1: the first json
                @param json2: the second json
                @returns: a dictionary with info, success and error messages,
                          fields to be hidden/shown/disabled/enabled,
                          and the dictionary with fields to be updated merged.
                          Be carefull with jsons that update the same field!
            """

            json = {}

            # Merge the messages of 2 dicts if they exist
            def merge_msg(msg_exists, key, json1, json2):
                if (json1.get(msg_exists) == 1 or json2.get(msg_exists) == 1):
                    msg1 = (json1.get(key) or '')
                    msg2 = (json2.get(key) or '')
                    if msg1 == '':
                        msg = msg2
                    elif msg2 == '':
                        msg == msg1
                    else:
                        msg = msg1 + '<br>' + msg2
                    return 1, msg
                else:
                    return 0, ''

            json['success'], json['success_message'] = \
                merge_msg('success', 'success_message', json1, json2)

            json['info'], json['info_message'] = \
                merge_msg('info', 'info_message', json1, json2)

            json['error'], json['error_message'] = \
                merge_msg('error', 'error_message', json1, json2)


            if 'fields' in json1 and 'fields' in json2:
                """ Be carefull when the two validators change the
                    value of the same field.
                """
                json['fields'] = dict(json1['fields'].items() +
                                      json2['fields'].items())
            elif 'fields' in json1:
                json['fields'] = json1['fields']
            elif 'fields' in json2:
                json['fields'] = json2['fields']

            # Create the union of the lists that specify UI actions on fields
            concat_values = lambda key, json1, json2: \
                            [i for i in json1.get(key) or []] + \
                            [i for i in json2.get(key) or []]

            json['hidden_fields'] = concat_values('hidden_fields',
                                                  json1, json2)

            json['visible_fields'] = concat_values('visible_fields',
                                                   json1, json2)

            json['enabled_fields'] = concat_values('enabled_fields',
                                                   json1, json2)

            json['disabled_fields'] = concat_values('disabled_fields',
                                                    json1, json2)
            return json

        def has_recjson_key(self):
            return self.recjson_key is not None

        def cook_json(self, json_reader):
            """
            Fills a json_reader object with the field's value
            based on the recjson key

            @param json_reader: BibField's JsonReader object
            """
            cook_json_function = self.config.get_cook_json_function()
            if cook_json_function is not None:
                return cook_json_function(json_reader, self.data)
            elif key is not None:  # Default behaviour
                json_reader[key] = self.data

            return json_reader

        def uncook_json(self, json_reader, webdeposit_json):
            """
            The opposite of `cook_json` (duh)
            Adds to the webdeposit_json the appropriate value
            from the json_reader based on the recjson key

            You have to retrieve the record with BibField and
            instantiate a json_reader object before starting
            the uncooking

            @param json_reader: BibField's JsonReader object
            @param webdeposit_json: a dictionary
            @return the updated webdeposit_json
            """

            if self.has_recjson_key() and \
                    self.recjson_key in json_reader:
                webdeposit_json[self.name] = json_reader[self.recjson_key]
            return webdeposit_json

    return WebDepositFieldClass
