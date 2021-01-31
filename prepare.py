from pytrie import SortedStringTrie as Trie
import re
import glob
from dataclasses import dataclass
import pickle
from threading import Thread
from datetime import datetime
from utils import get_mistakes_by_penalty


@dataclass
class AutoCompleteData:
    completed_sentence: str
    source_text: str
    offset: int
    score: int
    line_num: int

    def __str__(self):
        return  "SENTENCE IS: " + self.completed_sentence + \
                "FROM SRC FILE: " + self.source_text + \
                ", SCORE IS: " + str(self.score) + \
                ", IN OFFSET: " + str(self.offset) + "\n--------"


#
# class Observer():
#
#     def update(self, auto_complete, **kwargs):
#         '''update is called in the source thread context'''
#         pass
#         # Thread(target=self.handler, args=(self, auto_complete), kwargs=kwargs).start()
#
#     def handler(self, auto_complete, **kwargs):
#        '''handler runs in an independent thread context'''
#        with open("auto_complete_with_repairs.pkl", "wb") as pkl_file:
#            pickle.dump(auto_complete, pkl_file)


class AutoComplete:
    MAXIMUM_NUM_CHARS = 10
    NUM_OF_SUGGESTIONS = 5

    def __init__(self):
        self.full_match = Trie()
        self.repairs_match = Trie()
        self.full_sentences = {}

    def prepare_full_match(self, folder_path):
        count = 0
        for file in glob.glob(folder_path + "/**/*.txt", recursive=True):  # os.listdir(folder_path):
            count += 1
            print(count, file)
            with open(file, "r", encoding="utf8") as txt_file:
                for line_num, sen in enumerate(txt_file):
                    if len(sen) > 1:
                        self.process_line(file, sen, line_num)
        print("count", count)

    def process_line(self, file, sen, line_num):
        try:
            cleaned_line = AutoComplete.clean_line(sen)
            cleaned_line_in_words = cleaned_line.split()
            has_insert_flag = False
            for i in range(len(cleaned_line_in_words) - 1):
                tmp_line = " ".join(cleaned_line_in_words[i:])
                if self.sentence_exist_for_prefix(sen, tmp_line[:AutoComplete.MAXIMUM_NUM_CHARS]):
                    continue
                has_insert_flag = self.insert_full_match_sentence(file, tmp_line[:AutoComplete.MAXIMUM_NUM_CHARS], line_num) or has_insert_flag
            if has_insert_flag:
                self.full_sentences[(file, line_num)] = sen
        except:
            print("ERROR", sen)
            raise

    def sentence_exist_for_prefix(self, sen, prefix):
        try:
            for _tuple in self.full_match[prefix]:
                tmp_sen = self.full_sentences[_tuple]
                if sen.find(tmp_sen) > -1 or tmp_sen.find(sen) > -1:
                    return True
            return False
        except:
            return False

    def insert_full_match_sentence(self, filename, cropped, line_num):
        try:
            sug_len = len(self.full_match[cropped])
        except:
            self.full_match[cropped] = []
            sug_len = 0

        if sug_len < AutoComplete.NUM_OF_SUGGESTIONS:
            self.full_match[cropped].append((filename, line_num))
            return True
        return False

    def __call__(self, prefix, mode="online"):
        clean_prefix = AutoComplete.clean_line(prefix)
        sugs = []
        i = 0

        # get data from full matched
        arr_of_tuples = self.full_match.items(prefix=clean_prefix)[:AutoComplete.NUM_OF_SUGGESTIONS]
        for arr in arr_of_tuples:
            for suggestion in arr[1]:
                sugs.append(self.get_auto_complete_data(suggestion, clean_prefix))
                i += 1
                if i >= AutoComplete.NUM_OF_SUGGESTIONS:
                    return sugs
        print(len(sugs))

        # get data from repairs trie - have sort #TODO - have to sort
        arr_of_tuples = self.repairs_match.items(prefix=clean_prefix)[:AutoComplete.NUM_OF_SUGGESTIONS]
        for arr in arr_of_tuples:
            for suggestion in arr[1]:
                sugs.append(self.get_auto_complete_data(suggestion, clean_prefix))
                i += 1
                if i >= AutoComplete.NUM_OF_SUGGESTIONS:
                    return sugs
        print(len(sugs))

        if i < AutoComplete.NUM_OF_SUGGESTIONS and mode == "prepare":
            repairs_sugs = self.predict_prefix_and_update_from_repairs_trie(clean_prefix, AutoComplete.NUM_OF_SUGGESTIONS - i)
            for repair in repairs_sugs:
                self.update_repair_sentence(clean_prefix, repair)
            sugs += repairs_sugs

        return sugs

    def update_repair_sentence(self, prefix, repair_data):
        try:
            sug_len = len(self.repairs_match[prefix])
        except:
            self.repairs_match[prefix] = []
            sug_len = 0

        if sug_len < AutoComplete.NUM_OF_SUGGESTIONS:
            self.repairs_match[prefix].append((repair_data.source_text, repair_data.line_num, repair_data.offset, repair_data.score))
            # print(prefix, repair_data)

    def predict_prefix_and_update_from_repairs_trie(self, prefix, amount = NUM_OF_SUGGESTIONS, mode="offline"):
        options = get_mistakes_by_penalty(prefix)
        amount_found = 0
        suggestions = []
        for option, penalty in options:
            arr_of_tuples = self.full_match.items(prefix=option)[:AutoComplete.NUM_OF_SUGGESTIONS]
            for arr in arr_of_tuples:
                for suggestion in arr[1]:
                    # if mode == "realtime":
                    suggestions.append(self.get_auto_complete_data(suggestion, option, penalty))
                    amount_found += 1
                    if amount_found >= amount:
                        return suggestions
        return suggestions

    @staticmethod
    def clean_line(sentence):
        sentence2 = re.sub(r'\W+', ' ', sentence.lower().strip())
        sentence2 = re.sub(' +', ' ', sentence2)
        return sentence2

    def get_auto_complete_data(self, file_line_tuple, clean_prefix, penalty=0, mode="full_match"):
        if mode == "full_match":
            filename, line_num = file_line_tuple
            full_sentence = self.full_sentences[file_line_tuple]
            score = 2 * len(clean_prefix) - penalty  # TODO
            offset = AutoComplete.clean_line(full_sentence).find(clean_prefix)
        else:
            filename, line_num, offset, score = file_line_tuple
            full_sentence = self.full_sentences[(filename, line_num)]
        return AutoCompleteData(full_sentence, filename, offset, score, line_num)

    def observer_update_function(self):
        thread = Thread(target=self.save_to_pkl, args=(self,))
        thread.start()

    def save_to_pkl(self, *args):
        now = datetime.now()  # current date and time
        date_time = now.strftime("%d_%m_%Y__%H_%M_%S")

        with open(f"pkl_files_updated/auto_complete_with_repairs_{date_time}.pkl", "wb") as pkl_file:
            pickle.dump(self, pkl_file)


