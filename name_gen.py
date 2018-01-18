"""
generate a language for naming people, things and places

basic idea:
    a. create a inventory of the sounds in the language (a list of phonemes)
    b. transliterate the phones by specifying an orthography
"""

import collections
import random as rd
import re
import sys


# === syllable generation ===
CON_SETS = [
    'ptkmnsl',
    'ptkmnh',
    'ptkbdgmnlrsʃzʒʧ',
    'hklmnpwʔ',
    'ptkqvsgrmnŋlj',
    'tksʃdbqɣxmnlrwj',
    'tkdgmnsʃ',
    'ptkbdgmnszʒʧhjw'
]

# additional consonant sets for more variation
CON_SIB = [  # sibilants
    's',
    'sʃ',
    'sʃf'
]

CON_LIQ = [  # liquids
    'rl',
    'r',
    'l',
    'wj',
    'lrwj'
]

CON_FIN = [  # finals
    'mn',
    'sk',
    'mnŋ',
    'sʃzʒ'
]

VOW_SETS = [
    'aeiou',
    'aiu',
    'aeiouAEI',
    'aeiouU',
    'aiuAI',
    'eou',
    'aeiouAOU'
]

SYLL_PATTERNS = [
    'CVC',
    'CVV?C',
    'CVVC?', 'CVC?', 'CV', 'VC', 'CVF', 'C?VC', 'CVF?',
    'CL?VC', 'CL?VF', 'S?CVC', 'S?CVF', 'S?CVC?',
    'C?VF', 'C?VC?', 'C?VF?', 'C?L?VC', 'VC',
    'CVL?C?', 'C?VL?C', 'C?VLC?'
]

RESTRICTIONS = ['ss', 'ʃʃ', 'ʃs', 'sʃ', 'fs', 'fʃ', 'lr', 'rl', r'(.)\1']


# === orthography ===
# standard orthography that is modified with aesthetically coherent sets
ORTHO_DEFAULT = {
    'ʃ': 'sh',
    'ʒ': 'zh',
    'ʧ': 'ch',
    'ʤ': 'j',
    'ŋ': 'ng',
    'j': 'y',
    'x': 'kh',
    'ɣ': 'gh',
    'ʔ': '‘',
    'A': "á",
    'E': "é",
    'I': "í",
    'O': "ó",
    'U': "ú"
}

CON_ORTHO = [
    {'default': 'None'},
    {
        'ʃ': 'š',
        'ʒ': 'ž',
        'ʧ': 'č',
        'ʤ': 'ǧ',
        'j': 'j'
    },
    {
        'ʃ': 'sch',
        'ʒ': 'zh',
        'ʧ': 'tsch',
        'ʤ': 'dz',
        'j': 'j',
        'x': 'ch'
    },
    {
        'ʃ': 'ch',
        'ʒ': 'j',
        'ʧ': 'tch',
        'ʤ': 'dj',
        'x': 'kh'
    },
    {
        'ʃ': 'x',
        'ʧ': 'q',
        'ʤ': 'j'
    }
]

VOW_ORTHO = [
    {'default': 'None'},
    {
        'A': 'ä',
        'E': 'ë',
        'I': 'ï',
        'O': 'ö',
        'U': 'ü'
    },
    {
        'A': "au",
        'E': "ei",
        'I': "ie",
        'O': "ou",
        'U': "oo"
    },
    {
        'A': "â",
        'E': "ê",
        'I': "y",
        'O': "ô",
        'U': "w"
    },
    {
        'A': "aa",
        'E': "ee",
        'I': "ii",
        'O': "oo",
        'U': "uu"
    }
]


