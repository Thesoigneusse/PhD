import json
import torch
import copy
import doctest
import Concat_utils as cu

# Files fonctions
def lecture_data(absolute_file_path):
    """Read the data into the absolute_path file

    Args:
        absolute_path (str): absolute path to a .json file

    Returns:
        dict : dictionnary of the json file data
    """
    import mimetypes
    import json
    mime_type, encoding = mimetypes.guess_type(absolute_file_path)
    assert mime_type == "application/json", f"[DEBUG]File type error: need .json get {mime_type}"
    with open(f"{absolute_file_path}", "r") as f:
        data = json.load(f)
    return data

def ecriture_data(dictionnaire, absolute_folder_path, file_name="Attention_weights"):
    """Write the data into the absolute_folder_path

    Args:
        dictionnaire (_type_): _description_
        absolute_folder_path (_type_): _description_
    """
    assert type(dictionnaire) == dict, f"[DEBUG]Need to save a {type({})}, current type: {type(dictionnaire)}"
    print(f"[DEBUG]Inscription attention weights in: {absolute_folder_path}")
    import pathlib
    path = pathlib.Path(absolute_folder_path)
    absolute_file_path= f"{path}{file_name}.json"
    if absolute_file_path.exists():
        print(f"[DEBUG]File already exists: Suppression et Écriture...")
        with open(f"{absolute_file_path}", "w") as f:
            json.dump(dictionnaire, f, ensure_ascii=False)

def ecriture_tsv(matrice: torch.DoubleTensor, crt: list, ctx: list, id_crt: str, id_ctx:str, absolute_folder_path:str, file_name:str):
    matrice_snts = mise_en_forme_matricielle(matrice, crt, ctx, id_crt, id_ctx)
    with open(f"{absolute_folder_path}/{file_name}.tsv", "w") as f:
        f.write("\n".join("\t".join(str(colonne) for colonne in ligne) for ligne in matrice_snts))


# Fonctions principales
def normalise_tensor(matrice: torch.Tensor, precision: int =5, DEBUG: bool=False):
    """Normalize all value of a tensor by dividing by the max of each row.

    Args:
        matrice (torch.Tensor): a torch.Tensor of 2 dimensions
        precision (float, optional): The number of decimal required to round the values. Defaults to 5.
        DEBUG (bool, optional): Allow to have information about the values. Defaults to False.

    Returns:
        torch.Tensor: the input torch.Tensor normalized
    
    >>> normalise_tensor(torch.Tensor([[1,2,3,4,5], [6,7,8,9,10], [1,5,8,4,2]]))
    tensor([[0.2000, 0.4000, 0.6000, 0.8000, 1.0000],
            [0.6000, 0.7000, 0.8000, 0.9000, 1.0000],
            [0.1250, 0.6250, 1.0000, 0.5000, 0.2500]])
    >>> normalise_tensor(torch.Tensor([[1,2,3,4,5], [6,7,8,9,10], [1,5,8,4,2]]), 1)
    tensor([[0.2000, 0.4000, 0.6000, 0.8000, 1.0000],
            [0.6000, 0.7000, 0.8000, 0.9000, 1.0000],
            [0.1000, 0.6000, 1.0000, 0.5000, 0.2000]])
    """
    max_values, _ = torch.max(matrice, dim = 1, keepdim=True) # torch.max return torch.Tensor(max_values), torch.Tensor(indices of max values)
    test=torch.DoubleTensor()
    normalized_matrice = torch.round((matrice / max_values), decimals = precision)
    if DEBUG:
        print(f"[DEBUG]max_values: {max_values}")
        print(f"[DEBUG]normalized_matrice: {normalized_matrice}")
    return normalized_matrice