def create_auto_complete_full_match():
    auto_complete = AutoComplete()
    auto_complete.prepare_full_match("Archive")

    with open("auto_complete.pkl", "wb") as pkl_file:
        pickle.dump(auto_complete, pkl_file)

    return auto_complete


def get_best_k_completions(prefix: str, auto_complete):
    return auto_complete(prefix)


def insert_all_combos(auto_complete):
    all_alphabet = "abcdefghijklmnopqrstuvwxyz"
    all_alphabet_nums_space = all_alphabet + " "  # + "1234567890 "
    for char1 in all_alphabet:
        for char2 in all_alphabet_nums_space:
            for char3 in all_alphabet_nums_space:
                if char2 == " " and char3 == " ":
                    continue
                for char4 in all_alphabet_nums_space:
                    if char3 == " " and char4 == " ":
                        continue
                    for char5 in all_alphabet_nums_space:
                        if char4 == " " and char5 == " ":
                            continue
                        option = char5 + char2 + char3 + char4 + char1
                        print("OPTION", option)
                        auto_complete(option, mode="prepare")
                auto_complete.observer_update_function()


if __name__ == '__main__':

    # auto_complete = create_auto_complete_full_match()
    with open("auto_complete.pkl", "rb") as pkl_file:
        auto_complete = pickle.load(pkl_file)

    # insert_all_combos(auto_complete)
        print("hi")
        print(auto_complete("sara dic"))
    #
    # with open("auto_complete_with_repairs.pkl", "wb") as pkl_file:
    #     pickle.dump(auto_complete, pkl_file)

    #
    # str_in = input("enter text to auto complete:\n--type exit to exit.\n")
    # while str_in != "exit":
    #     suggestions = auto_complete(str_in)
    #     if suggestions is None:
    #         print("NO RESULTS!\n\n")
    #     else:
    #         for s in suggestions:
    #             print(s)
    #     str_in = input("\n -----------------\nenter text to auto complete:\n--type exit to exit.\n")
    #
