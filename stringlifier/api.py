#
# Copyright (c) 2020 Adobe Systems Incorporated. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from stringlifier.modules.stringc import AwDoC, AwDoCConfig, Encodings
import torch
import pkg_resources


def _tokenize(string):
    tokens = []
    ignore = []
    current_token = ''
    for char in string:
        if char.isalnum():
            current_token += char
        else:
            if current_token != '':
                if current_token.isalnum():
                    ignore.append(False)
                else:
                    ignore.append(True)
                tokens.append(current_token)
            current_token = ''

            tokens.append(char)
            ignore.append(True)

    tokens.append(current_token)
    if current_token.isalnum():
        ignore.append(False)
    else:
        ignore.append(True)
    return tokens, ignore


class Stringlifier:
    def __init__(self, model_base=None):
        encodings = Encodings()
        if model_base is None:
            enc_file = pkg_resources.resource_filename(__name__, 'data/string-c.encodings')
            conf_file = pkg_resources.resource_filename(__name__, 'data/string-c.conf')
            model_file = pkg_resources.resource_filename(__name__, 'data/string-c.bestType')
        else:
            enc_file = '{0}.encodings'.format(model_base)
            conf_file = '{0}.conf'.format(model_base)
            model_file = '{0}.bestType'.format(model_base)
        encodings.load(enc_file)
        config = AwDoCConfig()
        config.load(conf_file)
        self.classifier = AwDoC(config, encodings)
        self.classifier.load(model_file)
        self.classifier.eval()
        self.encodings = encodings

    def __call__(self, string_or_list, return_tokens=False):
        if isinstance(string_or_list, str):
            tokens, ignore_list = _tokenize(string_or_list)
        else:
            tokens = string_or_list
        with torch.no_grad():
            p_ts, _ = self.classifier(tokens)

        p_ts = torch.argmax(p_ts, dim=-1).detach().cpu().numpy()
        token_output = []
        for ignore, token, p_t in zip(ignore_list, tokens, p_ts):
            if not ignore:
                string_type = self.encodings._type_list[p_t]
            else:
                string_type = 'SYMBOL'

            token_output.append({'token': token, 'type': string_type})

        output_string = ''
        for entry in token_output:
            if entry['type'] == 'HASH':
                output_string += '<RANDOM_STRING>'
            else:
                output_string += entry['token']
        if return_tokens:
            return output_string, token_output
        else:
            return output_string