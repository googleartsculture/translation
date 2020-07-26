#!/usr/bin/python
#
# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import json


class DictionaryTreeException(Exception):
    pass





class DictionaryTree:
    """
    This class encapsulates two data structures that support operations on glyph
    words.

    tree:
        A nested dictionary that supports finding glyph words within a sequence
        of glyph codes. Gylph codes are by default lowercase.
    translations:
        A dictionary supporting the translation of glyph words into one or more
        alternative representations.
        Transliteration is considered a translation.

    tree comprises a set of nodes where a node comprises a key:value pair where:
    - Each node's key is either an object or the key used for a terminating node
    - When the key is an object the value is a dictionary.
    - When the key is the terminator the value is a dictionary entry ID string.
    - A terminator indicates that we've reached the end of a dictionary entry
    and provides the entry's ID

    translations is dictionary where:
    - A key is an entry_id string from the tree
    - The value is a dictionary containing 2 keys:
        - word: provides the glyph codes of a word in a glyph
        - translations: A dictionary containing a key for each supported
        language

    The key methods for working with glyph sequences and words are:

    get_entries_in_sequence(self, sequence):
        Given a sequence of glyph codes it finds all the glyph words in the
        sequence

    get_entries_containing_sequence(self, sequence, match='contains')
        Given a sequence of glyph codes it finds glyph words that match the
        sequence
        Search match options are {exact|starts_with|contains}

    get_glyph_words(self, term, lang='transliteration')
        Given a term in a translation language find a all the glyph words whose
        translations contain the term

    get_entry(self, entry_id)
        Given an entry ID string returns the entry from translations
    """

    # The nested dictionary of symbol sequences
    tree = dict()
    # Translations - a dictionary of symbol sequence translations
    translations = dict()
    # Key for a terminating node. The value of the terminating node is a
    # dictionary entry ID
    terminator = '-1'
    # Supported languages
    languages = []
    # This is the default. All tree keys are lowercase symbols.
    lowercase = True

    POSITIONS_KEY = 'positions'
    ENTEYIDS_KEY = 'entry_ids'

    def __init__(self, lowercase=True):
        """
        param lowercase: Boolean that determines whether to make all entries
        lowercase (default is True)
        """
        self.__initialise(lowercase)

    def populate(self, entries, translations=None, validate=False):
        """
        Dictionary generator
        param entries: A dictionary of entries (key is an entry ID - a string or
            int, value is tuple of symbols).
        param translations: A dictionary of translations for a dictionary entry
            where key is an entry ID (str or int) and value is a dictionary
            where keys are language codes and values are strings.
        param validate: Boolean that determines whether or not validation of
            entries and translations is done.
        """
        if not self.__is_valid_entries(entries):
            raise DictionaryTreeException(
                'Parameter entries is not a non-empty dict in method populate')
        if not self.__is_valid_translations(translations):
            raise DictionaryTreeException(
                'Parameter translations is not a' +
                ' non-empty dict in method populate')

        # Remove any existing entries and translations
        self.__initialise(self.lowercase)
        for entry_id in entries:
            try:
                self.add_entry(entries[entry_id], entry_id)
            except (AttributeError, ValueError):
                continue
        self.set_translations(translations)

    def add_entry(self, entry, entry_id):
        """
        Add an entry to the tree.
        param entry: The symbol sequence we are adding
        param entry_id: The symbol sequence's ID in the dictionary_tree
        TODO - check parameter values
        """
        if not self.__is_valid_entry(entry):
            raise DictionaryTreeException(
                'Parameter entry is not a non-empty tuple in method add_entry')
        if not self.__is_valid_entry_id(entry_id):
            raise DictionaryTreeException(
                'Parameter entry_id is not a non-empty str ' +
                'or int in method add_entry')
        key_list = []
        if self.lowercase:
            entry = [e.lower() for e in entry]
        for i, symbol in enumerate(entry):
            # First time in this will be the whole tree
            sub_d = self.__get_sub_tree(key_list)
            if i < len(entry) - 1:
                if symbol not in sub_d:
                    sub_d[symbol] = {}
            else:
                # Last element of entry which also handles entries with a
                # single element
                if symbol not in sub_d:
                    sub_d[symbol] = {self.terminator: [entry_id]}
                else:
                    if self.terminator in sub_d[symbol]:
                        sub_d[symbol][self.terminator].append(entry_id)
                    else:
                        sub_d[symbol][self.terminator] = [entry_id]
            key_list.append(symbol)

    def get_entries_in_sequence(self, sequence):
        """
        Public method for finding all dictionary entries within a sequence
        Calls __get_sequence_entries
        param sequence: Sequence of symbols we are analysing
        return an results data structure containing positional, entry_id and
            translation data
        """
        if not self.__is_populated():
            raise DictionaryTreeException(
                'The dictionary tree and/or translations are empty ' +
                'in method get_entries_in_sequence')
        if not self.__is_valid_sequence(sequence):
            raise DictionaryTreeException(
                'Parameter sequence is not a non-empty list ' +
                'in method get_entries_in_sequence')

        if self.lowercase:
            sequence = [s.lower() for s in sequence]
        entries = self.__get_sequence_entries(sequence)
        results = []
        for i, entry in enumerate(entries):
            # Ensure we have some entry ID values
            if len(entry[2]) > 0:
                # Separate result for each entry ID of a given glyph sequence
                for n, entry_id in enumerate(entry[2]):
                    results.append(
                        (entry[1], entry_id, self.get_entry(entry_id)))
        return results

    def get_entries_containing_sequence(self, sequence, match='contains'):
        """
        Public method for finding all dictionary entries that contain a sequence
        Calls __search_words
        param sequence: Sequence of symbols we are analysing
        param match: Search match options are {exact|starts_with|contains}
        return A list of glyph words and their translations
        """
        if not self.__is_populated():
            raise DictionaryTreeException(
                'The dictionary tree and/or translations are empty in' +
                ' method get_entries_containing_sequence')
        if not self.__is_valid_sequence(sequence):
            raise DictionaryTreeException('Parameter sequence is not a ' +
                'non-empty list in method get_entries_containing_sequence')
        if match not in ['exact', 'starts_with', 'contains']:
            raise DictionaryTreeException(
                'Parameter match is not one of [exact, starts_with, ' +
                'contains] in method get_entries_containing_sequence')

        entries = self.__search_words(sequence, match=match)
        for i, entry in enumerate(entries):
            entries[i] = self.get_entry(entries[i])
        return entries

    def get_glyph_words(self, term, lang='transliteration'):
        """
        Public method for finding all glyph words with translations
            that contain a search term
        Calls __search_translations
        param term: The string we are searching for
        param lang: The language of the translations we are searching.
            Default is transliteration
        return A list of glyph code words each word in its own list
        """
        if not self.__is_populated():
            raise DictionaryTreeException(
            'The dictionary tree and/or translations are empty' +
            ' in method get_glyph_codes')
        if len(term) == 0:
            raise DictionaryTreeException(
            'Parameter term is empty in method get_glyph_codes')
        if lang not in self.languages:
            raise DictionaryTreeException(
            'Language ' + lang +
            ' is not supported by dictionary in method get_glyph_codes')

        codes = self.__search_translations(term, lang=lang)
        return codes

    def get_entry(self, entry_id):
        """
        Get an entry from translations for a given entry_id
        param entry_id: The entry_id
        return A translation dict
        """
        if not self.__is_valid_entry_id(str(entry_id)):
            raise DictionaryTreeException(
                'Parameter entry_id is not a non-empty strin ' +
                'method get_entry_translations')
        if not self.__is_valid_translations(self.translations):
            raise DictionaryTreeException(
                'Parameter translations is not a non-empty dict in ' +
                'method get_entry_translations')
        if entry_id in self.translations:
            return self.translations[str(entry_id)]
        return {}

    def has_tree_entry(self, sequence):
        """
        Check whether a symbol sequence is in the tree and return a
            tuple containing:
        - A list of dictionary entry IDs if the sequence if found or,
            if not found, an empty list
        - An symbol which defines the last matching symbol in the sequence.
            If the sequence is found this will be the last symbol of the
            sequence or if not -1
        param sequence: The sequence to lookup in the dictionary
        return Tuple in form ([entry_id], dictionary symbol) where [entry_id]
            can be empty
        """
        if not self.__is_populated():
            raise DictionaryTreeException(
                'The dictionary tree and translations are empty in ' +
                'method has_tree_entry')
        if not self.__is_valid_sequence(sequence):
            raise DictionaryTreeException(
                'Parameter sequence is not a non-empty list in ' +
                'method has_tree_entry')

        if self.lowercase:
            sequence = [s.lower() for s in sequence]
        for n, item in enumerate(sequence):
            if n == 0:
                sub_tree = self.tree.get(item, None)
            else:
                sub_tree = sub_tree.get(sequence[n], None)
            if sub_tree is None:
                if n == 0:
                    # Can't find the first symbol in the the dictionary so
                    # return the terminator.
                    return [], self.terminator

                # Can't find a symbol in the the dictionary so return
                # the previous symbol on which we got a match.
                return [], sequence[n - 1]

            if self.terminator not in sub_tree:
                # Got to the end of the sequence but the sub-dictionary doesn't
                # contain a terminator key which means
                # there's no actual entry for the sequence.

                return [], item
            return sub_tree[self.terminator], item

    def set_translations(self, translations):
        """
        Set the dictionary translations
        param translations: The entry_id we want the translations for
        """
        if not self.__is_valid_translations(translations):
            raise DictionaryTreeException(
                'Parameter translations is not a non-empty dict in' +
                ' method set_translations')
        # Work out the supported languages
        self.languages = list(
            translations[list(translations.keys())[0]]['translations'].keys()
            )
        self.translations = translations

    def get_entry_combinations(self, sequence):
        """
        @TODO BROKEN
        Finding combinations of non-overlapping dictionary entries in a sequence
        Beware the combinatorial explosion
        """
        return []
        # Create a queue containing references and queries.
        # Initialise the queue
        # if len(sequence) == 0:
        #     return []
        # entries = list(self.get_entries_in_sequence(sequence))
        # queue = []
        # for i, t in enumerate(entries):
        #     queue.append(([t], entries[(i + 1):]))

        # output = []
        # while len(queue) > 0:
        #     refs, queries = queue.pop(0)
        #     non_overlapping = self.__get_non_overlaps(refs, queries)
        #     for i, x in enumerate(non_overlapping):
        #         new_refs = refs + [x]
        #         output.append([r[0:3] for r in new_refs])
        #         if len(non_overlapping) > 1:
        #             queue.append((new_refs, non_overlapping[(i + 1):]))
        # return output

    def get_tuples(self):
        '''
        USE WITH CAUTION ON SMALL TREES ONLY
        Create a queue of combinations of keys that we need to look at. Pop the
        first one off the queue, check whether these keys lead to another
        nested dict or not. If they do, for each key in the nested dictionary,
        add to the queue the combination we are looking at plus the new key.
        If not, add the combination to the return list. When the queue is empty,
        return.
        '''
        to_process = [(k,) for k in self.tree.keys()]
        tuples = []
        while len(to_process) > 0:
            keys = to_process.pop(0)
            d = self.tree[keys[0]]
            if len(keys) > 0:
                for k in keys[1:]:
                    d = d[k]
            if not isinstance(d, dict):  # Can change the stopping condition
                tuples.append(keys)
            else:
                for k in d.keys():
                    to_process.append(keys + (k,))
        return tuples

    def serialize(self, file_name):
        """
        Serialize the tree as JSON to a file
        param file_name: The serialised dictionary_tree's file name
        """
        try:
            if len(file_name) == 0:
                raise DictionaryTreeException(
                    'Parameter file_name is empty in method serialize')
            serialized_object = {
                'tree': self.tree,
                'translations': self.translations
            }
            with open(file_name, 'w') as outfile:
                json.dump(serialized_object, outfile)
            outfile.close()
        except Exception as e:
            message = str(e) + ' in method serialize'
            raise DictionaryTreeException(message)

    def deserialize(self, file_name):
        """
        Deseralize the from JSON to a dict object
        param file_name: The serialised dictionary_tree's file name
        """
        try:
            if len(file_name) == 0:
                raise DictionaryTreeException(
                'Parameter file_name is empty in method deserialize')
            with open(file_name) as json_data:
                serialized_object = json.load(json_data)
                self.tree = serialized_object['tree']
                self.translations = serialized_object['translations']
            json_data.close()
        except Exception as e:
            message = str(e) + ' in method deserialize'
            raise DictionaryTreeException(message)

    def __search_words(self, sequence, match='contains'):
        """
        Private method that searches for a sequence within glyph words in the
        translation dictionary.
        param sequence: The sequence to search for
        return list of translation dictionary keys
        """
        entries = []
        # Convert to lowercase
        sequence = [s.lower() for s in sequence]
        n = len(sequence)
        for key, value in self.translations.items():
            # Convert to lowercase
            word = [s.lower() for s in value['word']]
            if match == 'exact':
                if sequence == word:
                    entries.append(key)
            if match == 'starts_with':
                if sequence == word[0:n]:
                    entries.append(key)
            if match == 'contains':
                if any(
                    (sequence == word[i: i + n]) for i in range(
                        len(word) - n + 1)):
                    entries.append(key)
        return entries

    def __search_translations(self, term, lang='transliteration'):
        """
        Private method that finds all glyph codes with translation containing
        term.
        Errors in the definition of lang should be dealt with by the caller
        param term: The string to search for in the target language translation
        param lang: The language of term. Defaults to transliteration
        return list of glyph code words
        """
        results = []
        for key, value in self.translations.items():
            if isinstance(value['translations'][lang], str):
                # Converting to lowercase
                if term.lower() in value['translations'][lang].lower():
                    results.append(self.translations[key])
        return results

    def __get_sequence_entries(self, sequence):
        """
        Private method that implements a sliding window of variable length in
        order to find dictionary entries for contiguous sections of a sequence.
        The dictionary entry IDs are used to label each symbol in the
        sequence.
        Multiple labels may be applied to the same symbol in a sequence.
        param sequence: The sequence to label
        return A dictionary where key is a tuple comprising:
        - a tuple of symbol IDs
        - a tuple defining the start and end positions of the symbols in the
            sequence.
        and the value is a dictionary containing a tuple of dictionary entry IDs
        """
        entries = []
        for n in range(0, len(sequence)):
            for i in range(n + 1, len(sequence) + 1):
                entry_ids, _ = self.has_tree_entry(sequence[n:i])
                if len(entry_ids) > 0:
                    entries.append(
                        (tuple(sequence[n:i]), (n, i - 1), tuple(entry_ids)))
        return entries

    def __get_sub_tree(self, key_list):
        """
        Get a sub-tree of tree
        param key_list: An ordered list of keys for defining the path to the
            nested sub-tree. If empty then we are at the root of the tree.
        return dictionary: Empty if the sub-tree doesn't exist otherwise a
            non-empty sub-tree.
        """
        if len(key_list) == 0:
            return self.tree
        for i, item in enumerate(key_list):
            if i == 0:
                sub_tree = self.tree.get(item, None)
            else:
                sub_tree = sub_tree.get(item, None)
            if sub_tree is None:
                return {}
        return sub_tree

    def __initialise(self, lowercase):
        """
        Initialise entries and translations to empty dicts
        """
        self.tree = {}
        self.translations = {}
        self.languages = []
        self.lowercase = lowercase

    def __is_populated(self):
        """
        Check whether or not a tree is populated (note the validity of the
            entries and translation is not tested).
        return Boolean
        """
        if len(self.tree) == 0:
            return False
        if len(self.translations) == 0:
            return False
        return True

    def __is_valid_sequence(self, sequence):
        """
        Check whether or not sequence is a non-empty list
        param sequence: Contains the value of sequence we are checking
        return Boolean
        """
        if not isinstance(sequence, list):
            return False
        if len(sequence) == 0:
            return False
        return True

    def __is_valid_translations(self, translations):
        """
        Basic validation that checks whether or not translations is a
        non-empty list.
        param translations: Contains the value of translations we are checking
        return Boolean
        """
        if not isinstance(translations, dict):
            return False
        if len(translations) == 0:
            return False
        return True

    def __is_valid_entries(self, entries):
        """
        Basic validation that checks whether or not entries is a non-empty dict
        param entries: Contains the value of entries we are checking
        return Boolean
        """
        if not isinstance(entries, dict):
            return False
        if len(entries) == 0:
            return False
        return True

    def __is_valid_entry(self, entry):
        """
        Check whether or not an entry is a non-empty tuple
        param entry: Contains the value of entry we are checking
        return Boolean
        """
        if not isinstance(entry, tuple):
            return False
        if len(entry) == 0:
            return False
        return True

    def __is_valid_entry_id(self, entry_id):
        """
        Check whether or not an entry_id is a non-empty string or an integer
        param entry_id: Contains the value of entry_id we are checking
        return Boolean
        """
        if not isinstance(entry_id, str) and not isinstance(entry_id, int):
            return False
        if isinstance(entry_id, str) and len(entry_id) == 0:
            return False
        return True

    @staticmethod
    def __get_non_overlaps(refs, queries):
        # Use bitwise operations to check for overlaps
        non_overlaps = []

        # Combine all the "reference" words into an int with 1s in the positions
        # where letters are included
        ref_bitmask = 0
        for r in refs:
            #s, pos = r[0:2]
            pos = r[0]
            for p in range(pos[0], pos[1] + 1):
                ref_bitmask = ref_bitmask | (1 << p)

        # For each "query" word, create a bitmask in the same way
        for q in queries:
            query_bitmask = 0
            #s, pos = q[0:2]
            pos = q[0]
            for p in range(pos[0], pos[1] + 1):
                query_bitmask = query_bitmask | (1 << p)

            # If there is no overlap between the combined refs and the query,
            # then the OR of the two is equal to the XOR
            if (ref_bitmask | query_bitmask) == (ref_bitmask ^ query_bitmask):
                non_overlaps.append(q)

        return non_overlaps

    @staticmethod
    def __get_tree_list(tree, tree_list=None, depth=0):
        """
        Depth-first traversal of the tree to build a list of entries and their
        depths.
        param tree_list: The list we are building
        param depth: Depth of an entry
        return List of list where each inner list
            comprises [<entry>,<entry_depth>]
        """
        if tree_list is None or not isinstance(tree_list, list):
            tree_list = []

        for key, value in tree.items():
            if isinstance(value, dict):
                tree_list.append([key, depth])
                DictionaryTree.__get_tree_list(value, tree_list, depth + 1)
        return tree_list
