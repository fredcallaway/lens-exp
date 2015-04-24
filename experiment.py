"""Evaluates net performance on an experiment"""
from random import random
import logging
from scipy import stats


def get_error(trial):
    """Returns float: the total error of one trial

    Args:
      trial str: lens output for one trial"""
    # lines = trial.split('\n')
    # error_line = re.search(r'Err.*', trial).group(0)
    # error = re.search(r'[0-9.]+', error_line).group(0)
    # return float(error)

    examples = trial.split('\n')[3:-1]
    try:
        errors = [float(e.split('   ')[1]) for e in examples]
    except:
        errors = [float(e.split('   ')[2]) for e in examples]
    return sum(errors)


def get_network_choices(trial_errors):
    """Returns ([int], [float]): choices and reaction time
    choices is a list of 0 or 1 corresponding to word indices in one trial
    reaction time is a list of floats

    Args:
      trial_errors [(float, float)]: each tuple represents
        the reaction times for the two words in a trial
    """
    # pairs of consecutive words correspond to trials
    

    def choose(pair):
        # p(choose word1) = error2/(error1+error2)
        threshold = pair[0]/sum(pair)
        choice =  0 if random() > threshold else 1
        # reaction time is inverse of percentage difference between values
        rt = 1 / (abs(pair[0]-pair[1])/(sum(pair)/2))
        return (choice, rt)

    results = [choose(p) for p in trial_errors]
    choices = [r[0] for r in results]
    reaction_times = [r[1] for r in results]
    return choices, reaction_times


def get_correct_choices():
    """Returns [int]: tuple index of correct word for each trial"""
    with open('experiment/answer-key.txt', 'r') as f:
        key = f.read()
    key = key.split('\r')
    key = map(int, key)
    return key


def test_word_choices(choices):
    """Returns [int]: indices of trials net was incorrect for

    Args:
      choices: [int] network's word choices, 1 or 0"""
    key = get_correct_choices()
    assert len(choices) == len(key)
    incorrect = []
    for i in xrange(len(key)):
        if choices[i] != key[i]:
            incorrect.append(i)
    return incorrect
    

def run_one(out, ntrials=1000):
    """Returns accuracy and word errors for one condition"""
    runs = out.split('***')[1:]
    errors = [get_error(run) for run in runs]
    # put errors into pairs corresponding to trials
    trial_errors = [(errors[i], errors[i+1]) for i in xrange(0, len(errors), 2)]
    accuracies = []
    for t in xrange(ntrials):
        choices, reaction_times = get_network_choices(trial_errors)
        incorrect = test_word_choices(choices)
        accuracies.append(1 - float(len(incorrect)) / len(choices))
    d = stats.describe(accuracies)
    accuracy_mean, accuracy_std = d[2], d[3]**0.5
    return accuracy_mean, accuracy_std, trial_errors, reaction_times

def evaluate_experiment(lens_output):
    """Returns dict of net's performance on both word choice conditions

    Args:
      lens_output (str): lens output"""
    logging.debug('============================================================')
    logging.debug(lens_output)
    logging.debug('============================================================')
    with open('experiment-log.out', 'w+') as f:
        f.write(lens_output)

    A, B = map(run_one, lens_output.split('######'))

    results = {'expA_accuracy' : A[0],
               'expB_accuracy' : B[0],
               'expA_std' : A[1],
               'expB_std' : B[1],
               'expA_errors' : A[2],
               'expB_errors' : B[2],
               'expA_reaction': sum(A[3]) / len(A[3]),
               'expB_reaction': sum(B[3]) / len(B[3]),
               'expA_rts' : A[3],
               'expB_rts' : B[3],
               }
    return results


if __name__ == '__main__':
    with open('experiment-log.out', 'r') as f:
        res =  evaluate_experiment(f.read())
        print res['expA_std'], res['expB_std']