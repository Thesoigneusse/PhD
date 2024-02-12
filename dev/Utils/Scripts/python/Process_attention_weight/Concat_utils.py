import torch
import copy
import doctest

def find_eos_tokens(_snt: list, eos_token: str = "<eos>") -> list:
    """Permet d'obtenir une liste des positions des tokens end-of-sentence

    Args:
        _tokens (list): list des tokens de la phrase
        end_of_sentence_token (str, optional): Token end-of-sentence. Defaults to "<eos>".

    Returns:
        list: list des positions des tokens end-of-sentence
    """
    # Retourne une liste de position des tokens de "<eos>"
    snt = copy.deepcopy(_snt)
    pos_eos = []
    for i, token in enumerate(snt):
        if token == eos_token:
            pos_eos.append(i)
    return pos_eos

def ajoute_eos_tokens_src(_snt: list, src_segments_labels: list, eos_token: str = "<eos>") -> list:
    """Ajoute un token end-of-sentence dans la phrase afin de faire concorder la taille de la matrice et de la phrase

    Args:
        _snt (list): list de token de la phrase côté source
        src_segments_labels (list): list d'id de contexte pour chaque token de la phrase _snt
        eos_token (str, optional): token end-of-sentence. Defaults to "<eos>".

    Returns:
        list: list de tokens de la phrase coté source avec les tokens end-of-sentence
    """
    assert len(_snt) <= len(src_segments_labels), f"[DEBUG]Longueur error, len(snt) vs. len(labels): {len(_snt)} vs. {len(src_segments_labels)}"
    snt = copy.deepcopy(_snt)
    # Si on a des éléments à ajouter
    if len(snt) < len(src_segments_labels):
        # Parcours de src_segments_label
        for i in range(len(src_segments_labels) - 1):
            # Si on trouve un changement de segments alors on ajoute un token <eos>
            if src_segments_labels[i] != src_segments_labels[i+1]:
                snt.insert(i, eos_token)
    assert len(snt) == len(src_segments_labels)
    return snt

def ajoute_eos_tokens_tgt(_snt, tgt_segments_labels, eos_token = "<eos>"):
    """Ajoute un token end-of-sentence dans la phrase afin de faire concorder la taille de la matrice et de la phrase coté target

    Args:
        _snt (_type_): list de token de la phrase coté target
        tgt_segments_labels (_type_): list des position où ajouter le eos_token
        eos_token (str, optional): token end-of-sentence. Defaults to "<eos>".

    Returns:
        list: list de tokens de la phrase coté target avec les tokens end-of-sentence
    """
    snt= copy.deepcopy(_snt)
    for position in tgt_segments_labels:
        snt.insert(int(position[1:-1]), eos_token)
    return snt

def full_sentence_to_ctx_and_crt(_snt: list, eos_token: str = "<eos>"):
    """Découpe une liste de tokens contenant plusieurs phrases en une liste de phrase où chaque phrase correspond à une liste de tokens

    Args:
        _snt (list): list de tokens de phrases
        eos_token (str, optional): Token end-of-sentence. Defaults to "<eos>".

    Returns:
        list: liste de phrases
    """
    snt = copy.deepcopy(_snt)
    list_sentence = [[]]
    for i in range(len(snt)): # On parcourt la liste des tokens
        if snt[i] == eos_token: 
            # Si on rencontre un token <eos> alors on l'ajoute puis créé une autre phrase
            list_sentence[-1].append(eos_token)
            list_sentence.append([])
        else:
            # Sinon on ajoute le token courant à la denière phrase
            list_sentence[-1].append(snt[i])
    return list_sentence


def cut_matrix_into_sentences(_matrice: torch.DoubleTensor, snts: list) -> tuple:
    """Découpe une matrice ctx+crt de self-attention en différentes matrices k3 x k3, k3 x k2, ..., k0 x k0

    Args:
        _matrice (torch.DoubleTensor): Matrice de self-attention ctx+crt x ctx + crt
        snts (list): list de phrase (elles même liste de token)

    Returns:
        list: liste de dictionnaire contenant "ctx" pour la phrase de contexte, "crt" pour la phrase courante et "matrix" pour la matrice de poids "crt" x "ctx"
    """
    assert _matrice.size(dim=0) == sum([len(snt) for snt in snts]), f"[DEBUG]Size error, matrice size dim0 vs. snt len: {_matrice.size()} vs. {sum([len(snt) for snt in snts])}"
    assert _matrice.size(dim=1) == sum([len(snt) for snt in snts]), f"[DEBUG]Size error, matrice size dim1 vs. snt len: {_matrice.size()} vs. {sum([len(snt) for snt in snts])}"
    debut_row, fin_row = 0, 0
    matrices = []
    # Pour chaque ligne
    for i in range(len(snts)):
        fin_row += len(snts[i])
        debut_col, fin_col = 0, 0
        # temp: liste temporaire
        temp = []
        # Pour chaque colonne
        for j in range(len(snts)):
            fin_col += len(snts[j])
            # On ajoute les éléments de la matrice dans la liste temporaire
            temp.insert(0, {
                "crt": copy.deepcopy(snts[i]),
                "ctx": copy.deepcopy(snts[j]),
                "matrix": copy.deepcopy(_matrice[
                    debut_row:fin_row,
                    debut_col:fin_col
                ])
            })
            debut_col = fin_col
        matrices.insert(0, copy.deepcopy(temp))
        debut_row = fin_row
    return matrices