def fusion_bpe(_matrice: torch.Tensor, _row_snt: list, _col_snt: list, BPE_mark: str = "@@") -> tuple:
    """Fusionne les BPEs en ligne et en colonne

    Args:
        _matrice (torch.Tensor): matrice de poids
        _row_snt (list): liste des tokens de la phrase en ligne
        _col_snt (list): liste des tokens de la phrase en colonne
        BPE_mark (str, optional): marque signifiant les BPEs. Defaults to "@@".

    Returns:
        tuple: matrice des poids 
    """
    matrice = copy.deepcopy(_matrice)
    row_snt = copy.deepcopy(_row_snt)
    col_snt = copy.deepcopy(_col_snt)

    assert torch.is_tensor(matrice), f"[DEBUG]Type matrice not a torch.Tensor: {type(matrice)}"
    assert type(row_snt) == type([]), f"[DEBUG]Type row_snt not a list: {type(row_snt)}"
    assert type(col_snt) == type([]), f"[DEBUG]Type row_snt not a list: {type(col_snt)}"

    matrice, row_snt = row_fusion_bpe(matrice, row_snt, BPE_mark)
    matrice, col_snt = row_fusion_bpe(matrice.transpose(0,1), col_snt, BPE_mark)
    return matrice.transpose(0,1), row_snt, col_snt

def suppr_pad(_matrice: torch.Tensor, _row_snt: list, _col_snt: list, padding_mark: str = "<pad>", strict: bool = False) -> tuple:
    """Supprime les poids correspondant au padding dans les phrases en ligne et en colonne

    Args:
        matrice (torch.Tensor): Matrice d'attention dont la dimension est len(row_snt) x len(col_snt)
        row_snt (list): Liste de tokens de la phrase en ligne
        col_snt (list): Liste de tokens de la phrase en colonne
        padding_mark (str, optional): Token de padding. Defaults to "<pad>".
        strict (bool, optional): Option indicant s'il faut supprimer tout le padding (set to True) ou garder au moins un token quand il apparait (set to False). Defaults to False.

    Returns:
        tuple: Matrice modifiée ainsi que les listes pour les phrases en ligne et en colonne
    >>> suppr_pad(torch.Tensor([[j for j in range(i, i+10, 1)] for i in range(0,10,1)]), row_snt = ["<pad>", "test1", "test2", "<pad>", "<pad>", "test5", "<pad>", "test7", "test8", "test9"], col_snt = ["<pad>", "test1", "test2", "<pad>", "<pad>", "test5", "<pad>", "test7", "test8", "test9"], padding_mark = '<pad>', strict = True)
    (tensor([[ 2.,  3.,  6.,  8.,  9., 10.],
            [ 3.,  4.,  7.,  9., 10., 11.],
            [ 6.,  7., 10., 12., 13., 14.],
            [ 8.,  9., 12., 14., 15., 16.],
            [ 9., 10., 13., 15., 16., 17.],
            [10., 11., 14., 16., 17., 18.]]), ['test1', 'test2', 'test5', 'test7', 'test8', 'test9'], ['test1', 'test2', 'test5', 'test7', 'test8', 'test9'])

    """
    matrice = copy.deepcopy(_matrice)
    row_snt = copy.deepcopy(_row_snt)
    col_snt = copy.deepcopy(_col_snt)

    assert matrice.size(dim=0) == len(row_snt), f"[DEBUG]Matrice size error\nMatrice size: {matrice.size(dim=0)} \nrow_snt len: {len(row_snt)}"
    assert matrice.size(dim=1) == len(col_snt), f"[DEBUG]Matrice size error\nMatrice size: {matrice.size(dim=1)} \ncol_snt len: {len(col_snt)}"
    
    matrice, row_snt = row_suppr_pad(matrice, row_snt, padding_mark, strict)
    matrice, col_snt = row_suppr_pad(matrice.transpose(0,1), col_snt, padding_mark, strict)

    return matrice.transpose(0,1), row_snt, col_snt

