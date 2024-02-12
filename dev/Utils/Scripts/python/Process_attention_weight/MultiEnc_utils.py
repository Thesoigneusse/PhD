import json
import torch
import copy
import doctest

def ajoute_eos_tokens(_crt: list, _ctxs: list, eos_token: str = "<eos>") -> tuple:
    """Ajoute un token end-of-sentence dans la phrase courante et de contexte afin de faire concorder la taille de la matrice et de la phrase

    Args:
        _crt (list): list de token de la phrase côté source
        _ctxs (list): list des phrases de contexte
        eos_token (str, optional): token end-of-sentence. Defaults to "<eos>".

    Returns:
        list: list de tokens des phrases avec les tokens end-of-sentence
    """

    crt = copy.deepcopy(_crt)
    ctxs = copy.deepcopy(_ctxs)
    # Si on a des éléments à ajouter
    crt.append(eos_token)
    for i in range(len(ctxs)):
        ctxs[i].append(eos_token)
        

    return crt, ctxs