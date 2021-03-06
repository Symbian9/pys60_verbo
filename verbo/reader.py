import key_codes
import appuifw
import codecs
import e32

from window import Dialog
from draw import Draw
from fb2parser import FB2Parser

class Reader(Dialog):

    PUNCT_MARKS = (",", ".", "-", ":", "?", "!")

    def __init__(self, cbk, book_title, book_path, last_pos):
        menu = [(u"Start", self.reader_start),
                (u"Pause", self.reader_pause),
                (u"Close book", self.close_reader)]

        self.book_title = book_title
        self.book_path = book_path
        self.pause = False
        self.currword_idx = last_pos
        self.wpm = 250
        self.init_delay()
        self.words = []
        self.words_num = 0
        self.parse_words()

        self.old_orientation = appuifw.app.orientation
        appuifw.app.orientation = "landscape"
        self.draw = Draw()

        Dialog.__init__(self,
                        cbk,
                        self.book_title,
                        self.draw.canvas,
                        menu,
                        self.close_reader)

        self.reader_pause()

    def init_delay(self):
        self.word_delay = 60. / self.wpm
        self.punct_delay = self.word_delay * 2

    def parse_words(self):
        """ Parse words from book into self.word """
        book_ext = self.book_path.split(".")[-1]

        if book_ext == "txt":
            self.parse_txt()
        elif book_ext == "fb2":
            self.parse_fb2()

        self.words_num = len(self.words)-1

    def parse_txt(self):
        book_file = codecs.open(self.book_path, "r", "utf-8")

        for line in book_file:
            for w in line.split():
                self.words.append(w)

        book_file.close()

    def parse_fb2(self):
        fb2 = FB2Parser(self.book_path)
        self.words = fb2.parse_words()

    def reader_start(self):
        self.pause = False
        self.draw.canvas.bind(key_codes.EScancode5, self.reader_pause)
        # disable rewind when reading
        self.draw.canvas.bind(key_codes.EScancode6, lambda: None)
        self.draw.canvas.bind(key_codes.EScancode4, lambda: None)
        self.draw.canvas.bind(key_codes.EScancode7, lambda: None)
        self.draw.canvas.bind(key_codes.EScancode9, lambda: None)
        self.draw.canvas.bind(key_codes.EScancodeStar, lambda: None)
        self.draw.canvas.bind(key_codes.EScancodeHash, lambda: None)
        self.start_reading()

    def reader_pause(self):
        self.pause = True
        self.draw.canvas.bind(key_codes.EScancode5, self.reader_start)
        # enable rewind when pause
        self.draw.canvas.bind(key_codes.EScancode6, lambda: self.rewind(-1))
        self.draw.canvas.bind(key_codes.EScancode4, lambda: self.rewind(1))
        self.draw.canvas.bind(key_codes.EScancode7, lambda: self.rewind(10))
        self.draw.canvas.bind(key_codes.EScancode9, lambda: self.rewind(-10))
        self.draw.canvas.bind(key_codes.EScancodeStar, self.inc_wpm)
        self.draw.canvas.bind(key_codes.EKeyHash, self.dec_wpm)
        self.display_scene()

    def inc_wpm(self):
        new_wpm = self.wpm + 50
        if new_wpm <= 1000:
            self.wpm = new_wpm
            self.init_delay()
            self.display_scene()

    def dec_wpm(self):
        new_wpm = self.wpm - 50
        if new_wpm >= 50:
            self.wpm = new_wpm
            self.init_delay()
            self.display_scene()

    def rewind(self, offset):
        new_idx = self.currword_idx + offset

        if new_idx >= 0 and new_idx <= self.words_num:
            self.currword_idx = new_idx
        elif new_idx < 0:
            self.currword_idx = 0
        elif new_idx > self.words_num:
            self.currword_idx = self.words_num

        self.display_scene()

    def display_scene(self):
        word = self.words[self.currword_idx]
        best_letter = self.best_letter_pos(word)

        self.draw.clear()
        self.draw.word(word, best_letter)
        if self.pause:
            self.draw.info(self.wpm)
        self.draw.redraw()

    def best_letter_pos(self, word):
        """ Primitive algorithm for defining focus letter """
        word_len = len(word)
        best_letter = 0

        if word_len == 1:
            best_letter = 0
        elif word_len >= 2 and word_len <= 5:
            best_letter = 1
        elif word_len >= 6 and word_len <= 9:
            best_letter = 2
        elif word_len >= 10 and word_len <= 13:
            best_letter = 3
        else:
            best_letter = 4

        return best_letter

    def check_punct(self, word):
        if word[-1] in Reader.PUNCT_MARKS:
            return True
        return False

    def start_reading(self):
        offset = self.currword_idx
        last_idx = len(self.words)-1

        for i in range(offset, last_idx):
            # when user press pause or exit from reader
            if self.pause or self.cancel:
                self.pause = False
                break

            self.currword_idx += 1
            self.display_scene()

            if self.check_punct(self.words[self.currword_idx]):
                e32.ao_sleep(self.punct_delay)
            else:
                e32.ao_sleep(self.word_delay)

        self.reader_pause()

    def close_reader(self):
        del self.words[:]
        appuifw.app.orientation = self.old_orientation
        self.cancel_app()