def mise_en_forme_matricielle(_matrice: torch.Tensor, _crt: list, _ctx: list, id_crt: str = "0", id_ctx: str = "0") -> list:
    """Convertie une matrice ainsi que les phrases courante (de longueur n) et de contexte (de longueur m) en une matrice n x m au format:
    [[id_crt-id-ctx, ctx[0], ctx[1], ..., ctx[m]       ],
     [    crt[0]   , w_0_0 , w_1_0,  ...               ],
     ...................................................,
     ...................................................,
     [crt[len(crt)], w_n_1 , w_n_2, ... , w_n_m        ]]

    Args:
        _matrice (torch.Tensor): matrice des poids d'attention
        crt (list): list de token de la phrase courante
        ctx (list): list de token de la phrase de contexte
        id_crt (str): id de la phrase courante
        id_ctx (str): id de la phrase de contexte

    Returns:
        list: liste de la phrase courante, de contexte et les poids d'attention
    """
    
    matrice = copy.deepcopy(_matrice).tolist()
    crt = copy.deepcopy(_crt)
    ctx = copy.deepcopy(_ctx)
    
    assert _matrice.size(dim= 0) == len(crt), f"[DEBUG]Matrice size error, matrice.size(): {_matrice.size(dim= 0)} vs len(current sentence): {len(crt)}"
    assert _matrice.size(dim= 1) == len(ctx), f"[DEBUG]Matrice size error, matrice.size(): {_matrice.size(dim= 1)} vs len(current sentence): {len(ctx)}"

    matrice.insert(0, ctx)
    matrice[0].insert(0, f"{id_crt}-{id_ctx}")
    for i in range(1, len(matrice)):
        matrice[i].insert(0, crt[i - 1])
    return matrice

def suppression_inf_uniforme_tensor_src(matrice, DEBUG = False):
    """Applique un mask sur les poids de la matrice source inférieur à une valeur (ici threshold)

    Args:
        matrice (torch.Tensor): tensor représentant une matrice de poids
        DEBUG (bool, optional): Affiche différentes informations si True. Defaults to False.

    Returns:
        torch.Tensor: tensor représentant la matrice de poids avec un masque appliqué sur les valeurs inférieure à la moyenne uniforme
    """
    threshold = 1/matrice.size()[1]
    if DEBUG:
        print(f"[DEBUG]threshold: {threshold}")
    inverse_mask = matrice > threshold
    if DEBUG:
        print(f"[DEBUG]mask: {inverse_mask}")
    res_matrice = matrice * inverse_mask
    if DEBUG:
        print(f"[DEBUG]res_matrice: {res_matrice}")
    return res_matrice

def suppression_inf_uniforme_tensor_tgt(matrice, method_threshold="torch.nonzero",DEBUG=False):
    """Applique un mask sur les poids de la matrice target inférieur à une valeur (ici threshold)

    Args:
        matrice (torch.Tensor): tensor représentant une matrice de poids d'analyse_attention.ipynb
        DEBUG (bool, optional): Affiche différentes informations si True. Defaults to False.
    """
    for i in range(matrice.size()[0]):
        threshold = None
        if method_threshold == "torch.nonzero":
            threshold = 1/len(torch.nonzero(matrice[i]))
        elif method_threshold == "count":
            threshold = 1/(i + 1)
        assert type(threshold) == int or type(threshold) == float, f"[DEBUG]threshold must be 'torch.nonzero' or 'count'. Current type : {type(threshold)}"
        if DEBUG:
            print(f"[DEBUG]threshold: {threshold}")
        # Produit un mask ne gardant que les valeurs supérieures ou égales à la limite (moyenne uniforme sur le nombre de poids utilisés)
        mask = matrice[i] >= threshold
        if DEBUG:
            print(f"[DEBUG]mask: {mask}")
        matrice[i] = matrice[i]*mask
    return matrice
    
def convertion_matrice_str_to_float(matrice: list) -> torch.DoubleTensor:
    return torch.DoubleTensor([ [float(weight) for weight in line] for line in matrice ])