class Orthography(collections.Mapping):
    ortho = ORTHO_DEFAULT

    def __init__(self, c_ortho=None, v_ortho=None, joiner=" "):
        self.c_ortho = c_ortho
        self.v_ortho = v_ortho
        self.joiner = joiner

        if self.c_ortho is not None:
            self.ortho.update(self.c_ortho)

        if self.v_ortho is not None:
            self.ortho.update(self.v_ortho)

        print(self.ortho)

    def __getitem__(self, key):
        return self.ortho[key]

    def __len__(self):
        return len(self.ortho)

    def __iter__(self):
        return self.ortho

    def __repr__(self):
        c_chars = " ".join(self.c_ortho.values())
        v_chars = " ".join(self.v_ortho.values())
        return f'{type(self).__name__}({c_chars}, {v_chars})'


class BasicLanguage:
    def __init__(
                    self, phonemes, syll='CVC', ortho=None, min_syll=1,
                    max_syll=1, restricts=RESTRICTIONS
                ):
        self.phonemes = phonemes
        self.ortho = ortho
        self.syll = syll
        self.min_syll = min_syll
        self.max_syll = max_syll
        self.restricts = restricts
        self.morphemes = collections.defaultdict(list)
        self.words = collections.defaultdict(list)
        self.names = collections.defaultdict(set)

        if len(syll) < 3:
            self.min_char = len(syll) + 1
            self.max_char = len(syll) * 4
        else:
            self.min_char = len(syll)
            self.max_char = len(syll) * 3

    def gen_syllable(self):
        """Generate a random syllable according to the specified pattern.

        If the syllable is not valid, it will be re-generated.

        :param pattern: Vowel-consonant pattern of the syllable.
        """
        while True:
            phones = []
            for spec in self.syll:
                if spec == '?':
                    # 50% chance to remove the char that preceded the '?'
                    if rd.random() > 0.5:
                        phones = phones[:-1]
                else:
                    p = choose(self.phonemes[spec])
                    phones.append(p)
            syll = ''.join(phones)

            # Filter out restricted sound combinations
            for r in self.restricts:
                if re.search(r, syll):
                    break
            else:
                return self.transliterate(syll)

    def transliterate(self, syll):
        """Translate phones of a syllable to their orthographic character.

        :param syll: Syllable to be transliterated.
        """
        if self.ortho is None:
            return syll

        trans = ''
        for c in syll:
            trans += self.ortho.get(c, c)
        return trans

    def gen_word(self, pool=None):
        num_sylls = range(self.min_syll, self.max_syll+1)
        return ''.join([self.get_morpheme(pool) for syll in num_sylls])

    def get_word(self, pool=None):
        word_list = self.words[pool]
        extras = 3 if pool is None else 2
        while True:
            n = rd.randrange((len(word_list)) + extras)
            if n < len(word_list):
                return word_list[n]
            else:
                new_word = self.gen_word(pool)
                if new_word not in self.words.values():
                    break

        self.words[pool].append(new_word)
        return new_word

    def gen_name(self, pool=None):
        genitive = self.get_morpheme('of')
        definitive = self.get_morpheme('the')

        while True:
            name = None
            if rd.random() < 0.5:
                name = self.get_word(pool).capitalize()
            else:
                n_part1 = self.get_word(
                            pool if rd.random() < 0.6 else None
                            ).capitalize()
                n_part2 = self.get_word(
                            pool if rd.random() < 0.6 else None
                            ).capitalize()

                if n_part1 == n_part2:
                    continue

                if rd.random() < 0.5:
                    name = self.ortho.joiner.join([n_part1, n_part2])
                else:
                    name = self.ortho.joiner.join([n_part1, genitive, n_part2])

            if rd.random() < 0.1:
                name = self.ortho.joiner.join([definitive, name])
            if not (self.min_char <= len(name) <= self.max_char*2):
                continue

            if self.check_unique(name):
                self.names[pool].add(name)
                return name

    def check_unique(self, name):
        for cat in self.names.values():
            for other_name in cat:
                if (name in other_name) or (other_name in name):
                    return False

        return True

    def get_morpheme(self, pool=None):
        """Add a pseudo-semantic layer to the language by associating syllables
        with meaning.

        Morphemes are divided into semnantic pools (e.g. 'city', 'land') and
        a generic pool. Whenever a new word is generated, it will be composed
        of one random morpheme from its class, while the remaining are drawn
        from the generic pool.

        Initally, these pools are empty and grow only when one of its morphemes
        has not been reused. For generic morphemes, the chance to redraw is
        artifically lowered (new morphemes are generated more often), while
        words of specific word classes reuse their morphemes more frequently.

        Morphemes are inventorized to avoid doubling or cross-class occurences.

        :param pool: Morpheme pool of the word to be generated.
        """
        morph_list = self.morphemes[pool]
        # Reuse morphemes in word class pools more often than in generic pools
        extras = 10 if pool is None else 1
        while True:
            # Determine if a morpheme is going to be reused
            n = rd.randrange(len(morph_list) + extras)
            if n < len(morph_list):
                return morph_list[n]
            else:
                # Create new morpheme otherwise and check if it already exists
                new_morph = self.gen_syllable()
                if new_morph not in self.morphemes.values():
                    break

        self.morphemes[pool].append(new_morph)
        return new_morph

    def show(self):
        for pset in 'VCFLS':
            if pset in self.syll:
                print(pset, self.phonemes[pset])
        print('pattern', self.syll)
        print('ortho', self.ortho)


