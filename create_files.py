"""Creates LENS training and testing files"""
import csv


def get_corpus(lang, word_boundaries=False):
    """Returns str: corpus as continuous string of phonemes and utterance boundaries"""
    with open('corpora/%s-corpus.txt' % lang, 'r') as f:
        corpus = f.readlines()
    if lang is 'cas98':
        corpus = [line[:line.find('\t')] for line in corpus]  # remove stress
        if word_boundaries:
            corpus = 'X'.join(corpus)
            corpus = corpus.replace('#X', '#')
            corpus = corpus.replace('X#', '#')
        else:
            corpus = ''.join(corpus)
        corpus = corpus.replace('/', '')
        corpus = corpus.replace('E', 'e')

    else:
        corpus = [line[1:-1] for line in corpus]  # remove leading Q and \n
        corpus = ''.join(corpus)
        if not word_boundaries:
            corpus = corpus.replace('X', '')
        corpus = corpus.replace('QX', 'Q')
        corpus = corpus.replace('XQ', 'Q')
        corpus = corpus.replace('\r', '')
        corpus = corpus.replace('QQ', 'Q')
    return corpus


# def convertSampa(corpus):
#     """Convert Danish SAMPA to our SAMPA and remove word boundaries"""
#     corpus = corpus.replace('0', '@')
#     corpus = corpus.replace('U', 'V')
# corpus = corpus.replace('Y', '2')
# other stuff
#     return corpus

# def convertArpabet(corpus):
#     """convert arpabet to our SAMPA"""
#     with open('arpabet.csv','r')  as f:
#         reader = list(csv.reader(f))
#         arpadict= {row[0]:row[1:] for row in reader[1:]}
# todo: how is the corpus formated?
#     return corpus

def get_encodings(lang, distributed):
    """Returns tuple with input and output neuron mappings for `lang`"""

    if lang is 'cas98':
        if distributed:
            # read distributed encodings
            with open('encodings/cas98-distributed.csv', 'r') as f:
                reader = list(csv.reader(f))
                distributed_encoding = {row[0]: '0 ' + str(row[1:]).translate(
                                          None, ",[]'") for row in reader[1:]}
                distributed_encoding['#'] = '1' + ' 0' * len(reader[0][1:])

        # read localist encodings (output is always localist)
        with open('encodings/cas98-distributed.csv', 'r') as f:
            reader = list(csv.reader(f))
            localist_encoding = {}
            for i, row in enumerate(reader[1:]):
                localist_encoding[row[0]] = str(i + 1)
                localist_encoding['#'] = '0'

    else:
        # TODO: handle distributed input
        assert not distributed
        # with open('encodings/NULL.csv','r')  as f:
        #     reader = list(csv.reader(f))
        #     distributed_encoding = {row[0]:'0 '+str(row[1:]).translate(None,",[]'")
        #                             for row in reader[1:]}
        # distributed_encoding['Q'] = '1' #+' 0'*len(reader[0][1:])

        with open('encodings/%s-localist.csv' % lang, 'r') as f:
            reader = list(csv.reader(f))
            # assuming csv has a header, we ignore first row
            localist_encoding = {row[0]: row[1] for row in reader[1:]}
    incoding = distributed_encoding if distributed else localist_encoding
    outcoding = localist_encoding
    return (incoding, outcoding)


def create_training_files(lang, corpus, num_train, num_test,
                          incoding, outcoding, distributed):
    """Populates lens/ with .ex files for training and testing segmentation

    Returns int: the number of training examples"""

    # make test file
    test_file = 'lens/test.ex'
    with open(test_file, 'w+') as f:
        for c in range(num_test):
            i = corpus[c]
            t = corpus[c + 1]
            write_example(f, i, t, incoding, outcoding, distributed)

    # make training file
    train_file = 'lens/train.ex'
    with open(train_file, 'w+') as f:
        c = num_test  # start where we left off
        while c < num_test + num_train:
            i = corpus[c]
            try:
                t = corpus[c + 1]
            except IndexError:
                # no more examples
                break
            write_example(f, i, t, incoding, outcoding, distributed)
            c += 1
    return c - num_test  # the number of training examples


def creat_exp_files(lang, incoding, outcoding, distributed):
    """Populates lens/ with .ex files for the experiment"""

    for exp in ('A', 'B'):
        # write training file
        with open('experiment/{0}/train{1}.txt'.format(lang, exp), 'r') as f:
            exp_training = f.read()
        train_file = 'lens/exp-train%s.ex' % exp
        with open(train_file, 'w+') as f:
            k = 0
            while True:  # use all examples
                i = exp_training[k]
                try:
                    t = exp_training[k + 1]
                except IndexError:
                    # no more examples
                    break
                write_example(f, i, t, incoding, outcoding, distributed)
                k += 1

        # create test files
        with open('experiment/{0}/test{1}.txt'.format(lang, exp), 'r') as f:
            trials = f.read()
        trials = trials.replace('\r', '')
        trials = trials.replace('\n', '')
        trials = trials.replace('QQ', 'Q')
        trials = trials.split('Q')[1:-1]
        trials = [t + 'Q' for t in trials]
        # if this changes, make sure to change all 72's in project files
        assert len(trials) is 72
        for k, trial in enumerate(trials):
            with open('lens/exp-test%s%s.ex' % (exp, k), 'w+') as f:
                for j in xrange(len(trial) - 1):
                    i = trial[j]
                    t = trial[j + 1]
                    write_example(f, i, t, incoding, outcoding)


def write_example(f, i, t, incoding, outcoding, distributed=False):
    """Writes one example to a .ex file"""
    f.write('name: {%s -> %s}\n' % (i, t))
    f.write('1\n')
    # upper case letter indicates dense encoding
    if distributed:
        f.write('I: ' + incoding[i] + ' t: ' + outcoding[t] + ';\n')
    else:
        f.write('i: ' + incoding[i] + ' t: ' + outcoding[t] + ';\n')


def write_example_files(lang, distributed, num_train, num_test=1000):
    """Populates lens/ with .ex files for training, testing, and experiment"""
    corpus = get_corpus(lang)
    incoding, outcoding = get_encodings(lang, distributed)
    num_examples = create_training_files(lang, corpus, num_train, num_test,
                                         incoding, outcoding, distributed)
    creat_exp_files(lang, incoding, outcoding, distributed)

    return num_examples, incoding, outcoding

if __name__ == '__main__':
    # for debugging
    print write_example_files('english', 'B', False, 900000)