# Sous Fonctions
def row_fusion_bpe(matrice: torch.Tensor, row_snt: list, BPE_mark:str = '@@') -> tuple:
    """Fonction qui fusionne les BPEs des lignes d'une matrice. Garde le max des lignes fusionnées

    Args:
        matrice (torch.Tensor): matrice flottant
        row_snt (list): liste des tokens de la phrase
        BPE_mark (str, optional): Marque des BPEs utilisés (ATTENTION: sera supprimé). Defaults to '@@'.

    Returns:
        tuple: matrice et list de tokens sans les BPEs.
    """
    ## TODO : Function qui fusionne les BPEs des phrases d'une matrice
    # Checking Size: matrice = row_snt x col_snt
    assert matrice.size(dim=0) == len(row_snt), f"[DEBUG]Matrice and row sentence size not the same: {matrice.size(dim=0)} vs {len(row_snt)}"
    # Merging BPEs on the line
    i = len(row_snt) - 2
    while i > 0:
        if str(row_snt[i]).endswith(BPE_mark):
            # Si on trouve la marque d'un BPE alors
            # On prends le max de la ligne 
            matrice[i] = torch.max(matrice[i], matrice[i+1])
            matrice = torch.cat((matrice[:i+1], matrice[i+2:]), dim = 0)
            row_snt[i] = f"{row_snt[i].split(BPE_mark)[0]}{row_snt[i+1]}"
            del row_snt[i+1]
        i -= 1
    return matrice, row_snt

def row_suppr_pad(matrice: torch.Tensor, snt: list, padding_mark: str = "<pad>", strict: bool = False) -> tuple:
    """Supprime les poids de la matrice correspondant au padding dans les phrases en ligne

    Args:
        matrice (torch.Tensor): Une matrice d'attention de dont la dimension sur les lignes est la longueur de la phrase
        snt (list): Liste de tokens de la phrase en ligne
        padding_mark (str, optional): Token de padding. Defaults to "<pad>".
        strict (bool, optional): Option indicant s'il faut supprimer tout le padding (set to True) ou garder au moins un token quand il apparait (set to False). Defaults to False.

    Returns:
        tuple: Matrice modifiée ainsi que la phrase données en paramètre

    >>> row_suppr_pad(torch.Tensor([[j for j in range(i, i+10, 1)] for i in range(0,10,1)]), ["<pad>", "test1", "test2", "<pad>", "<pad>", "test5", "<pad>", "test7", "test8", "test9"], padding_mark = '<pad>', strict = True)
    (tensor([[ 1.,  2.,  3.,  4.,  5.,  6.,  7.,  8.,  9., 10.],
            [ 2.,  3.,  4.,  5.,  6.,  7.,  8.,  9., 10., 11.],
            [ 5.,  6.,  7.,  8.,  9., 10., 11., 12., 13., 14.],
            [ 7.,  8.,  9., 10., 11., 12., 13., 14., 15., 16.],
            [ 8.,  9., 10., 11., 12., 13., 14., 15., 16., 17.],
            [ 9., 10., 11., 12., 13., 14., 15., 16., 17., 18.]]), ['test1', 'test2', 'test5', 'test7', 'test8', 'test9'])
    """
    assert matrice.size(dim=0) == len(snt), f"[DEBUG]Matrice size error\nMatrice size: {matrice.size(dim=0)} \nsnt len: {len(snt)}"

    if strict:
        stop = 0
    else:
        stop = 1

    i = len(snt) - 1
    while i >= stop:
        if snt[i] == padding_mark:
            del snt[i]
            matrice = torch.concat([matrice[0:i], matrice[i+1:, :]])
        i-=1
    assert matrice.size(dim=0) == len(snt), f"[DEBUG]Matrice size error\nMatrice size: {matrice.size(dim=0)} \nsnt len: {len(snt)}"
    
    return matrice, snt



# Fonction d'affichage
def affiche_matrix(_matrice, type):
    """Affiche la matrice d'une façon plus lisible

    Args:
        _matrice (torch.Tensor or list): matrice a afficher
        type (_type_): type de la matrice a afficher
    """
    if type == torch.Tensor:
        matrice = _matrice.tolist()
    elif type == list:
        matrice = _matrice
    for i in range(0, len(matrice)):
        print(matrice[i])

if __name__ == "__main__":
    import doctest
    doctest.testmod()