def choose(lst, exp=2):
    """Choose a random item from a list.

    Selection is weighted toward the lower end of the list, making
    items in that range more common than others.

    :param lst: List to choose from.
    :param exp: Exponent used for computing the weigthed index
        (higher = more weight).
    """
    index = int((rd.random()**exp) * len(lst))
    return lst[index]


def user_select(options):
    for i, option in enumerate(options):
        print(f'{i}. {option}')

    while True:
        try:
            selection = int(input(f"Choose from options: "))
        except ValueError:
            continue

        if int(selection) not in range(len(options)):
            continue
        else:
            return selection


def build_language(lang=BasicLanguage, random=True):
    if random:
        syll = choose(SYLL_PATTERNS)
        phonemes = {'C': choose(CON_SETS),
                    'V': choose(VOW_SETS),
                    'S': choose(CON_SIB),
                    'F': choose(CON_FIN),
                    'L': choose(CON_LIQ)}
        min_syll = rd.randrange(1, 3)
        max_syll = rd.randrange(min_syll+1, 6)
        c_ortho = rd.choice(CON_ORTHO)
        v_ortho = rd.choice(VOW_ORTHO)
        joiner = rd.choice('   --´:')
        ortho = Orthography(c_ortho=c_ortho, v_ortho=v_ortho, joiner=joiner)
    else:
        syll = user_select(SYLL_PATTERNS)
        phonemes = {'C': user_select(CON_SETS),
                    'V': user_select(VOW_SETS),
                    'S': user_select(CON_SIB),
                    'F': user_select(CON_FIN),
                    'L': user_select(CON_LIQ)}
        min_syll = input("Minimum word length (syllables): ")
        max_syll = input("Maximum word length (syllables): ")
        c_ortho = user_select(CON_ORTHO)
        v_ortho = user_select(VOW_ORTHO)
        ortho = Orthography(c_ortho=c_ortho, v_ortho=v_ortho, joiner=joiner)

    language = lang(
                phonemes=phonemes,
                syll=syll,
                min_syll=min_syll,
                max_syll=max_syll,
                ortho=ortho)

    return language


if __name__ == '__main__':
    if len(sys.argv) > 1:
        random = not sys.argv[1] == 'select'
    else:
        random = True

    language = build_language(random=random)
    language.show()

    for i in range(10):
        print()
        print(language.morphemes[None])
        print(language.morphemes["city"])
        print(language.morphemes["land"])
        print(language.names["city"])
        print(language.names["land"])
        print("ALL", language.names.values())
        print()
        print(language.gen_name("city"))
        print(language.gen_name("land"))
